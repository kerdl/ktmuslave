from __future__ import annotations
import datetime
from typing import Literal, Optional, TypeVar
from dataclasses import dataclass
from pydantic import BaseModel
from time import time
from src.data.weekday import WEEKDAY_LITERAL
from src.data.schedule import raw
from src.data.range import Range


T = TypeVar("T")


class Type:
    WEEKLY = "weekly"
    DAILY  = "daily"

TYPE_LITERAL = Literal["weekly", "daily"]


class Format:
    FULLTIME = "fulltime"
    REMOTE   = "remote"

FORMAT_LITERAL = Literal["fulltime", "remote"]


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

    async def update(self) -> bool:
        from src.api.schedule import SCHEDULE_API

        response = await SCHEDULE_API.update()

        self.last_update = time()

        has_daily_updates = response.data.notify.daily is not None
        has_weekly_updates = response.data.notify.weekly is not None

        has_updates = has_daily_updates or has_weekly_updates
        return has_updates

class Subject(BaseModel):
    raw: str
    num: int
    time: Range[datetime.time]
    name: str
    format: FORMAT_LITERAL
    teachers: list[str]
    cabinet: Optional[str]

    def is_unknown_window(self) -> bool:
        return self.raw != "" and len(self.teachers) < 1

class Day(BaseModel):
    raw: str
    weekday: WEEKDAY_LITERAL
    date: datetime.date
    subjects: list[Subject]

class Group(BaseModel):
    raw: str
    name: str
    days: list[Day]

class Page(BaseModel):
    raw: str
    raw_types: list[raw.TYPE_LITERAL]
    sc_type: TYPE_LITERAL
    date: Range[datetime.date]
    groups: list[Group]

    def get_group(self, name: str) -> Optional[Group]:
        for group in self.groups:
            if group.name == name:
                return group
        
        return None