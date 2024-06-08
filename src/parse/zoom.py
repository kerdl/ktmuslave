from __future__ import annotations
from typing import Optional, Literal, Union, Callable, TYPE_CHECKING
from dataclasses import dataclass
from urllib import parse
import re

from src import data
from src.data import zoom
from .pattern import (
    SPACE_NEWLINE,
    NAME,
    SHORT_NAME,
    ZOOM_ID,
    ZOOM_PWD,
    NON_LETTER_NO_SPACE,
    DIGIT,
    LETTER
)

if TYPE_CHECKING:
    from src.data.settings import MODE_LITERAL

KEY_LITERAL = Literal["имя", "ссылка", "ид", "код", "пароль", "ключ", "заметки"]
GROUP_KEY_LITERAL = Literal["имя", "ссылка", "ид", "код", "пароль", "заметки"]
TCHR_KEY_LITERAL = Literal["имя", "ссылка", "ид", "код", "пароль", "ключ", "заметки"]


class Key:
    NAME = "имя"
    URL = "ссылка"
    ID = "ид"
    PWD = ["код", "пароль"]
    HOST_KEY = "ключ"
    NOTES = "заметки"

    @staticmethod
    def with_semicolon(key: KEY_LITERAL) -> str:
        return f"{key}:"

    @classmethod
    def _is_relevant(cls, key: Union[KEY_LITERAL, list[KEY_LITERAL]], line: str) -> bool:
        if isinstance(key, str):
            return line.lower().startswith(cls.with_semicolon(key))
        if isinstance(key, list):
            return any([line.lower().startswith(key_var) for key_var in key])

    @classmethod
    def group_is_relevant(cls, key: Union[GROUP_KEY_LITERAL, list[GROUP_KEY_LITERAL]], line: str) -> bool:
        if cls.HOST_KEY in key: return False
        return cls._is_relevant(key, line)

    @classmethod
    def tchr_is_relevant(cls, key: Union[TCHR_KEY_LITERAL, list[TCHR_KEY_LITERAL]], line: str) -> bool:
        return cls._is_relevant(key, line)
    
    @classmethod
    def _find(
        cls,
        line: str,
        relevance_fn: Callable[[Union[KEY_LITERAL, list[KEY_LITERAL]], str], bool],
        ignored: list[str] = [],
    ) -> Optional[KEY_LITERAL]:
        for (_, key) in cls.__dict__.items():
            key_vars = [key]
            if isinstance(key, list):
                key_vars = key
            
            key_vars = filter(lambda key: key not in ignored, key_vars)

            for key_var in key_vars:
                if relevance_fn(key_var, line):
                    return key
        
        return None
    
    @classmethod
    def group_find(cls, line: str) -> Optional[GROUP_KEY_LITERAL]:
        return cls._find(line, cls.group_is_relevant, ignored=[cls.HOST_KEY])

    @classmethod
    def tchr_find(cls, line: str) -> Optional[TCHR_KEY_LITERAL]:
        return cls._find(line, cls.tchr_is_relevant, ignored=[])

    @staticmethod
    def _remove(
        key: Union[KEY_LITERAL, list[KEY_LITERAL]],
        line: str,
        relevance_fn: Callable[[Union[KEY_LITERAL, list[KEY_LITERAL]], str], bool]
    ) -> str:
        def remove_str(key: KEY_LITERAL, line: str):
            return re.sub(Key.with_semicolon(key), "", line, flags=re.IGNORECASE).strip()
        
        if isinstance(key, str):
            return remove_str(key, line)
        if isinstance(key, list):
            for key_var in key:
                if relevance_fn(key_var, line):
                    return remove_str(key_var, line)
    
    @staticmethod
    def group_remove(key: Union[GROUP_KEY_LITERAL, list[GROUP_KEY_LITERAL]], line: str) -> str:
        return Key._remove(key, line, Key.group_is_relevant)

    @staticmethod
    def tchr_remove(key: Union[TCHR_KEY_LITERAL, list[TCHR_KEY_LITERAL]], line: str) -> str:
        return Key._remove(key, line, Key.tchr_is_relevant)


@dataclass
class Parser:
    text: str

    def remove_newline_spaces(self, text: str) -> str:
        return SPACE_NEWLINE.sub("\n\n", text)

    def split_sections(self, text: str) -> list[str]:
        newline_split = text.split("\n")
        sections: list[str] = []
        
        first_name_occurrence_found = False
        prev_key: Optional[KEY_LITERAL] = None

        current_section_rows = []

        for (index, line) in enumerate(newline_split):
            is_last = (index + 1) == len(newline_split)

            this_line_key = Key.group_find(line)

            if this_line_key == Key.NAME and first_name_occurrence_found is False:
                first_name_occurrence_found = True
            elif this_line_key == Key.NAME:
                sections.append("\n".join(current_section_rows))
                current_section_rows = []

            if this_line_key is not None or prev_key == Key.NOTES:
                current_section_rows.append(line)
            
            if is_last:
                sections.append("\n".join(current_section_rows))

            if this_line_key is not None:
                prev_key = this_line_key

        return sections
    
    def parse_name(self, line: str) -> Optional[str]:
        def search_full_name(line: str) -> list[str]:
            """ ## `Ебанько Хуйло Йоба` """
            return NAME.findall(line)

        def search_short_name(line: str) -> Optional[re.Match[str]]:
            """ ## `Ебанько Х.` or `Ебанько Х.Й.` """
            return SHORT_NAME.search(line)

        # try to find short name first
        short_name: Optional[re.Match[str]] = search_short_name(line)

        if short_name is not None:
            return short_name.group()

        full_name: list[str] = search_full_name(line)

        if len(full_name) <= 3 and len(full_name) > 0:
            first_name: str = None
            initials_parts: list[str] = []

            for name_section in full_name:
                # keep first name complete
                if first_name is None:
                    first_name = name_section
                    continue
                    
                # then shorten anything else
                initial = name_section[0] + "."
                initials_parts.append(initial)

            initials = "".join(initials_parts)

            name = f"{first_name} {initials}"

            return name.rstrip().lstrip()
    
    def parse_id(self, line: str) -> Optional[str]:
        no_spaces = line.replace(" ", "")
        id = ZOOM_ID.search(no_spaces)

        if id is not None:
            return id.group()
        
        return None

    def parse_section(
        self,
        text: str,
        mode: "MODE_LITERAL",
        find_fn: Callable[[str], Optional[KEY_LITERAL]],
        relevance_fn: Callable[[Union[KEY_LITERAL, list[KEY_LITERAL]], str], bool],
        remove_fn: Callable[[Union[KEY_LITERAL, list[KEY_LITERAL]], str], str],
    ) -> Optional[zoom.Data]:
        name: data.Field[Optional[str]] = data.Field(value=None)
        url: data.Field[Optional[str]] = data.Field(value=None)
        id: data.Field[Optional[str]] = data.Field(value=None)
        pwd: data.Field[Optional[str]] = data.Field(value=None)
        host_key: data.Field[Optional[str]] = data.Field(value=None)
        notes: data.Field[Optional[str]] = data.Field(value=None)

        lines: list[str] = text.split("\n")

        prev_key: Optional[KEY_LITERAL] = None

        for line in lines:
            line = line.strip()

            if line == "":
                continue

            this_line_key = find_fn(line)

            # if that is a name key
            if relevance_fn(Key.NAME, line):
                name.value = remove_fn(Key.NAME, line)
                    
            # if that is a url key
            elif relevance_fn(Key.URL, line): 
                url.value = remove_fn(Key.URL, line)

            # if that is an id key
            elif relevance_fn(Key.ID, line):
                id.value = remove_fn(Key.ID, line)

            # if that is a pwd key
            elif relevance_fn(Key.PWD, line):
                pwd.value = remove_fn(Key.PWD, line)
            
            # if that is a host key key
            elif relevance_fn(Key.HOST_KEY, line):
                host_key.value = remove_fn(Key, Key.HOST_KEY, line)

            # if that is a notes key
            elif relevance_fn(Key.NOTES, line):
                if notes.value is None:
                    notes.value = ""

                without_key = remove_fn(Key.NOTES, line)

                if without_key != "":
                    notes.value += without_key
                    notes.value += "\n"

            elif prev_key == Key.NOTES:
                notes.value += line
                notes.value += "\n"

            if this_line_key is not None:
                prev_key = this_line_key

        if name.value is None:
            return None
        
        if len(name.value) > zoom.NAME_LIMIT:
            return None
        
        for field in [url, id, pwd, host_key, notes]:
            if field.value is None:
                continue

            if len(field.value) > zoom.VALUE_LIMIT:
                field.value = None
        
        if url.value is not None and id.value is None:
            matched = ZOOM_ID.search(url.value)

            if matched is not None:
                id.value = matched.group()

        if notes.value is not None:
            notes.value = ", ".join([section for section in notes.value.split("\n") if section != ""])

        model = zoom.Data(
            name=name,
            url=url,
            id=id,
            pwd=pwd,
            host_key=host_key,
            notes=notes
        )

        model.check(mode)

        return model
    
    def group_parse(self) -> list[zoom.Data]:
        from src.data.settings import Mode

        self.no_newline_spaces = self.remove_newline_spaces(self.text)
        self.sections = self.split_sections(self.no_newline_spaces)
        self.models: list[zoom.Data] = []

        for section in self.sections:
            parsed = self.parse_section(
                section,
                Mode.GROUP,
                Key.group_find,
                Key.group_is_relevant,
                Key.group_remove
            )

            if parsed is not None:
                self.models.append(parsed)
        
        return self.models

    def teacher_parse(self) -> list[zoom.Data]:
        from src.data.settings import Mode
        
        self.sections = self.split_sections(self.text)
        self.models: list[zoom.Data] = []

        for section in self.sections:
            parsed = self.parse_section(
                section,
                Mode.TEACHER,
                Key.tchr_find,
                Key.tchr_is_relevant,
                Key.tchr_remove
            )

            if parsed is not None:
                self.models.append(parsed)
        
        return self.models
    