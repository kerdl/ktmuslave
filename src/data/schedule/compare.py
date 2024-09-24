import datetime
from typing import (
    TypeVar,
    Generic,
    Optional,
    ClassVar
)
from pydantic import BaseModel
from src.data import (
    TranslatedBaseModel,
    RepredBaseModel
)
from src.data.weekday import WEEKDAYS
from src.data.range import Range
from src.data.schedule import (
    Formation,
    Day,
    Subject,
    Attender
)


T = TypeVar("T")
CMP_T = TypeVar("CMP_T")
ORIGNAL_T = TypeVar("ORIGNAL_T")


class ChangeType:
    APPEARED = "appeared"
    DISAPPEARED = "disappeared"
    CHANGED = "changed"


class DetailedChanges(BaseModel, Generic[CMP_T, ORIGNAL_T]):
    appeared: list[ORIGNAL_T]
    disappeared: list[ORIGNAL_T]
    changed: list[CMP_T]

class Changes(BaseModel, Generic[T]):
    appeared: list[T]
    disappeared: list[T]
    changed: list[T]

class PrimitiveChange(BaseModel, Generic[T]):
    old: Optional[T]
    new: Optional[T]

    def is_same(self) -> bool:
        return self.old == self.new
    
    def is_different(self) -> bool:
        return not self.is_same()


class CabinetCompare(TranslatedBaseModel):
    primary: Optional[PrimitiveChange[str]] = None
    opposite: Optional[PrimitiveChange[str]] = None

    __translation__: ClassVar[dict[str, str]] = {
        "primary": "Первичный",
        "opposite": "Противоположный"
    }

class AttenderCompate(RepredBaseModel):
    name: Optional[str] = None
    cabinet: CabinetCompare

    @property
    def repr_name(self) -> str:
        return self.name or ""

class SubjectCompare(TranslatedBaseModel, RepredBaseModel):
    name: Optional[str] = None
    num: Optional[PrimitiveChange[int]] = None
    attenders: Optional[DetailedChanges[AttenderCompate, Attender]] = None

    __translation__: ClassVar[dict[str, str]] = {
        "name": "Пара",
        "num": "Номер",
        "attenders": "Посетители"
    }

    @property
    def repr_name(self) -> str:
        return self.name or ""

class DayCompare(RepredBaseModel):
    date: Optional[datetime.date] = None
    subjects: DetailedChanges[SubjectCompare, Subject]

    @property
    def repr_name(self) -> str:
        return WEEKDAYS[self.date.weekday()]

class FormationCompare(RepredBaseModel):
    name: Optional[str] = None
    days: DetailedChanges[DayCompare, Day]

    @property
    def repr_name(self) -> str:
        return self.name or ""

class PageCompare(BaseModel):
    date: PrimitiveChange[Range[datetime.date]]
    formations: DetailedChanges[FormationCompare, Formation]


def cmp_subject(
    a: Subject,
    b: Subject,
    ignored_keys: list[str]
) -> bool:
    mapping = {}
    mapping["name"] = a.name == b.name
    mapping["num"] = a.num == b.num
    mapping["attenders"] = a.attenders == b.attenders

    checks = [
        mapping[key] for key in mapping.keys()
        if key not in ignored_keys
    ]

    return all(checks)

def cmp_subjects(
    subjects: list[Subject],
    ignored_keys: list[str]
) -> bool:
    if len(subjects) < 2:
        return True
    if len(subjects) == 2:
        return cmp_subject(subjects[0], subjects[1], ignored_keys)

    compares = []

    for i in range(0, len(subjects)-1):
        curr_subj = subjects[i]
        next_subj = subjects[i+1] if len(subjects)-1 >= i+1 else None

        if next_subj is not None:
            compares.append(
                cmp_subject(curr_subj, next_subj, ignored_keys)
            ) 

    return all(compares)
