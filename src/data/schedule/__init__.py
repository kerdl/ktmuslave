from __future__ import annotations

import datetime
from typing import Literal, Optional, Generic, TypeVar
from typing_extensions import Self
from dataclasses import dataclass
from pydantic import BaseModel, Field
from src.parse import pattern
from src.data import RepredBaseModel, week
from src.data.weekday import WEEKDAYS
from src.data.schedule import raw
from src.data.range import Range


T = TypeVar("T")


class Format:
    FULLTIME = "fulltime"
    REMOTE = "remote"
    UNKNOWN = "unknown"

FORMAT_LITERAL = Literal[
    "fulltime",
    "remote",
    "unknown"
]


class AttenderKind:
    TEACHER = "teacher"
    GROUP = "group"
    VACANCY = "vacancy"

ATTENDER_KIND_LITERAL = Literal[
    "teacher",
    "group",
    "vacancy"
]


NO_NAME = "Без имени"


class GetDate:
    def get_date(self) -> datetime.date: ...


@dataclass
class Weeked(Generic[T]):
    week: Range[datetime.date]
    data: T

    @classmethod
    def chunk_by_weeks(cls, pack: list[GetDate]) -> list[Self]:
        """
        # Chunk a days container by weeks
        """
        chunks: list[Weeked] = []
        
        current_week: Optional[Range[datetime.date]] = None
        hold: list[Day] = []
        
        for idx, day in enumerate(pack):
            try:
                next_day = pack[idx+1]
                next_day_week = week.from_day(next_day.get_date())
                is_last = False
            except IndexError:
                next_day = None
                next_day_week = None
                is_last = True
            
            day_week = week.from_day(day.get_date())
            
            if current_week is None:
                current_week = day_week
            
            hold.append(day)
            
            if next_day_week != current_week or is_last:
                weeked = Weeked(week=day_week, data=hold)
                chunks.append(weeked)
                hold = []
                current_week = next_day_week
        
        return chunks


class Schedule(BaseModel):
    """
    # User's schedule flags
    
    This is a part of database structure
    holding temporary formation identifiers
    and week navigation.
    
    Everytime the user
        **uses fast lookup of another groups or teachers**,
        these temporary identifiers are stored here.
        **browses past or future weeks**,
        current week range is stored here.
    """
    temp_group: Optional[str] = None
    """
    # Temporary group
    
    This value overrides the group specified in settings.
    
    Holds a group identifier that the user had typed
    in hub to quickly view ther schedule.
    """
    temp_teacher: Optional[str] = None
    """
    # Temporary teacher
    
    This value overrides the teacher specified in settings.
    
    Holds a teacher identifier that the user had typed
    in hub to quickly view ther schedule.
    """
    temp_mode: Optional[str] = None
    """
    # Temporary mode
    
    This value overrides the mode specified in settings.
    
    This is set according to which identifier
    was requested: a group or a teacher.
    """
    temp_week: Optional[Range[datetime.date]] = None
    """
    # Temporary week range
    
    Hub has navigation arrows which allow
    to view past or future weeks.
    
    This value stores currently selected
    week date range.
    
    If this value is None, assume current week.
    """

    def reset_temp_mode(self):
        """
        # Reset all temporary identifiers
        """
        self.temp_group = None
        self.temp_teacher = None
        self.temp_mode = None
    
    def reset_temp_week(self):
        """
        # Reset temporary week
        """
        self.temp_week = None
    
    def reset_temps(self):
        """
        # Reset all temporary flags
        """
        self.reset_temp_mode()
        self.reset_temp_week()
    
    def get_week_or_current(self) -> Range[datetime.date]:
        """
        # Get `temp_week` or a current one
        """
        if self.temp_week is not None: return self.temp_week
        else: return week.current_active()
    

class Cabinet(BaseModel):
    recovered: bool
    primary: Optional[str]
    """
    # A value taken from the original schedule
    """
    opposite: Optional[str]
    """
    # A value taken from the opposite schedule
    This is only used to shame the people
    responsible for maintaining the schedule
    if `primary` and `opposite` don't match.
    These differences are shown in the formatted schedule.
    
    ## For example
    If this instance belongs to a group schedule,
    `opposite` would reference a cabinet found in
    teacher's schedule.
    """

    def do_versions_match(self) -> bool:
        """
        # Basic comparison
        Tests if `primary` == `opposite`.
        
        ## Do not use in formatting
        `primary` and `opposite` may be the same
        from a human perspective,
        but have differences in how they are written.
        
        ## Example
        ```
        cab = Cabinet(primary="каб. 39а", opposite="39а")
        cab.do_version_match() // False
        ```
        """
        self.primary == self.opposite
    
    def do_versions_match_complex(self) -> bool:
        """
        # Complex comparison
        Tests if `primary` == `opposite`,
        but preprocesses both with regexes
        for more accurate results.
        
        ## Good to use in formatting
        `primary` and `opposite` are both preprocessed
        to remove excess garbage
        (like prefix and punctuation)
        and compares just the numbers.
        
        ## Example
        ```
        cab = Cabinet(primary="каб. 39а", opposite="39а")
        cab.do_version_match_complex() // True
        
        cab = Cabinet(primary="каб. 39б", opposite="39а")
        cab.do_version_match_complex() // False
        ```
        """
        if self.primary is None and self.opposite is not None:
            return False
        if self.primary is not None and self.opposite is None:
            return False
        if self.primary is None and self.opposite is None:
            return True

        primary_contains_digits = pattern.DIGIT.search(self.primary)
        opposite_contains_digits = pattern.DIGIT.search(self.opposite)
        
        clean_primary = self.primary.lower().replace(
            "каб", ""
        ) if primary_contains_digits else self.primary
        clean_opposite = self.opposite.lower().replace(
            "каб", ""
        ) if opposite_contains_digits else self.opposite
        
        # remove punctuation
        clean_primary = pattern.SPACE.sub("", clean_primary)
        clean_opposite = pattern.SPACE.sub("", clean_opposite)
        clean_primary = pattern.PUNCTUATION.sub("", clean_primary)
        clean_opposite = pattern.PUNCTUATION.sub("", clean_opposite)
        
        return clean_primary == clean_opposite


class Attender(RepredBaseModel):
    """
    # Either a teacher or a group
    """
    raw: str
    recovered: bool
    kind: ATTENDER_KIND_LITERAL
    name: str
    cabinet: Cabinet

    @property
    def repr_name(self) -> str:
        name = self.name.replace("\n", "").strip()
        raw = self.raw.replace("\n", "").strip()
        return name or raw or NO_NAME


class Subject(RepredBaseModel):
    raw: str
    recovered: bool
    name: str
    num: int
    format: FORMAT_LITERAL
    attenders: list[Attender]
    """
    # Either teachers or groups
    """

    @property
    def repr_name(self) -> str:
        name = self.name.replace("\n", "").strip()
        raw = self.raw.replace("\n", "").strip()
        return name or raw or NO_NAME

    def is_unknown_window(self) -> bool:
        """
        # Is this subject cannot be classified
        """
        return self.raw != "" and len(self.attenders) < 1


class Day(RepredBaseModel, GetDate):
    raw: str
    recovered: bool
    date: datetime.date
    subjects: list[Subject]

    @property
    def repr_name(self) -> str:
        return WEEKDAYS[self.date.weekday()]
    
    def get_date(self) -> datetime.date:
        return self.date


class Formation(RepredBaseModel):
    """
    # Either a group or a teacher
    """
    raw: str
    recovered: bool
    name: str
    days: list[Day]
    days_weekly_chunked: list[Weeked[list[Day]]] = Field(
        default_factory=list
    )
    """
    # Days chunked by week
    """

    @property
    def repr_name(self) -> str:
        return self.name or NO_NAME
    
    def _chunk_by_weeks(self):
        self.days_weekly_chunked = Weeked[list[Day]].chunk_by_weeks(pack=self.days)
    
    def _copy_weeked(self, weeked: Weeked[list[Day]]) -> Weeked[Formation]:
        form = Formation(
            raw=self.raw,
            recovered=self.recovered,
            name=self.name,
            days=weeked.data,
            days_weekly_chunked=[weeked]
        )
        return Weeked(week=weeked.week, data=form)
    
    def get_week_range(self) -> Optional[Range[datetime.date]]:
        try:
            return self.days_weekly_chunked[0].week
        except IndexError:
            return None
    
    def get_days(self) -> list[GetDate]:
        return self.days
    
    def get_week(self, rng: Range[datetime.date]) -> Optional[list[Day]]:
        for weeked in self.days_weekly_chunked:
            if weeked.week == rng:
                return weeked.data
    
    def get_week_self(self, rng: Range[datetime.date]) -> Optional[Formation]:
        w = self.get_week(rng)
        if w is None: return None
        return Formation(
            raw=self.raw,
            recovered=self.recovered,
            name=self.name,
            days=w,
            days_weekly_chunked=[Weeked[list[Day]](week=rng, data=w)]
        )
    
    def prev_week(self, rng: Range[datetime.date]) -> Optional[Weeked[list[Day]]]:
        for idx, weeked in enumerate(self.days_weekly_chunked):
            if weeked.week != rng: continue
            prev_idx = idx - 1
            if prev_idx < 0: return None
            return self.days_weekly_chunked[prev_idx]
    
    def prev_week_self(self, rng: Range[datetime.date]) -> Optional[Weeked[Formation]]:
        w = self.prev_week(rng)
        if w is None: return None
        return self._copy_weeked(w)
    
    def nearest_prev_week(self, rng: Range[datetime.date]) -> Optional[Weeked[list[Day]]]:
        try:
            return next(filter(
                lambda weeked: rng > weeked.week,
                reversed(self.days_weekly_chunked)
            ))
        except StopIteration:
            return None
    
    def nearest_prev_week_self(self, rng: Range[datetime.date]) -> Optional[Weeked[Formation]]:
        w = self.nearest_prev_week(rng)
        if w is None: return None
        return self._copy_weeked(w)
    
    def next_week(self, rng: Range[datetime.date]) -> Optional[Weeked[list[Day]]]:
        for idx, weeked in enumerate(self.days_weekly_chunked):
            if weeked.week != rng: continue
            try: return self.days_weekly_chunked[idx+1]
            except IndexError: return None
    
    def next_week_self(self, rng: Range[datetime.date]) -> Optional[Weeked[Formation]]:
        w = self.next_week(rng)
        if w is None: return None
        return self._copy_weeked(w)
    
    def nearest_next_week(self, rng: Range[datetime.date]) -> Optional[Weeked[list[Day]]]:
        try:
            return next(filter(
                lambda weeked: rng < weeked.week,
                self.days_weekly_chunked
            ))
        except StopIteration:
            return None
    
    def nearest_next_week_self(self, rng: Range[datetime.date]) -> Optional[Weeked[Formation]]:
        w = self.nearest_next_week(rng)
        if w is None: return None
        return self._copy_weeked(w)
    
    def first_week(self) -> Optional[Weeked[list[Day]]]:
        try: return self.days_weekly_chunked[0]
        except: return None
    
    def first_week_self(self, rng: Range[datetime.date]) -> Optional[Weeked[Formation]]:
        w = self.first_week(rng)
        if w is None: return None
        return self._copy_weeked(w)
    
    def last_week(self) -> Optional[Weeked[list[Day]]]:
        try: return self.days_weekly_chunked[-1]
        except: return None

    def last_week_self(self, rng: Range[datetime.date]) -> Optional[Weeked[Formation]]:
        w = self.last_week(rng)
        if w is None: return None
        return self._copy_weeked(w)

class Page(BaseModel):
    kind: raw.KIND_LITERAL
    date: Range[datetime.date]
    formations: list[Formation]
    """
    # Either groups or teachers
    """

    def _chunk_formations_by_week(self):
        for form in self.formations:
            form._chunk_by_weeks()

    def names(self) -> list[str]:
        return [formation.name for formation in self.formations]

    def get_by_name(self, name: str) -> Optional[Formation]:
        for formation in self.formations:
            if formation.name == name:
                return formation
        
        return None
