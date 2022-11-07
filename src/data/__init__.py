from __future__ import annotations
from typing import ClassVar, Iterable, TypeVar, Generic
from dataclasses import dataclass, field


T = TypeVar("T")


FIELD_FMT = (
    "{emoji} | {name}"
)
VALUE_FIELD_FMT = (
    "{emoji} | {name}: {value}"
)


class Translated:
    __translation__: ClassVar[dict[str, str]]

class Emojized:
    __emojis__: ClassVar[dict[str, str]]

class Repred:
    def __repr_name__(self) -> str: ...


class Emoji:
    COMPLETE   = "🔹"
    INCOMPLETE = "🔸"
    NONE       = "❓"
    WARN       = "❗"

@dataclass
class Warning:
    anchor: str
    text: str

    @staticmethod
    def format_multiple(warns: Iterable[Warning]) -> str:
        text_warns: list[str] = []

        for warn in warns:
            text_warns.append(warn.text)
        
        return "(" + ", ".join(text_warns) + ")"

    def __hash__(self) -> int:
        return hash(self.anchor)
    
    def __eq__(self, other: object) -> bool:
        return self.anchor == other

@dataclass
class Field(Generic[T], Repred):
    value: T

    warnings: set[Warning] = field(default_factory=set)
    """
    # Warns if `value` is unusual
    """

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def format(self, emoji: str, name: str, display_value: bool = True) -> str:
        from src.svc import common

        if display_value:
            base_formatted = VALUE_FIELD_FMT.format(
                emoji = emoji, 
                name  = name, 
                value = common.messages.value_repr(self.value),
            )
        else:
            base_formatted = FIELD_FMT.format(
                emoji = emoji, 
                name  = name, 
            )

        if not self.has_warnings:
            return base_formatted
        
        warns_text = Warning.format_multiple(self.warnings)
        #warns_text = common.text.indent(warns_text, add_dropdown = True)

        #return f"{base_formatted}\n{warns_text}"
        return f"{base_formatted} {warns_text}"

    def __repr_name__(self) -> str:
        return self.value

    def __hash__(self):
        return hash(self.value)
    
    def __eq__(self, other: object) -> bool:
        return self.value == other

INCORRECT_NAME_FORMAT = Warning(
    "incorrect_name_format", 
    "🔴 не соответствует формату: Ебанько Х.Й. или Ебанько Х."
)
NO_DOT_AT_THE_END = Warning(
    "no_dot_at_the_end", 
    "🔴 нет точки на конце"
)
URL_MAY_BE_CUTTED = Warning(
    "url_may_be_cutted",
    "🔴 возможно обрезана: на конце есть многоточие"
)
NOT_AN_URL = Warning(
    "not_an_url",
    "🔴 не является ссылкой"
)

INCORRECT_ID_FORMAT = Warning(
    "incorrect_id_format",
    "🔴 не соответствует формату: от 10 цифр"
)

HAS_LETTERS = Warning(
    "has_letters",
    "🔴 есть буквы, хотя не должны быть"
)
HAS_PUNCTUATION = Warning(
    "has_punctuation",
    "🔴 есть знаки препинания, хотя не должны быть"
)
HAS_SPACE = Warning(
    "has_space",
    "🔴 есть пробелы, хотя не должны быть"
)