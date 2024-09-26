from __future__ import annotations
import datetime
from typing import Literal, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from src.parse import pattern
from src.data import RepredBaseModel, week
from src.data.weekday import WEEKDAYS
from src.data.schedule import raw
from src.data.range import Range


class Format:
    FULLTIME = "fulltime"
    REMOTE = "remote"
    UNKNOWN = "unknown"

FORMAT_LITERAL = Literal["fulltime", "remote", "unknown"]

class AttenderKind:
    TEACHER = "teacher"
    GROUP = "group"
    VACANCY = "vacancy"

ATTENDER_KIND_LITERAL = Literal["teacher", "group", "vacancy"]


class Schedule(BaseModel):
    temp_group: Optional[str] = None
    """
    # Temporary group
    
    This value has higher priority:
    overrides the group specified in settings.
    
    If this is not `None`, user had typed this group
    while being in a hub to quickly view their schedule.
    """
    temp_teacher: Optional[str] = None
    """
    # Temporary teacher
    
    This value has higher priority:
    overrides the teacher specified in settings.
    
    If this is not `None`, user had typed this teacher
    while being in a hub to quickly view their schedule.
    """
    temp_mode: Optional[str] = None
    """
    # Temporary mode
    
    Similar to `temp_group` and `temp_teacher`:
    overrides the mode specified in settings.
    
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
    """

    def reset_temp_mode(self):
        self.temp_group = None
        self.temp_teacher = None
        self.temp_mode = None
    
    def reset_temp_week(self):
        self.temp_week = None
    
    def reset_temps(self):
        self.reset_temp_mode()
        self.reset_temp_week()
    
    def get_week_or_current(self) -> Range[datetime.date]:
        """
        # Get `temp_week` or a current one
        """
        if self.temp_week is not None: return self.temp_week
        else: return week.current_active()
    
    def is_week_greater_than_now(self) -> bool:
        return self.get_week_or_current() > week.current_active()
    
    def is_week_less_than_now(self) -> bool:
        return self.get_week_or_current() < week.current_active()
    
    def is_week_equal_to_now(self) -> bool:
        return self.temp_week is None


class Cabinet(BaseModel):
    primary: Optional[str]
    opposite: Optional[str]

    def do_versions_match(self) -> bool:
        """
        # Basic comparison
        Tests if `primary` == `opposite`
        """
        self.primary == self.opposite
    
    def do_versions_match_complex(self) -> bool:
        """
        # Complex comparison
        Tests if `primary` == `opposite`,
        but preprocesses both with regexes
        for more accurate results
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

@dataclass
class DaysWithWeek:
    """
    Shorthand for `dww`
    """
    week: Range[datetime.date]
    days: list[Day]

@dataclass
class FormationWithWeek:
    """
    Shorthand for `fww`
    """
    week: Range[datetime.date]
    formation: Formation

class Formation(RepredBaseModel):
    raw: str
    name: str
    days: list[Day]
    days_weekly_chunked: list[DaysWithWeek] = Field(default_factory=list)

    @property
    def repr_name(self) -> str:
        return self.name
    
    def _chunk_by_weeks(self):
        chunks: list[DaysWithWeek] = []
        
        current_week: Optional[Range[datetime.date]] = None
        hold: list[Day] = []
        
        for idx, day in enumerate(self.days):
            try:
                next_day = self.days[idx+1]
                next_day_week = week.from_day(next_day.date)
                is_last = False
            except IndexError:
                next_day = None
                next_day_week = None
                is_last = True
            
            day_week = week.from_day(day.date)
            
            if current_week is None:
                current_week = day_week
            
            hold.append(day)
            
            if next_day_week != current_week or is_last:
                dww = DaysWithWeek(week=day_week, days=hold)
                chunks.append(dww)
                hold = []
                current_week = next_day_week
        
        self.days_weekly_chunked = chunks
    
    def _copy_as_fww(self, dww: DaysWithWeek) -> FormationWithWeek:
        form = Formation(
            raw=self.raw,
            name=self.name,
            days=dww.days,
            days_weekly_chunked=[dww]
        )
        return FormationWithWeek(week=dww.week, formation=form)
    
    def get_week(self, rng: Range[datetime.date]) -> Optional[DaysWithWeek]:
        for dww in self.days_weekly_chunked:
            if dww.week == rng:
                return dww
    
    def get_week_self(self, rng: Range[datetime.date]) -> Optional[FormationWithWeek]:
        w = self.get_week(rng)
        if w is None: return None
        return self._copy_as_fww(w)
    
    def prev_week(self, rng: Range[datetime.date]) -> Optional[DaysWithWeek]:
        for idx, dww in enumerate(self.days_weekly_chunked):
            if dww.week != rng: continue
            try: return self.days_weekly_chunked[idx-1]
            except IndexError: return None
    
    def prev_week_self(self, rng: Range[datetime.date]) -> Optional[FormationWithWeek]:
        w = self.prev_week(rng)
        if w is None: return None
        return self._copy_as_fww(w)
    
    def next_week(self, rng: Range[datetime.date]) -> Optional[DaysWithWeek]:
        for idx, dww in enumerate(self.days_weekly_chunked):
            if dww.week != rng: continue
            try: return self.days_weekly_chunked[idx+1]
            except IndexError: return None
    
    def next_week_self(self, rng: Range[datetime.date]) -> Optional[FormationWithWeek]:
        w = self.next_week(rng)
        if w is None: return None
        return self._copy_as_fww(w)
    
    def first_week(self) -> Optional[DaysWithWeek]:
        try: return self.days_weekly_chunked[0]
        except: return None
    
    def first_week_self(self, rng: Range[datetime.date]) -> Optional[FormationWithWeek]:
        w = self.first_week(rng)
        if w is None: return None
        return self._copy_as_fww(w)
    
    def last_week(self) -> Optional[DaysWithWeek]:
        try: return self.days_weekly_chunked[-1]
        except: return None

    def last_week_self(self, rng: Range[datetime.date]) -> Optional[FormationWithWeek]:
        w = self.last_week(rng)
        if w is None: return None
        return self._copy_as_fww(w)

class Page(BaseModel):
    kind: raw.KIND_LITERAL
    date: Range[datetime.date]
    formations: list[Formation]

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
