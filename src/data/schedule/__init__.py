from __future__ import annotations
import datetime
from typing import Literal, Optional
from pydantic import BaseModel
from src.parse import pattern
from src.data import RepredBaseModel
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
    
    def do_versions_match_complex(self) -> bool:
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
    
    def retain_days(self, rng: Range[datetime.date]) -> Formation:
        """
        # Only keep days in date range
        """
        kept_days = []
        
        for day in self.days:
            if day.date in rng:
                kept_days.append(day)
                
        return Formation(
            raw=self.raw,
            name=self.name,
            days=kept_days
        )

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
