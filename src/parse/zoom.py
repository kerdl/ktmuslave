from __future__ import annotations
from typing import Optional, Literal
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


KEY_LITERAL = Literal["имя", "ссылка", "ид", "код", "заметки"]


class Key:
    NAME  = "имя"
    URL   = "ссылка"
    ID    = "ид"
    PWD   = "код"
    NOTES = "заметки"

    @staticmethod
    def with_semicolon(key: KEY_LITERAL) -> str:
        return f"{key}:"

    @classmethod
    def is_relevant(cls, key: KEY_LITERAL, line: str) -> bool:
        return line.lower().startswith(cls.with_semicolon(key))
    
    @classmethod
    def find(cls, line: str) -> Optional[KEY_LITERAL]:
        for (_, key) in cls.__dict__.items():
            if cls.is_relevant(key, line):
                return key
        
        return None

    @staticmethod
    def remove(key: KEY_LITERAL, line: str) -> str:
        return re.sub(Key.with_semicolon(key), "", line, flags=re.IGNORECASE).strip()


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

            this_line_key = Key.find(line)

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

    def parse_section(self, text: str) -> Optional[zoom.Data]:
        name:  data.Field[Optional[str]] = data.Field(None)
        url:   data.Field[Optional[str]] = data.Field(None)
        id:    data.Field[Optional[str]] = data.Field(None)
        pwd:   data.Field[Optional[str]] = data.Field(None)
        notes: data.Field[Optional[str]] = data.Field(None)

        lines: list[str] = text.split("\n")

        prev_key: Optional[KEY_LITERAL] = None

        for line in lines:
            line = line.strip()

            if line == "":
                continue

            this_line_key = Key.find(line)

            # if that is a name key
            if Key.is_relevant(Key.NAME, line):
                name.value = Key.remove(Key.NAME, line)
                    
            # if that is a url key
            elif Key.is_relevant(Key.URL, line): 
                url.value = Key.remove(Key.URL, line)

            # if that is an id key
            elif Key.is_relevant(Key.ID, line):
                id.value = Key.remove(Key.ID, line)

            # if that is a pwd key
            elif Key.is_relevant(Key.PWD, line):
                pwd.value = Key.remove(Key.PWD, line)
            
            # if that is a notes key
            elif Key.is_relevant(Key.NOTES, line):
                if notes.value is None:
                    notes.value = ""

                without_key = Key.remove(Key.NOTES, line)

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
        
        if url.value is not None and id.value is None:
            matched = ZOOM_ID.search(url.value)

            if matched is not None:
                id.value = matched.group()

        if notes.value is not None:
            notes.value = ", ".join([section for section in notes.value.split("\n") if section != ""])

        model = zoom.Data(
            name  = name,
            url   = url,
            id    = id,
            pwd   = pwd,
            notes = notes
        )

        model.check()

        return model
    
    def parse(self) -> list[zoom.Data]:
        self.no_newline_spaces = self.remove_newline_spaces(self.text)
        self.sections = self.split_sections(self.no_newline_spaces)
        self.models: list[zoom.Data] = []

        for section in self.sections:
            parsed = self.parse_section(section)

            if parsed is not None:
                self.models.append(parsed)
        
        return self.models