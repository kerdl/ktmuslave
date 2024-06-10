from __future__ import annotations
from typing import ClassVar, Iterable, TypeVar, Generic, Optional, Generator, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field as PydField
from pydantic.generics import GenericModel

from . import format as fmt
from src.svc import telegram as tg


T = TypeVar("T")


FIELD_FMT = (
    "{emoji} | {name}"
)
VALUE_FIELD_FMT = (
    "{emoji} | {name}: {value}"
)

class Translated:
    __translation__: ClassVar[dict[str, str]]

class TranslatedBaseModel(BaseModel):
    __translation__: ClassVar[dict[str, str]]

    def translate(self, key: str) -> Optional[str]: 
        return self.__translation__.get(key)

    def __iter__(self) -> Generator[tuple[str, Any], None, None]:
        return super().__iter__()

class Emojized:
    __emojis__: ClassVar[dict[str, str]]

class Repred:
    def __repr_name__(self) -> str: ...

class RepredBaseModel(BaseModel):
    @property
    def repr_name(self) -> str: ...

class HiddenVars(BaseModel):
    def __init__(self, hidden_vars: bool = True, **data):
        super().__init__(**data)
        if hidden_vars:
            self.__dict__["__hidden_vars__"] = {}

    @property
    def __hidden_vars__(self) -> dict[str, Any]:
        return self.__dict__["__hidden_vars__"]

    def set_hidden_vars(self, value: dict[str, Any]):
        self.__dict__["__hidden_vars__"] = value

    def del_hidden_vars(self):
        del self.__dict__["__hidden_vars__"]
    
    def take_hidden_vars(self) -> dict[str, Any]:
        hidden_vars = self.__hidden_vars__
        self.del_hidden_vars()
        return hidden_vars



class Duration(BaseModel):
    secs: int
    nanos: int

    def __str__(self) -> str:
        """as minutes"""
        return str(int(self.secs / 60))


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

class Field(GenericModel, Generic[T], Repred):
    value: T
    warnings: list[Warning] = PydField(default_factory=list, exclude=True)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def format(
        self,
        emoji: str,
        name: str,
        display_value: bool = True,
        do_tg_markup: bool = False,
        escape_tg_markdown: bool = False
    ) -> str:
        from src.svc import common

        if display_value:
            value = fmt.value_repr(self.value)
            if escape_tg_markdown:
                value = tg.escape_html(value)
            if do_tg_markup:
                value = f"<code>{value}</code>"
            base_formatted = VALUE_FIELD_FMT.format(
                emoji = emoji, 
                name  = name, 
                value = value,
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