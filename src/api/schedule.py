from __future__ import annotations
import asyncio
import datetime
import aiofiles
from loguru import logger
from typing import Optional
from dataclasses import dataclass
from pydantic import BaseModel
from websockets import client, exceptions
from websockets.legacy import client
from aiohttp.client_exceptions import (
    ClientConnectorError,
    ServerDisconnectedError
)
from pathlib import Path
from src.api import request, get, post, Notify
from src.data.schedule import Page
from src.data.duration import Duration


class LastNotify(BaseModel):
    path: Optional[Path]
    random: Optional[str]

    async def save(self):
        path: Path = self.path
        async with aiofiles.open(path, mode="w") as f:
            ser = self.json(
                ensure_ascii=False,
                indent=2,
                exclude={"path"}
            )
            await f.write(ser)
    
    def poll_save(self):
        from src import defs
        defs.create_task(self.save())
    
    @classmethod
    def load(cls, path: Path):
        with open(path, mode="r", encoding="utf8") as f:
            self = cls.model_validate_json(f.read())
            self.path = path

            return self

    @classmethod
    def load_or_init(cls: type[LastNotify], path: Path) -> LastNotify:
        if path.exists():
            return cls.load(path)
        else:
            self = cls(path=path, random=None)
            self.poll_save()

            return self
    
    def set_random(self, random: str):
        self.random = random
        self.poll_save()

@dataclass
class ScheduleApi:
    url: str
    is_online: bool = False
    last_notify: Optional[LastNotify] = None

    _cached_groups: Optional[Page] = None
    _cached_teachers: Optional[Page] = None

    _cached_last_update: Optional[datetime.datetime] = None
    _cached_update_period: Optional[Duration] = None

    async def group_names(self, force: bool = False) -> list[str]:
        return (await self.get_groups(force=force)).names()
    
    async def teacher_names(self, force: bool = False) -> list[str]:
        return (await self.get_teachers(force=force)).names()

    async def await_server(self):
        retry_period = 5
        is_connect_error_logged = False
        url = "http://" + self.url

        while True:
            try:
                await get(url=url, return_result=False)
            except ClientConnectorError:
                if not is_connect_error_logged:
                    logger.error(
                        "unable to reach ktmuscrap instance "
                        f"at {url}, awaiting..."
                    )
                    is_connect_error_logged = True
                await asyncio.sleep(retry_period)
                continue

            break

    async def schedule_from_url(self, url: str) -> Optional[Page]:
        response = await get(url)
        if response.data is None:
            return None

        return response.data.page

    async def get_groups(
        self,
        name: Optional[str] = None,
        force: bool = False
    ) -> Page:
        if not force and self._cached_groups:
            return self._cached_groups

        url = "http://" + self.url + "/schedule/groups"
        if name is not None: url += f"?name={name}"

        self._cached_groups = await self.schedule_from_url(url)
        return self._cached_groups

    async def get_teachers(
        self,
        name: Optional[str] = None,
        force: bool = False
    ) -> Page:
        if not force and self._cached_teachers:
            return self._cached_teachers
        
        url = "http://" + self.url + "/schedule/teachers"
        if name is not None: url += f"?name={name}"

        self._cached_teachers = await self.schedule_from_url(url)
        return self._cached_teachers

    async def get_last_update(
        self,
        force: bool = False
    ) -> datetime.datetime:
        if not force:
            return self._cached_last_update
        
        url = "http://" + self.url + "/schedule/updates/last"

        return (await get(url)).data.updates.last

    async def get_update_period(self, force: bool = True) -> Duration:
        url = "http://" + self.url + "/schedule/updates/period"
        if self._cached_update_period is None or force:
            self._cached_update_period = (await get(url)).data.updates.period
        return self._cached_update_period

    async def updates(self):
        from src import defs

        retry_period = 5
        is_connection_attempt_logged = False
        is_connect_error_logged = False
        url = "ws://" + self.url + f"/schedule/updates"
    
        while True:
            try:
                def protocol_factory(*args, **kwargs) -> client.WebSocketClientProtocol:
                    protocol = client.WebSocketClientProtocol()
                    protocol.max_size = 2**48
                    protocol.read_limit = 2**48

                    return protocol

                if not is_connection_attempt_logged:
                    logger.info(f"connecting to {url}")
                    is_connection_attempt_logged = True

                async with client.connect(
                    url,
                    create_protocol=protocol_factory
                ) as socket:
                    try:
                        await self.get_update_period(force=True)

                        self.is_online = True
                        is_connect_error_logged = False
                        is_connection_attempt_logged = False

                        logger.info(f"awaiting updates...")
                        async for message in socket:
                            notify = Notify.model_validate_json(message)

                            if notify.random == self.last_notify.random:
                                logger.info(
                                    f"caught duplicate notify {notify.random}, ignoring"
                                )
                                continue
                            
                            self.last_notify.set_random(notify.random)

                            await self.get_groups()
                            await self.get_teachers()

                            await defs.check_redisearch_index()
                            await defs.ctx.broadcast(notify)
                    except exceptions.ConnectionClosedError as e:
                        logger.info(e)
                        logger.info("reconnecting...")
                        continue

            except (
                ConnectionRefusedError,
                ClientConnectorError,
                ServerDisconnectedError
            ):
                if not is_connect_error_logged:
                    self.is_online = False

                    logger.error(
                        "unable to reach ktmuscrap instance "
                        f"at {url}, awaiting..."
                    )

                    is_connect_error_logged = True
        
                await asyncio.sleep(retry_period)
                continue
