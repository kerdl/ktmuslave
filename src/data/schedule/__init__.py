from __future__ import annotations
import datetime
from typing import Literal, Optional, TypeVar
from dataclasses import dataclass
from pydantic import BaseModel
from time import time

from src.data import RepredBaseModel
from src.data.weekday import WEEKDAY_LITERAL
from src.data.schedule import raw
from src.data.range import Range


T = TypeVar("T")


MATERIALS_URL = "https://docs.google.com/document/d/1mvj8U4vejPYjQL0VH2FRHa-_4zbwtMguv4GXSYidmKM"
JOURNALS_URL = "https://drive.google.com/drive/folders/17sbp95SfRhU1JPII5S_uibxj27t9zpFM"


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

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "is_folded": self.is_folded
        }

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

    def to_dict(self) -> dict:
        return {
            "message": self.message.to_dict(),
            "last_update": self.last_update
        }

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

    async def update(self):
        from src.api.schedule import SCHEDULE_API

        response = await SCHEDULE_API.update()

        self.last_update = time()

        return response.data.notify

class Subject(RepredBaseModel):
    raw: str
    num: int
    time: Range[datetime.time]
    name: str
    format: FORMAT_LITERAL
    teachers: list[str]
    cabinet: Optional[str]

    def is_unknown_window(self) -> bool:
        return self.raw != "" and len(self.teachers) < 1

    @property
    def repr_name(self) -> str:
        return self.name


class Day(RepredBaseModel):
    raw: str
    weekday: WEEKDAY_LITERAL
    date: datetime.date
    subjects: list[Subject]

    @property
    def repr_name(self) -> str:
        return self.weekday


class Group(RepredBaseModel):
    raw: str
    name: str
    days: list[Day]

    @property
    def repr_name(self) -> str:
        return self.name


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
