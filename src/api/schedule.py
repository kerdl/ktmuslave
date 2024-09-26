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
    path: Optional[Path] = None
    random: Optional[str] = None

    async def save(self):
        path: Path = self.path
        async with aiofiles.open(path, mode="w") as f:
            ser = self.model_dump_json(
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

    async def schedule_from_url(self, url: str) -> Optional[Page]:
        response = await get(url)
        if response.data is None:
            return None

        return response.data.page

    async def request_groups(self) -> Page:
        url = "http://" + self.url + "/schedule/groups"
        self._cached_groups = await self.schedule_from_url(url)
        return self._cached_groups
        
    async def request_teachers(self) -> Page:
        url = "http://" + self.url + "/schedule/teachers"
        self._cached_teachers = await self.schedule_from_url(url)
        return self._cached_teachers

    async def request_last_update(self) -> datetime.datetime:
        url = "http://" + self.url + "/schedule/updates/last"
        self._cached_last_update = (await get(url)).data.updates.last
        return self._cached_last_update

    async def request_update_period(self) -> Page:
        url = "http://" + self.url + "/schedule/updates/period"
        self._cached_update_period = (await get(url)).data.updates.period
        return self._cached_update_period
    
    async def request_all(self):
        await self.request_groups()
        self._cached_groups._chunk_formations_by_week()
        await self.request_teachers()
        self._cached_teachers._chunk_formations_by_week()
        await self.request_last_update()
        await self.request_update_period()
    
    def get_groups(self) -> Optional[Page]:
        return self._cached_groups

    def get_teachers(self) -> Optional[Page]:
        return self._cached_teachers

    def get_last_update(self) -> Optional[datetime.datetime]:
        return self._cached_last_update

    def get_update_period(self) -> Optional[Duration]:
        return self._cached_update_period

    def group_names(self) -> list[str]:
        page = self.get_groups()
        if page is None: return []
        return page.names()
    
    def teacher_names(self) -> list[str]:
        page = self.get_teachers()
        if page is None: return []
        return page.names()

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
                        await self.request_all()

                        self.is_online = True
                        is_connect_error_logged = False
                        is_connection_attempt_logged = False

                        logger.info(f"awaiting schedule updates...")
                        async for message in socket:
                            notify = Notify.model_validate_json(message)

                            if notify.random == self.last_notify.random:
                                logger.info(
                                    f"caught duplicate notify {notify.random}, ignoring"
                                )
                                continue
                            
                            self.last_notify.set_random(notify.random)

                            await self.request_all()

                            await defs.check_redisearch_index()
                            await defs.ctx.broadcast(notify)
                    except exceptions.ConnectionClosedError as e:
                        logger.info(e)
                        logger.info("reconnecting to ktmuscrap...")
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
