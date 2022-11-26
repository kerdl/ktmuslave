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


class Changes(GenericModel, Generic[CMP_T, ORIGNAL_T]):
    appeared: list[ORIGNAL_T]
    disappeared: list[ORIGNAL_T]
    changed: list[CMP_T]

class PrimitiveChange(GenericModel, Generic[T]):
    old: Optional[T]
    new: T

    def is_same(self) -> bool:
        return self.old == self.new
    
    def is_different(self) -> bool:
        return not self.is_same()


class SubjectCompare(TranslatedBaseModel, RepredBaseModel):
    name: str
    num: Optional[Union[int, PrimitiveChange[int]]]
    teachers: Optional[Union[list[str], Changes[str, str]]]
    cabinet: Optional[Union[Optional[str], PrimitiveChange[Optional[str]]]]
    time: Optional[Union[Range[datetime.time], PrimitiveChange[Range[datetime.time]]]]

    __translation__: ClassVar[dict[str, str]] = {
        "name": "Пара",
        "num": "Номер",
        "teachers": "Преподы",
        "cabinet": "Кабинет",
        "time": "Время"
    }

    @property
    def repr_name(self) -> str:
        return self.name

class DayCompare(RepredBaseModel):
    weekday: WEEKDAY_LITERAL
    subjects: Changes[SubjectCompare, Subject]

    @property
    def repr_name(self) -> str:
        return self.weekday

class GroupCompare(RepredBaseModel):
    name: str
    days: Changes[DayCompare, Day]

    @property
    def repr_name(self) -> str:
        return self.name

class PageCompare(BaseModel):
    raw: str
    date: PrimitiveChange[Range[datetime.date]]
    groups: Changes[GroupCompare, Group]