from __future__ import annotations
import datetime
from typing import Literal, Optional
from pydantic import BaseModel
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
    temp_week_cached_formation: Optional[Formation] = None
    """
    # Filtered formation within the `temp_week` boundaries
    """
    
    def reset_temp_week_cache(self):
        self.temp_week_cached_formation = None
    
    def reset_temp_week(self):
        self.temp_week = None
        self.reset_temp_week_cache()
    
    def reset_temps(self):
        self.temp_group = None
        self.temp_teacher = None
        self.temp_mode = None
        self.reset_temp_week()
    
    def get_week_or_current(self) -> Range[datetime.date]:
        """
        # Get `temp_week` or a current one
        """
        if self.temp_week is not None: return self.temp_week
        else: return week.current_active()
    
    ### REMOVAL CANDIDATES START
    
    def week_shifted_backward(self) -> Range[datetime.date]:
        """ # Get `temp_week` shifted backward """
        return week.shift_backwards(self.get_week_or_current())
    
    def week_shifted_forward(self) -> Range[datetime.date]:
        """ # Get `temp_week` shifted forward """
        return week.shift_forward(self.get_week_or_current())
    
    def week_shifted_backward_until(self, fn) -> Range[datetime.date]:
        ...
    
    def week_shifted_forward_until(self, fn) -> Range[datetime.date]:
        ...
    
    def shift_week_backward(self):
        """ # Shift `temp_week` backward """
        shifted = self.week_shifted_backward()
        if shifted == week.current_active(): shifted = None
        self.temp_week = shifted
        
    def shift_week_forward(self):
        """ # Shift `temp_week` forward """
        shifted = self.week_shifted_forward()
        if shifted == week.current_active(): shifted = None
        self.temp_week = shifted
        
    
    ### REMOVAL CANDIDATES END
    
    def is_week_greater_than(self, rng: Range[datetime.date]) -> bool:
        return self.get_week_or_current().start > rng.start
    
    def is_week_less_than(self, rng: Range[datetime.date]) -> bool:
        return self.get_week_or_current().start < rng.start 
    
    def is_week_equal_to(self, rng: Range[datetime.date]) -> bool:
        cur = self.get_week_or_current()
        return rng.start == cur.start and rng.end == cur.end
    
    def is_week_greater_than_now(self) -> bool:
        return self.is_week_greater_than(week.current_active())
    
    def is_week_less_than_now(self) -> bool:
        return self.is_week_less_than(week.current_active())
    
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


class Formation(RepredBaseModel):
    raw: str
    name: str
    days: list[Day]

    @property
    def repr_name(self) -> str:
        return self.name
    
    def is_week_within_boundaries(self, rng: Range[datetime.date]) -> bool:
        """
        # Is `rng` within present `days`
        """
        if len(self.days) < 1:
            return False
        
        # schedule parser is guaranteed
        # to sort the days
        minimum = self.days[0].date
        maximum = self.days[-1].date
        
        return rng.start <= maximum and rng.end > minimum
    
    def retain_days_indexed(self, rng: Range[datetime.date]) -> list[tuple[int, Day]]:
        """
        # Only keep days in date range
        Returns a list of days with position indexes.
        """
        kept_days = []
        
        for idx, day in enumerate(self.days):
            if day.date in rng:
                kept_days.append((idx, day))
        
        return kept_days
    
    def retain_days(self, rng: Range[datetime.date]) -> list[Day]:
        """
        # Only keep days in date range
        Returns a list of days.
        """
        return [day for day in map(
            lambda day: day[1], self.retain_days_indexed(rng)
        )]
    
    def retain_days_new(self, rng: Range[datetime.date]) -> Formation:
        """
        # Only keep days in date range
        Returns a copy of self with days filtered.
        """
        return Formation(
            raw=self.raw,
            name=self.name,
            days=self.retain_days(rng)
        )
    
    #################
    # PREVIOUS WEEK #
    #################
    
    def prev_week_indexed(
        self,
        current: Range[datetime.date]
    ) -> tuple[Optional[Range[datetime.date]], list[tuple[int, Day]]]:
        retained_for_current = self.retain_days_indexed(current)
        if len(retained_for_current) < 1: return (None, [])
        current_week_first_day_idx = retained_for_current[0][0]
        prev_week_last_day_idx = current_week_first_day_idx - 1
        if prev_week_last_day_idx < 0: return (None, [])
        
        last_prev = self.days[prev_week_last_day_idx]
        new_week_rng = week.from_day(last_prev.date)
        
        return (new_week_rng, self.retain_days_indexed(new_week_rng))
    
    def prev_week(
        self,
        current: Range[datetime.date]
    ) -> tuple[Optional[Range[datetime.date]], list[Day]]:
        date_range, days = self.prev_week_indexed(current)
        days_no_idx = [day for day in map(
            lambda day: day[1], days
        )]
        return (date_range, days_no_idx)
    
    def prev_week_new_rng(
        self,
        current: Range[datetime.date]
    ) -> tuple[Optional[Range[datetime.date]], Formation]:
        rng, days = self.prev_week(current)
        form = Formation(
            raw=self.raw,
            name=self.name,
            days=days
        )
        return (rng, form)
    
    def prev_week_new(self, current: Range[datetime.date]) -> Formation:
        return self.prev_week_new_rng(current)[1]
    
    #############
    # NEXT WEEK #
    #############
    
    def next_week_indexed(
        self,
        current: Range[datetime.date]
    ) -> tuple[Optional[Range[datetime.date]], list[tuple[int, Day]]]:
        retained_for_current = self.retain_days_indexed(current)
        if len(retained_for_current) < 1: return (None, [])
        current_week_last_day_idx = retained_for_current[-1][0]
        next_week_first_day_idx = current_week_last_day_idx + 1
        if next_week_first_day_idx > len(self.days) - 1: return (None, [])
            
        next_first = self.days[next_week_first_day_idx]
        new_week_rng = week.from_day(next_first.date)
        
        return (new_week_rng, self.retain_days_indexed(new_week_rng))
    
    
    def next_week(
        self,
        current: Range[datetime.date]
    ) -> tuple[Optional[Range[datetime.date]], list[Day]]:
        date_range, days = self.next_week_indexed(current)
        days_no_idx = [day for day in map(
            lambda day: day[1], days
        )]
        return (date_range, days_no_idx)
    
    def next_week_new_rng(
        self,
        current: Range[datetime.date]
    ) -> tuple[Optional[Range[datetime.date]], Formation]:
        rng, days = self.next_week(current)
        form = Formation(
            raw=self.raw,
            name=self.name,
            days=days
        )
        return (rng, form)
    
    def next_week_new(self, current: Range[datetime.date]) -> Formation:
        return self.next_week_new_rng(current)[1]
    
    ##############
    # FIRST WEEK #
    ##############
    
    def first_week_indexed(
        self
    ) -> tuple[Optional[Range[datetime.date]], list[tuple[int, Day]]]:
        if len(self.days) < 0: return (None, [])
        first_day = self.days[0]
        first_week = week.from_day(first_day.date)
        return (first_week, self.retain_days_indexed(first_week))
    
    def first_week(
        self
    ) -> tuple[Optional[Range[datetime.date]], list[Day]]:
        date_range, days = self.first_week_indexed()
        days_no_idx = [day for day in map(
            lambda day: day[1], days
        )]
        return (date_range, days_no_idx)
    
    def first_week_new_rng(
        self
    ) -> tuple[Optional[Range[datetime.date]], Formation]:
        rng, days = self.first_week()
        form = Formation(
            raw=self.raw,
            name=self.name,
            days=days
        )
        return (rng, form)
    
    def first_week_new(self) -> Formation:
        return self.first_week_new_rng()[1]
    
    #############
    # LAST WEEK #
    #############

    def last_week_indexed(
        self
    ) -> tuple[Optional[Range[datetime.date]], list[tuple[int, Day]]]:
        if len(self.days) < 0: return (None, [])
        last_day = self.days[-1]
        last_week = week.from_day(last_day.date)
        return (last_week, self.retain_days_indexed(last_week))
    
    def last_week(
        self
    ) -> tuple[Optional[Range[datetime.date]], list[Day]]:
        date_range, days = self.last_week_indexed()
        days_no_idx = [day for day in map(
            lambda day: day[1], days
        )]
        return (date_range, days_no_idx)
    
    def last_week_new_rng(
        self
    ) -> tuple[Optional[Range[datetime.date]], Formation]:
        rng, days = self.last_week()
        form = Formation(
            raw=self.raw,
            name=self.name,
            days=days
        )
        return (rng, form)
    
    def last_week_new(self) -> Formation:
        return self.last_week_new_rng()[1]

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
