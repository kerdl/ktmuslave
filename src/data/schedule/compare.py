from __future__ import annotations

import datetime
from typing import (
    TypeVar,
    Generic,
    Optional,
    ClassVar
)
from typing_extensions import Self
from pydantic import BaseModel, Field
from src.data import (
    TranslatedBaseModel,
    RepredBaseModel
)
from src.data.weekday import WEEKDAYS
from src.data.range import Range
from src.data.schedule import (
    Weeked,
    GetDate,
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
    appeared: list[ORIGNAL_T] = Field(default_factory=list)
    disappeared: list[ORIGNAL_T] = Field(default_factory=list)
    changed: list[CMP_T] = Field(default_factory=list)


class Changes(BaseModel, Generic[T]):
    appeared: list[T] = Field(default_factory=list)
    disappeared: list[T] = Field(default_factory=list)
    changed: list[T] = Field(default_factory=list)


class PrimitiveChange(BaseModel, Generic[T]):
    old: Optional[T] = None
    new: Optional[T] = None

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


class AttenderCompare(RepredBaseModel):
    name: Optional[str] = None
    cabinet: CabinetCompare = Field(default_factory=CabinetCompare)

    @property
    def repr_name(self) -> str:
        return self.name or ""


class SubjectCompare(TranslatedBaseModel, RepredBaseModel):
    name: Optional[str] = None
    num: Optional[PrimitiveChange[int]] = None
    attenders: Optional[DetailedChanges[AttenderCompare, Attender]] = None

    __translation__: ClassVar[dict[str, str]] = {
        "name": "Пара",
        "num": "Номер",
        "attenders": "Посетители"
    }

    @property
    def repr_name(self) -> str:
        return self.name or ""


class DayCompare(RepredBaseModel, GetDate):
    date: Optional[datetime.date] = None
    subjects: DetailedChanges[SubjectCompare, Subject] = Field(
        default_factory=DetailedChanges
    )

    @property
    def repr_name(self) -> str:
        return WEEKDAYS[self.date.weekday()]
    
    def get_date(self) -> datetime.date:
        return self.date


class FormationCompare(RepredBaseModel):
    name: Optional[str] = None
    days: DetailedChanges[DayCompare, Day] = Field(
        default_factory=DetailedChanges
    )
    days_weekly_chunked: DetailedChanges[Weeked[list[DayCompare]], Weeked[list[Day]]] = Field(
        default_factory=list
    )

    @property
    def repr_name(self) -> str:
        return self.name or ""
    
    def _chunk_by_weeks(self) -> None:
        appeared = Weeked[list[Day]].chunk_by_weeks(pack=self.days.appeared)
        disappeared = Weeked[list[Day]].chunk_by_weeks(pack=self.days.disappeared)
        changed = Weeked[list[DayCompare]].chunk_by_weeks(pack=self.days.changed)
        
        self.days_weekly_chunked = (
            DetailedChanges[Weeked[list[DayCompare]], Weeked[list[Day]]](
                appeared=appeared,
                disappeared=disappeared,
                changed=changed
            )
        )
    
    def get_week_range(self) -> Optional[Range[datetime.date]]:
        try:
            if self.days_weekly_chunked.appeared:
                return self.days_weekly_chunked.appeared[0].week
            if self.days_weekly_chunked.disappeared:
                return self.days_weekly_chunked.disappeared[0].week
            if self.days_weekly_chunked.changed:
                return self.days_weekly_chunked.changed[0].week
        except (AttributeError, IndexError):
            return None
    
    def get_week_self(
        self,
        rng: Range[datetime.date]
    ) -> Self:
        appeared = None
        disappeared = None
        changed = None
        
        try: appeared = next(
            day for day in self.days_weekly_chunked.appeared if day.week == rng
        )
        except StopIteration: ...
        try: disappeared = next(
            day for day in self.days_weekly_chunked.disappeared if day.week == rng
        )
        except StopIteration: ...
        try: changed = next(
            day for day in self.days_weekly_chunked.changed if day.week == rng
        )
        except StopIteration: ...
        
        return FormationCompare(
            name=self.name,
            days=DetailedChanges[DayCompare, Day](
                appeared=appeared.data if appeared else [],
                disappeared=disappeared.data if disappeared else [],
                changed=changed.data if changed else []
            ),
            days_weekly_chunked=DetailedChanges[Weeked[list[DayCompare]], Weeked[list[Day]]](
                appeared=[appeared] if appeared else [],
                disappeared=[disappeared] if disappeared else [],
                changed=[changed] if changed else []
            )
        )


class PageCompare(BaseModel):
    date: PrimitiveChange[Range[datetime.date]] = Field(
        default_factory=PrimitiveChange
    )
    formations: DetailedChanges[FormationCompare, Formation] = Field(
        default_factory=DetailedChanges
    )
    
    def _chunk_formations_by_week(self) -> None:
        for form in self.formations.appeared:
            form._chunk_by_weeks()
            
        for form in self.formations.disappeared:
            form._chunk_by_weeks()
            
        for form in self.formations.changed:
            form._chunk_by_weeks()
    
    def get_week_range(self) -> Optional[Range[datetime.date]]:
        try:
            if self.formations.appeared:
                return self.formations.appeared[0].get_week_range()
            if self.formations.disappeared:
                return self.formations.disappeared[0].get_week_range()
            if self.formations.changed:
                return self.formations.changed[0].get_week_range()
        except (AttributeError, IndexError):
            return None
    
    def get_week_self(self, rng: Range[datetime.date]) -> Self:
        appeared = []
        disappeared = []
        changed = []
        
        for form in self.formations.appeared:
            weeked = form.get_week_self(rng)
            if weeked is None: continue
            appeared.append(weeked)
            
        for form in self.formations.disappeared:
            weeked = form.get_week_self(rng)
            if weeked is None: continue
            disappeared.append(weeked)
            
        for form in self.formations.changed:
            weeked = form.get_week_self(rng)
            if weeked is None: continue
            changed.append(weeked)
        
        return PageCompare(
            date=self.date,
            formations=DetailedChanges[FormationCompare, Formation](
                appeared=appeared,
                disappeared=disappeared,
                changed=changed
            )
        )
            


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
