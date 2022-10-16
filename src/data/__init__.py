from __future__ import annotations
from typing import ClassVar, Iterable, TypeVar, Generic
from dataclasses import dataclass, field

from src.svc import common


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
        if display_value:
            base_formatted = VALUE_FIELD_FMT.format(
                emoji = emoji, 
                name  = name, 
                value = self.value if self.value is not None else "нет",
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
URL_MAY_BE_CUTTED = Warning(
    "url_may_be_cutted",
    "🔴 возможно обрезана: на конце есть \"...\""
)