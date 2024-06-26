from typing import TypeVar, Generic, Optional, Union, ClassVar
from pydantic import BaseModel, validator
from pydantic.generics import GenericModel
import datetime

from src.data import TranslatedBaseModel, RepredBaseModel
from src.data.weekday import WEEKDAY_LITERAL
from src.data.range import Range
from src.data.schedule import Page, Group, Day, Subject, TchrPage, TchrTeacher, TchrDay, TchrSubject, Subgroup


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

class TchrSubjectCompare(TranslatedBaseModel, RepredBaseModel):
    name: Optional[str]
    num: Optional[PrimitiveChange[int]]
    groups: Optional[Changes[Subgroup]]
    cabinet: Optional[PrimitiveChange[Optional[str]]]
    time: Optional[PrimitiveChange[Range[datetime.time]]]

    __translation__: ClassVar[dict[str, str]] = {
        "name": "Пара",
        "num": "Номер",
        "groups": "Группы",
        "cabinet": "Кабинет",
        "time": "Время"
    }

    @property
    def repr_name(self) -> str:
        return self.name or ""

class TchrDayCompare(RepredBaseModel):
    weekday: Optional[WEEKDAY_LITERAL]
    subjects: DetailedChanges[TchrSubjectCompare, TchrSubject]

    @property
    def repr_name(self) -> str:
        return self.weekday or ""

class TchrTeacherCompare(RepredBaseModel):
    name: Optional[str]
    days: DetailedChanges[TchrDayCompare, TchrDay]

    @property
    def repr_name(self) -> str:
        return self.name or ""

class TchrPageCompare(BaseModel):
    raw: Optional[str]
    date: PrimitiveChange[Range[datetime.date]]
    teachers: DetailedChanges[TchrTeacherCompare, TchrTeacher]

def cmp_subject(a: Subject, b: Subject, ignored_keys: list[str]) -> bool:
    mapping = {}
    mapping["raw"] = a.raw == b.raw
    mapping["num"] = a.num == b.num
    mapping["time"] = a.time == b.time
    mapping["name"] = a.name == b.name
    mapping["format"] = a.format == b.format
    mapping["teachers"] = a.teachers == b.teachers
    mapping["cabinet"] = a.cabinet == b.cabinet

    checks = [mapping[key] for key in mapping.keys() if key not in ignored_keys]

    return all(checks)

def cmp_tchr_subject(a: TchrSubject, b: TchrSubject, ignored_keys: list[str]) -> bool:
    mapping = {}
    mapping["raw"] = a.raw == b.raw
    mapping["num"] = a.num == b.num
    mapping["time"] = a.time == b.time
    mapping["name"] = a.name == b.name
    mapping["format"] = a.format == b.format
    mapping["groups"] = a.groups == b.groups
    mapping["cabinet"] = a.cabinet == b.cabinet

    checks = [mapping[key] for key in mapping.keys() if key not in ignored_keys]

    return all(checks)

def cmp_subjects(subjects: list[Subject], ignored_keys: list[str]) -> bool:
    if len(subjects) < 2:
        return True
    if len(subjects) == 2:
        return cmp_subject(subjects[0], subjects[1], ignored_keys)

    compares = []

    for i in range(0, len(subjects)-1):
        curr_subj = subjects[i]
        next_subj = subjects[i+1] if len(subjects)-1 >= i+1 else None

        if next_subj is not None:
            compares.append(cmp_subject(curr_subj, next_subj, ignored_keys)) 

    return all(compares)

def cmp_tchr_subjects(subjects: list[TchrSubject], ignored_keys: list[str]) -> bool:
    if len(subjects) < 2:
        return True
    if len(subjects) == 2:
        return cmp_subject(subjects[0], subjects[1], ignored_keys)

    compares = []

    for i in range(0, len(subjects)-1):
        curr_subj = subjects[i]
        next_subj = subjects[i+1] if len(subjects)-1 >= i+1 else None

        if next_subj is not None:
            compares.append(cmp_tchr_subject(curr_subj, next_subj, ignored_keys)) 

    return all(compares)    