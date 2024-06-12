from __future__ import annotations
from loguru import logger
from typing import Optional, Literal, Union, Callable, Awaitable
from dataclasses import dataclass
from pydantic import BaseModel
from websockets import client, exceptions
from websockets.legacy import client
from aiohttp.client_exceptions import ClientConnectorError, ServerDisconnectedError
from aiohttp import ClientResponse
from pathlib import Path
from dotenv import get_key
import asyncio
import datetime
import aiofiles
import time

from src import defs, ENV_PATH
from src.api.base import Api
from src.data import RepredBaseModel, Duration
from src.data.schedule import Page, TchrPage, compare
from src.svc.common import keyboard as kb


AUTO_LITERAL = Literal["auto"]


class Interactor(BaseModel):
    key: str

class Invoker(BaseModel):
    manually: Interactor

class Notify(BaseModel):
    random: str
    invoker: Union[AUTO_LITERAL, Invoker]
    daily: Optional[compare.PageCompare]
    weekly: Optional[compare.PageCompare]
    tchr_daily: Optional[compare.TchrPageCompare]
    tchr_weekly: Optional[compare.TchrPageCompare]
    
    def has_updates_for_group(self, name: str):
        for page_compare in [self.daily, self.weekly]:
            if page_compare is None:
                continue

            for change in [
                page_compare.groups.appeared,
                page_compare.groups.changed
            ]:
                for group in change:
                    group: RepredBaseModel

                    if group.repr_name == name:
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
        async with aiofiles.open(defs.data_dir.joinpath("last_notify.json"), mode="w") as f:
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
    interactor: Optional[Interactor] = None
    is_online: bool = False

    _last_daily: Optional[Page] = None
    _last_weekly: Optional[Page] = None

    _ft_daily_friendly_url: Optional[str] = None
    _ft_weekly_friendly_url: Optional[str] = None
    _r_weekly_friendly_url: Optional[str] = None
    _tchr_ft_daily_friendly_url: Optional[str] = None
    _tchr_ft_weekly_friendly_url: Optional[str] = None
    _tchr_r_weekly_friendly_url: Optional[str] = None

    _ft_daily_url_button: Optional[kb.Button] = None
    _ft_weekly_url_button: Optional[kb.Button] = None
    _r_weekly_url_button: Optional[kb.Button] = None
    _tchr_ft_daily_url_button: Optional[kb.Button] = None
    _tchr_ft_weekly_url_button: Optional[kb.Button] = None
    _tchr_r_weekly_url_button: Optional[kb.Button] = None

    _update_period: Optional[Duration] = None
    _last_update: Optional[datetime.datetime] = None

    async def _req(self, url: str, method: Callable[[str], Awaitable[ClientResponse]], return_result: bool = True):
        from src.api import Response

        start = time.time()
        resp = await method(url)
        resp_text = await resp.text()
        end = time.time()

        logger.debug(f"req for url {url} took {end - start}")

        if return_result:
            response = Response.parse_raw(resp_text)

            return response

    async def _get(self, url: str, return_result: bool = True):
        return await self._req(url, defs.http.get, return_result=return_result)

    async def _post(self, url: str):
        return await self._req(url, defs.http.post)

    async def daily_groups(self) -> list[str]:
        groups: list[str] = []

        daily = await self.daily()

        if daily is None:
            return groups

        for group in daily.groups:
            groups.append(group.name)
        
        return groups

    async def weekly_groups(self) -> list[str]:
        groups: list[str] = []

        weekly = await self.weekly()

        if weekly is None:
            return groups

        for group in weekly.groups:
            groups.append(group.name)
        
        return groups

    async def daily_teachers(self) -> list[str]:
        teachers: list[str] = []

        daily = await self.tchr_daily()

        if daily is None:
            return teachers

        for teacher in daily.teachers:
            teachers.append(teacher.name)
        
        return teachers

    async def weekly_teachers(self) -> list[str]:
        teachers: list[str] = []

        weekly = await self.tchr_weekly()

        if weekly is None:
            return teachers

        for teacher in weekly.teachers:
            teachers.append(teacher.name)
        
        return teachers

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

    async def tchr_schedule(self, url: str) -> Optional[TchrPage]:
        response = await self._get(url)
        if response.data is None:
            return None

        return response.data.tchr_page

    async def daily(self, group: Optional[str] = None) -> Page:
        url = "http://" + self.url + "/daily"

        if group is not None:
            url += f"?group={group}"

        return await self.schedule(url)
    
    async def weekly(self, group: Optional[str] = None) -> Page:
        url = "http://" + self.url + "/weekly"

        if group is not None:
            url += f"?group={group}"

        return await self.schedule(url)
    
    async def tchr_daily(self, teacher: Optional[str] = None) -> TchrPage:
        url = "http://" + self.url + "/tchr_daily"

        if teacher is not None:
            url += f"?teacher={teacher}"

        return await self.tchr_schedule(url)
    
    async def tchr_weekly(self, teacher: Optional[str] = None) -> TchrPage:
        url = "http://" + self.url + "/tchr_weekly"

        if teacher is not None:
            url += f"?teacher={teacher}"

        return await self.tchr_schedule(url)

    async def get_url(self, url: str) -> str:
        return (await self._get(url)).data.url

    async def last_update(self) -> datetime.datetime:
        url = "http://" + self.url + "/update/last"

        return (await self._get(url)).data.last_update

    async def update_period(self, force: bool = True) -> Duration:
        url = "http://" + self.url + "/update/period"

        if self._update_period is None or force:
            self._update_period = (await self._get(url)).data.period
        
        return self._update_period

    async def ft_daily_friendly_url(self, force: bool = False) -> str:
        url = "http://" + self.url + "/raw/ft_daily/friendly_url"

        if self._ft_daily_friendly_url is None or force:
            self._ft_daily_friendly_url = await self.get_url(url)

        return self._ft_daily_friendly_url

    async def ft_weekly_friendly_url(self, force: bool = False) -> str:
        url = "http://" + self.url + "/raw/ft_weekly/friendly_url"

        if self._ft_weekly_friendly_url is None or force:
            self._ft_weekly_friendly_url = await self.get_url(url)

        return self._ft_weekly_friendly_url

    async def r_weekly_friendly_url(self, force: bool = False) -> str:
        url = "http://" + self.url + "/raw/r_weekly/friendly_url"

        if self._r_weekly_friendly_url is None or force:
            self._r_weekly_friendly_url = await self.get_url(url)

        return self._r_weekly_friendly_url

    async def tchr_ft_daily_friendly_url(self, force: bool = False) -> str:
        url = "http://" + self.url + "/raw/tchr_ft_daily/friendly_url"

        if self._tchr_ft_daily_friendly_url is None or force:
            self._tchr_ft_daily_friendly_url = await self.get_url(url)

        return self._tchr_ft_daily_friendly_url

    async def tchr_ft_weekly_friendly_url(self, force: bool = False) -> str:
        url = "http://" + self.url + "/raw/tchr_ft_weekly/friendly_url"

        if self._tchr_ft_weekly_friendly_url is None or force:
            self._tchr_ft_weekly_friendly_url = await self.get_url(url)

        return self._tchr_ft_weekly_friendly_url

    async def tchr_r_weekly_friendly_url(self, force: bool = False) -> str:
        url = "http://" + self.url + "/raw/tchr_r_weekly/friendly_url"

        if self._tchr_r_weekly_friendly_url is None or force:
            self._tchr_r_weekly_friendly_url = await self.get_url(url)

        return self._tchr_r_weekly_friendly_url

    def ft_daily_url_button(self, force: bool = True) -> kb.Button:
        if self._ft_daily_url_button is None or force:
            self._ft_daily_url_button = kb.Button(
                text = kb.Text.FT_DAILY,
                url  = self._ft_daily_friendly_url
            )
        
        return self._ft_daily_url_button

    def ft_weekly_url_button(self, force: bool = True) -> kb.Button:
        if self._ft_weekly_url_button is None or force:
            self._ft_weekly_url_button = kb.Button(
                text = kb.Text.FT_WEEKLY,
                url  = self._ft_weekly_friendly_url
            )
        
        return self._ft_weekly_url_button

    def r_weekly_url_button(self, force: bool = True) -> kb.Button:
        if self._r_weekly_url_button is None or force:
            self._r_weekly_url_button = kb.Button(
                text = kb.Text.R_WEEKLY,
                url  = self._r_weekly_friendly_url
            )
        
        return self._r_weekly_url_button

    def tchr_ft_daily_url_button(self, force: bool = True) -> kb.Button:
        if self._tchr_ft_daily_url_button is None or force:
            self._tchr_ft_daily_url_button = kb.Button(
                text = kb.Text.FT_DAILY,
                url  = self._tchr_ft_daily_friendly_url
            )
        
        return self._tchr_ft_daily_url_button

    def tchr_ft_weekly_url_button(self, force: bool = True) -> kb.Button:
        if self._tchr_ft_weekly_url_button is None or force:
            self._tchr_ft_weekly_url_button = kb.Button(
                text = kb.Text.FT_WEEKLY,
                url  = self._tchr_ft_weekly_friendly_url
            )
        
        return self._tchr_ft_weekly_url_button

    def tchr_r_weekly_url_button(self, force: bool = True) -> kb.Button:
        if self._tchr_r_weekly_url_button is None or force:
            self._tchr_r_weekly_url_button = kb.Button(
                text = kb.Text.R_WEEKLY,
                url  = self._tchr_r_weekly_friendly_url
            )
        
        return self._tchr_r_weekly_url_button
    
    async def interact(self) -> Interactor:
        from src.api import Response

        url = "http://" + self.url + "/interact"

        logger.info("getting schedule updates key")

        self.interactor = (await self._get(url)).data.interactor

        logger.info(f"we got key {self.interactor.key}")

        return self.interactor

    async def interactor_valid(self) -> bool:
        url = "http://" + self.url + f"/interact/is-valid?key={self.interactor.key}"

        return (await self._get(url)).is_ok

    async def updates(self):
        retry_period = 5
        is_connect_error_logged = False
    
        while True:
            try:
                if self.interactor is None or not await self.interactor_valid():
                    await self.interact()
                
                url = "ws://" + self.url + f"/updates?key={self.interactor.key}"

                def protocol_factory(*args, **kwargs) -> client.WebSocketClientProtocol:
                    protocol = client.WebSocketClientProtocol()
                    protocol.max_size = 2**48
                    protocol.read_limit = 2**48

                    return protocol

                logger.info(f"connecting to {url}")

                async with client.connect(url, create_protocol=protocol_factory) as socket:
                    try:
                        await SCHEDULE_API.update_period(force=True)
                        await SCHEDULE_API.ft_daily_friendly_url(force=True)
                        await SCHEDULE_API.ft_weekly_friendly_url(force=True)
                        await SCHEDULE_API.r_weekly_friendly_url(force=True)
                        await SCHEDULE_API.tchr_ft_daily_friendly_url(force=True)
                        await SCHEDULE_API.tchr_ft_weekly_friendly_url(force=True)
                        await SCHEDULE_API.tchr_r_weekly_friendly_url(force=True)

                        SCHEDULE_API.ft_daily_url_button(force=True)
                        SCHEDULE_API.ft_weekly_url_button(force=True)
                        SCHEDULE_API.r_weekly_url_button(force=True)
                        SCHEDULE_API.tchr_ft_daily_url_button(force=True)
                        SCHEDULE_API.tchr_ft_weekly_url_button(force=True)
                        SCHEDULE_API.tchr_r_weekly_url_button(force=True)

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

                            await self.daily()
                            await self.weekly()

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

    async def update(self):
        if self.interactor is None or not await self.interactor_valid():
            await self.interact()

        url = "http://" + self.url + f"/update?key={self.interactor.key}"

        response = await self._post(url)

        return response

KTMUSCRAP_ADDR = get_key(ENV_PATH, 'KTMUSCRAP_ADDR')

SCHEDULE_API = ScheduleApi(f"{KTMUSCRAP_ADDR}/schedule" if KTMUSCRAP_ADDR else "127.0.0.1:8080/schedule")
LAST_NOTIFY  = LastNotify.load_or_init(defs.data_dir.joinpath("last_notify.json"))