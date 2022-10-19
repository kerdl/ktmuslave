from __future__ import annotations
import datetime
import aiofiles
import asyncio
from typing import Literal, Optional
from loguru import logger
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from time import time
from aiohttp import ClientResponse

from src import defs
from src.data import error


class Type:
    WEEKLY = "weekly"
    DAILY  = "daily"

TYPE_LITERAL = Literal["weekly", "daily"]

class RawType:
    FT_WEEKLY = "ft_weekly"
    FT_DAILY  = "ft_daily"
    R_WEEKLY  = "r_weekly"

RAW_TYPE_LITERAL = Literal["ft_weekly", "ft_daily", "r_weekly"]


@dataclass
class Message:
    type: TYPE_LITERAL
    is_folded: bool

    @classmethod
    def default(cls: type[Message]) -> Message:
        return cls(
            type      = Type.WEEKLY,
            is_folded = False
        )
    
    def switch_to_weekly(self):
        self.type = Type.WEEKLY
    
    def switch_to_daily(self):
        self.type = Type.DAILY

    @property
    def is_weekly(self):
        return self.type == Type.WEEKLY
    
    @property
    def is_daily(self):
        return self.type == Type.DAILY


@dataclass
class Schedule:
    message: Message
    last_update: Optional[float]

    @classmethod
    def default(cls: type[Schedule]) -> Schedule:
        return cls(
            message     = Message.default(),
            last_update = 0
        )
    
    @property
    def can_update(self):
        return self.next_allowed_time < time()
    
    @property
    def next_allowed_time(self):
        return self.last_update + 60
    
    @property
    def until_allowed(self):
        return self.next_allowed_time - time()

    def update(self) -> bool:
        self.last_update = time()

        has_updates = False
        return has_updates

@dataclass
class File:
    path: Path
    contents: Optional[bytes]

    async def read(self) -> bytes:
        async with aiofiles.open(self.path, "rb") as f:
            self.contents = await f.read()
        
        return self.contents

    async def write(self, contents: bytes):
        async with aiofiles.open(self.path, "wb") as f:
            await f.write(contents)
        
        self.contents = contents

@dataclass
class RawSchedule(File):
    type: RAW_TYPE_LITERAL
    url: str
    friendly_url: Optional[str]
    sha256: Optional[str]

    async def calc_sha256(self) -> str:
        hex_hash = sha256(self.contents).hexdigest()

        self.sha256 = hex_hash

        return hex_hash
    
    async def request(self) -> ClientResponse:
        response = await defs.http.get(self.url)
        return response
    
    def __hash__(self) -> int:
        return hash(self.type)


@dataclass
class Index(File):
    updated: Optional[datetime.datetime]
    types: Optional[set[RawSchedule]]

    async def infinite_update(self):
        while True:
            now = datetime.datetime.now()

            if self.updated is None:
                self.updated = now - datetime.timedelta(minutes = 10)

            next_update = self.updated + datetime.timedelta(minutes = 10)
            sleep_until_update = (
                next_update - now
            ).total_seconds()

            if sleep_until_update < 0:
                sleep_until_update = 0

            await asyncio.sleep(sleep_until_update)
            await self.update()

    async def update(self):
        if self.types is None:
            self.types = [FT_WEEKLY, FT_DAILY, R_WEEKLY]

        try:
            await self.download_all()
        except error.InvalidStatusCode:
            return await self.delayed_update(60)

        self.updated = datetime.datetime.now()

    async def delayed_update(self, after: float):
        await asyncio.sleep(after)
        await self.update()

    async def download_all(self):
        downloaded: dict[RawSchedule, bytes] = {}

        download_tasks = []

        async def download(schedule: RawSchedule):
            response = await schedule.request()

            if response.status != 200:
                raise error.InvalidStatusCode(response.status)
            
            byte_response = await response.read()
            downloaded.update({schedule: byte_response})
        
        for schedule in self.types:
            download_tasks.append(download(schedule))
        
        await asyncio.gather(*download_tasks)
        
        for (schedule, content) in downloaded.items():
            await schedule.write(content)


INDEX = Index(
    path     = Path(".", "data", "index.json"),
    contents = None,
    updated  = None,
    types    = None,
)

FT_WEEKLY = RawSchedule(
    type         = RawType.FT_WEEKLY,
    path         = Path(".", "data", "ft_weekly.zip"),
    url          = "https://docs.google.com/document/d/1FH4ctIgRX1fWjIPoboXWieEYVMDYSlg4/export?format=zip",
    friendly_url = "https://docs.google.com/document/d/1FH4ctIgRX1fWjIPoboXWieEYVMDYSlg4",
    sha256       = None,
    contents     = None,
)
FT_DAILY = RawSchedule(
    type         = RawType.FT_DAILY,
    path         = Path(".", "data", "ft_daily.zip"),
    url          = "https://docs.google.com/document/d/1gsE6aikIQ1umKSQWVnyn3_59mnGQQU8O/export?format=zip",
    friendly_url = "https://docs.google.com/document/d/1gsE6aikIQ1umKSQWVnyn3_59mnGQQU8O",
    sha256       = None,
    contents     = None,
)
R_WEEKLY = RawSchedule(
    type         = RawType.R_WEEKLY,
    path         = Path(".", "data", "r_weekly.zip"),
    url          = "https://docs.google.com/spreadsheets/d/1SWv7ARLLC6S_FjIzzhUz0kzGCdG53t9xL68VPoiYlnA/export?format=zip",
    friendly_url = "https://docs.google.com/spreadsheets/d/1SWv7ARLLC6S_FjIzzhUz0kzGCdG53t9xL68VPoiYlnA",
    sha256       = None,
    contents     = None,
)