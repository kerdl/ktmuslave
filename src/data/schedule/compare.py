from typing import TypeVar, Generic, Optional
from pydantic import BaseModel
import datetime

from src.data.weekday import WEEKDAY_LITERAL
from src.data.range import Range

T = TypeVar("T")


class Changes(BaseModel, Generic[T]):
    appeared: list[T]
    disappeared: list[T]
    changed: list[T]
    unchanged: list[T]

class PrimitiveChange(BaseModel, Generic[T]):
    old: Optional[T]
    new: T


class SubjectCompare(BaseModel):
    name: str
    teachers: Changes[str]
    cabinet: PrimitiveChange[str]
    time: PrimitiveChange[Range[datetime.time]]

class DayCompare(BaseModel):
    weekday: WEEKDAY_LITERAL
    subjects: Changes[SubjectCompare]

class GroupCompare(BaseModel):
    name: str
    days: Changes[DayCompare]

class PageCompare(BaseModel):
    raw: str
    groups: Changes[GroupCompare]