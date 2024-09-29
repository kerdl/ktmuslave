from typing import Literal, Optional


WEEKDAY_LITERAL = Literal[
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье"
]

class Weekday:
    MONDAY = "Понедельник"
    TUESDAY = "Вторник"
    WEDNESDAY = "Среда"
    THURSDAY = "Четверг"
    FRIDAY = "Пятница"
    SATURDAY = "Суббота"
    SUNDAY = "Воскресенье"
    
    @classmethod
    def from_index(cls, idx: int) -> Optional[WEEKDAY_LITERAL]:
        if idx == 0:
            return cls.MONDAY
        if idx == 1:
            return cls.TUESDAY
        if idx == 2:
            return cls.WEDNESDAY
        if idx == 3:
            return cls.THURSDAY
        if idx == 4:
            return cls.FRIDAY
        if idx == 5:
            return cls.SATURDAY
        if idx == 6:
            return cls.SUNDAY

WEEKDAYS = [
    Weekday.MONDAY,
    Weekday.TUESDAY,
    Weekday.WEDNESDAY,
    Weekday.THURSDAY,
    Weekday.FRIDAY,
    Weekday.SATURDAY,
    Weekday.SUNDAY
]

