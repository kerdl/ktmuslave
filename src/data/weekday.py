from typing import Literal


class Weekday:
    MONDAY    = "Понедельник"
    TUESDAY   = "Вторник"
    WEDNESDAY = "Среда"
    THURSDAY  = "Четверг"
    FRIDAY    = "Пятница"
    SATURDAY  = "Суббота"
    SUNDAY    = "Воскресенье"

WEEKDAY_LITERAL = Literal[
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье"
]
