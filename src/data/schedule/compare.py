from typing import TypeVar, Generic, Optional, Union, ClassVar
from pydantic import BaseModel, validator
from pydantic.generics import GenericModel
import datetime

from src.data import TranslatedBaseModel, RepredBaseModel
from src.data.weekday import WEEKDAY_LITERAL
from src.data.range import Range
from src.data.schedule import Page, Group, Day, Subject


T = TypeVar("T")
CMP_T = TypeVar("CMP_T")
ORIGNAL_T = TypeVar("ORIGNAL_T")


class ChangeType:
    APPEARED = "appeared"
    DISAPPEARED = "disappeared"
    CHANGED = "changed"


class DetailedChanges(GenericModel, Generic[CMP_T, ORIGNAL_T]):
    appeared: list[ORIGNAL_T]
    disappeared: list[ORIGNAL_T]
    changed: list[CMP_T]

class Changes(GenericModel, Generic[T]):
    appeared: list[T]
    disappeared: list[T]
    changed: list[T]
    unchanged: list[T]

class PrimitiveChange(GenericModel, Generic[T]):
    old: Optional[T]
    new: Optional[T]

    def is_same(self) -> bool:
        return self.old == self.new
    
    def is_different(self) -> bool:
        return not self.is_same()


class SubjectCompare(TranslatedBaseModel, RepredBaseModel):
    name: Optional[str]
    num: Optional[PrimitiveChange[int]]
    teachers: Optional[Changes[str]]
    cabinet: Optional[PrimitiveChange[Optional[str]]]
    time: Optional[PrimitiveChange[Range[datetime.time]]]

    __translation__: ClassVar[dict[str, str]] = {
        "name": "Пара",
        "num": "Номер",
        "teachers": "Преподы",
        "cabinet": "Кабинет",
        "time": "Время"
    }

    @property
    def repr_name(self) -> str:
        return self.name or ""

class DayCompare(RepredBaseModel):
    weekday: Optional[WEEKDAY_LITERAL]
    subjects: DetailedChanges[SubjectCompare, Subject]

    @property
    def repr_name(self) -> str:
        return self.weekday or ""

class GroupCompare(RepredBaseModel):
    name: Optional[str]
    days: DetailedChanges[DayCompare, Day]

    @property
    def repr_name(self) -> str:
        return self.name or ""

class PageCompare(BaseModel):
    raw: Optional[str]
    date: PrimitiveChange[Range[datetime.date]]
    groups: DetailedChanges[GroupCompare, Group]