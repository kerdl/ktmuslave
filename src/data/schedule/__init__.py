from __future__ import annotations
import datetime
from typing import Literal, Optional, TypeVar
from dataclasses import dataclass
from pydantic import BaseModel, Field as PydField
from time import time

from src.data import RepredBaseModel
from src.data.weekday import WEEKDAY_LITERAL
from src.data.schedule import raw
from src.data.range import Range


T = TypeVar("T")


MATERIALS_URL = "https://docs.google.com/document/d/1mvj8U4vejPYjQL0VH2FRHa-_4zbwtMguv4GXSYidmKM"
JOURNALS_URL = "https://drive.google.com/drive/folders/14siGbti1t6X4LY2V5MDFDT786Eu-Py10"


class Type:
    WEEKLY = "weekly"
    DAILY  = "daily"

    @classmethod
    def opposite(cls: type[Type], sc_type: TYPE_LITERAL) -> TYPE_LITERAL:
        if sc_type == cls.WEEKLY:
            return cls.DAILY
        if sc_type == cls.DAILY:
            return cls.WEEKLY

TYPE_LITERAL = Literal["weekly", "daily"]


class Format:
    FULLTIME = "fulltime"
    REMOTE   = "remote"

FORMAT_LITERAL = Literal["fulltime", "remote"]


class Message(BaseModel):
    type: TYPE_LITERAL = Type.WEEKLY
    is_folded: bool = False
    
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


class Schedule(BaseModel):
    message: Message = PydField(default_factory=Message)
    last_update: Optional[float] = 0.0
    temp_group: Optional[str] = None

    
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
