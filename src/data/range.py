from __future__ import annotations
import datetime
from typing import Generic, TypeVar, get_args
from pydantic import BaseModel, field_validator
from src.data import format as fmt


T = TypeVar("T")


class Range(BaseModel, Generic[T]):
    start: T
    end: T

    def __str__(self) -> str:
        if (
            isinstance(self.start, datetime.time)
            and isinstance(self.end, datetime.time)
        ):
            start = f"{self.start.hour}:{fmt.zero_at_start(self.start.minute)}"
            end = f"{self.end.hour}:{fmt.zero_at_start(self.end.minute)}"
            
            if start == end:
                return start
            
            return f"{start} - {end}"

        return f"{self.start} - {self.end}"
    
    def __eq__(self, value: object) -> bool:
        if isinstance(value, Range):
            return self.start == value.start and self.end == value.end
        else:
            return False
