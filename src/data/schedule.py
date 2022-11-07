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
