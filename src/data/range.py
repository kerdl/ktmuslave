from __future__ import annotations
import datetime
from typing import Generic, TypeVar, Any
from pydantic import BaseModel
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
    
    def __gt__(self, value: object) -> bool:
        if not isinstance(value, Range):
            raise TypeError(
                f"'>' not supported between instances of 'Range' and '{type(value)}'"
            )
        
        return self.start > value.start
    
    def __lt__(self, value: object) -> bool:
        if not isinstance(value, Range):
            raise TypeError(
                f"'<' not supported between instances of 'Range' and '{type(value)}'"
            )
        
        return self.start < value.start
    
    def __eq__(self, value: object) -> bool:
        if isinstance(value, Range):
            return self.start == value.start and self.end == value.end
        else:
            return False
        
    def __contains__(self, item: Any) -> bool:
        if (
            isinstance(self.start, datetime.date) and
            isinstance(self.end, datetime.date) and
            isinstance(item, datetime.date)
        ): 
            rng = range(self.start.toordinal(), self.end.toordinal())
            return item.toordinal() in rng
        else:
            rng = range(self.start, self.end)
            return item in rng
