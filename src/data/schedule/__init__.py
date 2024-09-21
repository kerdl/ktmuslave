from __future__ import annotations
import datetime
from typing import Literal, Optional
from pydantic import BaseModel
from src.data import RepredBaseModel
from src.data.weekday import WEEKDAYS
from src.data.schedule import raw
from src.data.range import Range


class Format:
    FULLTIME = "fulltime"
    REMOTE = "remote"

FORMAT_LITERAL = Literal["fulltime", "remote"]

class AttenderKind:
    TEACHER = "teacher"
    GROUP = "group"

ATTENDER_KIND_LITERAL = Literal["teacher", "group"]


class Schedule(BaseModel):
    temp_group: Optional[str] = None
    temp_teacher: Optional[str] = None
    temp_mode: Optional[str] = None

    def reset_temps(self):
        self.temp_group = None
        self.temp_teacher = None
        self.temp_mode = None


class Cabinet(BaseModel):
    primary: Optional[str]
    opposite: Optional[str]

    def do_versions_match(self) -> bool:
        self.primary == self.opposite


class Attender(RepredBaseModel):
    raw: str
    kind: ATTENDER_KIND_LITERAL
    name: str
    cabinet: Cabinet


class Subject(RepredBaseModel):
    raw: str
    name: str
    num: int
    format: FORMAT_LITERAL
    attenders: list[Attender]

    def is_unknown_window(self) -> bool:
        return self.raw != "" and len(self.attenders) < 1

    @property
    def repr_name(self) -> str:
        return self.name


class Day(RepredBaseModel):
    raw: str
    date: datetime.date
    subjects: list[Subject]

    @property
    def repr_name(self) -> str:
        return WEEKDAYS[self.date.weekday()]


class Formation(RepredBaseModel):
    raw: str
    name: str
    days: list[Day]

    @property
    def repr_name(self) -> str:
        return self.name


class Page(BaseModel):
    kind: raw.KIND_LITERAL
    date: Range[datetime.date]
    formations: list[Formation]

    def names(self) -> list[str]:
        return [formation.name for formation in self.formations]

    def get_by_name(self, name: str) -> Optional[Formation]:
        for formation in self.formations:
            if formation.name == name:
                return formation
        
        return None
