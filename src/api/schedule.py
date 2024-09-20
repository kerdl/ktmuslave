from __future__ import annotations
from loguru import logger
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass
from pydantic import BaseModel
from websockets import client, exceptions
from websockets.legacy import client
from aiohttp.client_exceptions import (
    ClientConnectorError,
    ServerDisconnectedError
)
from aiohttp import ClientResponse
from pathlib import Path
import asyncio
import datetime
import aiofiles

from src import defs
from src.api.base import Api
from src.data import RepredBaseModel, Duration
from src.data.schedule import Page, compare


class Notify(BaseModel):
    random: str
    groups: Optional[compare.PageCompare]
    teachers: Optional[compare.PageCompare]
    
    def has_updates_for_group(self, name: str) -> bool:
        if self.groups is None:
            return False
        
        for change in [
            self.groups.formations.appeared,
            self.groups.formations.changed
        ]:
            for formation in change:
                formation: RepredBaseModel
                if formation.repr_name == name:
                    return True

        for page_compare in [self.daily, self.weekly]:
            if page_compare is None:
                continue

            for change in [
                page_compare.groups.appeared,
                page_compare.groups.changed
            ]:
                for formation in change:
                    formation: RepredBaseModel

                    if formation.repr_name == name:
                        return True
        
        return False
    
    def has_updates_for_teacher(self, name: str):
        for page_compare in [self.tchr_daily, self.tchr_weekly]:
            if page_compare is None:
                continue

            for change in [
                page_compare.teachers.appeared,
                page_compare.teachers.changed
            ]:
                for teacher in change:
                    teacher: RepredBaseModel

                    if teacher.repr_name == name:
                        return True
        
        return False

    @property
    def is_auto_invoked(self) -> bool:
        return self.invoker == "auto"
    
    @property
    def is_manually_invoked(self) -> bool:
        return isinstance(self.invoker, Invoker)

class LastNotify(BaseModel):
    path: Optional[Path]
    random: Optional[str]

    async def save(self):
        async with aiofiles.open(self.path, mode="w") as f:
            ser = self.json(ensure_ascii=False, indent=2, exclude={"path"})
            await f.write(ser)
    
    def poll_save(self):
        defs.create_task(self.save())
    
    @classmethod
    def load(cls, path: Path):
        self = cls.parse_file(path)
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
class ScheduleApi(Api):
    is_online: bool = False

    _last_groups: Optional[Page] = None
    _last_teachers: Optional[Page] = None

    _last_update: Optional[datetime.datetime] = None
    _update_period: Optional[Duration] = None

    async def _req(self, url: str, method: Callable[[str], Awaitable[ClientResponse]], return_result: bool = True):
        from src.api import Response

        resp = await method(url)
        resp_text = await resp.text()

        if return_result:
            response = Response.parse_raw(resp_text)

            return response

    async def _get(self, url: str, return_result: bool = True):
        return await self._req(url, defs.http.get, return_result=return_result)

    async def _post(self, url: str):
        return await self._req(url, defs.http.post)

    async def groups(self) -> list[str]:
        groups_list: list[str] = []

        daily = await self.daily_groups()
        weekly = await self.weekly_groups()

        # fuck off about ""sets"", i want shit sorted
        for weekly_group in weekly:
            groups_list.append(weekly_group)
        
        for daily_group in daily:
            if daily_group not in groups_list:
                groups_list.append(daily_group)

        return groups_list
    
    async def teachers(self) -> list[str]:
        teacher_list: list[str] = []

        daily = await self.daily_teachers()
        weekly = await self.weekly_teachers()

        # fuck off about ""sets"", i want shit sorted
        for weekly_teacher in weekly:
            teacher_list.append(weekly_teacher)
        
        for daily_teacher in daily:
            if daily_teacher not in teacher_list:
                teacher_list.append(daily_teacher)

        return teacher_list

    async def wait_for_schedule_server(self):
        retry_period = 5
        is_connect_error_logged = False
        url = "http://" + self.url

        while True:
            try:
                await self._get(url, return_result = False)
            except ClientConnectorError:
                if not is_connect_error_logged:
                    logger.error(
                        f"run schedule HTTP API server on {url} first, "
                        f"will keep trying reconnecting each {retry_period} secs"
                    )
                    is_connect_error_logged = True
                await asyncio.sleep(retry_period)
                continue

            break
    
    async def ping(self) -> bool:
        url = "http://" + self.url

        try:
            await self._get(url, return_result = False)
            return True
        except ClientConnectorError:
            return False

    async def schedule(self, url: str) -> Optional[Page]:
        response = await self._get(url)
        if response.data is None:
            return None

        return response.data.page

    async def groups(self, name: Optional[str] = None) -> Page:
        url = "http://" + self.url + "/groups"

        if name is not None:
            url += f"?name={name}"

        return await self.schedule(url)

    async def get_url(self, url: str) -> str:
        return (await self._get(url)).data.url

    async def last_update(self) -> datetime.datetime:
        url = "http://" + self.url + "/update/last"

        return (await self._get(url)).data.updates.last

    async def update_period(self, force: bool = True) -> Duration:
        url = "http://" + self.url + "/update/period"

        if self._update_period is None or force:
            self._update_period = (await self._get(url)).data.updates.period
        
        return self._update_period

    async def updates(self):
        retry_period = 5
        is_connect_error_logged = False
    
        while True:
            try:
                url = "ws://" + self.url + f"/updates"

                def protocol_factory(*args, **kwargs) -> client.WebSocketClientProtocol:
                    protocol = client.WebSocketClientProtocol()
                    protocol.max_size = 2**48
                    protocol.read_limit = 2**48

                    return protocol

                logger.info(f"connecting to {url}")

                async with client.connect(url, create_protocol=protocol_factory) as socket:
                    try:
                        await SCHEDULE_API.update_period(force=True)

                        self.is_online = True
                        is_connect_error_logged = False

                        logger.info(f"awaiting updates...")
                        async for message in socket:
                            notify = Notify.parse_raw(message)

                            if notify.random == LAST_NOTIFY.random:
                                logger.info(
                                    f"caught duplicate notify {notify.random}, ignoring"
                                )
                                continue
                            
                            LAST_NOTIFY.set_random(notify.random)

                            await self.groups()
                            await self.teachers()

                            await defs.check_redisearch_index()
                            await defs.ctx.broadcast(notify)
                    except exceptions.ConnectionClosedError as e:
                        logger.info(e)
                        logger.info("reconnecting...")
                        continue

            except (ClientConnectorError, ServerDisconnectedError):
                if not is_connect_error_logged:
                    self.is_online = False

                    logger.error(
                        f"can't connect to updates server, "
                        f"will keep retrying each {retry_period} secs"
                    )

                    is_connect_error_logged = True
        
                await asyncio.sleep(5)
                continue

KTMUSCRAP_ADDR = get_key(ENV_PATH, 'KTMUSCRAP_ADDR')

SCHEDULE_API = ScheduleApi(f"{KTMUSCRAP_ADDR}/schedule" if KTMUSCRAP_ADDR else "127.0.0.1:8080/schedule")
LAST_NOTIFY = LastNotify.load_or_init(defs.data_dir.joinpath("last_notify.json"))
