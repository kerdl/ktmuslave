from typing import Optional
from re import Match
from dataclasses import dataclass
from urllib import parse

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


@dataclass
class Parser:
    text: str

    def remove_newline_spaces(self, text: str) -> str:
        return SPACE_NEWLINE.sub("\n\n", text)

    def split_sections(self, text: str) -> list[str]: 
        return text.split("\n\n")
    
    def parse_name(self, line: str) -> Optional[str]:
        def search_full_name(line: str) -> list[str]:
            """ ## `Ебанько Хуйло Йоба` """
            return NAME.findall(line)

        def search_short_name(line: str) -> Optional[Match[str]]:
            """ ## `Ебанько Х.` or `Ебанько Х.Й.` """
            return SHORT_NAME.search(line)

        # try to find short name first
        short_name: Optional[Match[str]] = search_short_name(line)

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
    
    def parse_pwd(self, line: str) -> Optional[str]:        
        non_word_line = NON_LETTER_NO_SPACE.sub("", line)

        pwd = ZOOM_PWD.search(non_word_line)

        if pwd is not None:
            # if no digits in pwd
            if not DIGIT.search(pwd.group()):
                return None
            
            # if no letters in pwd
            if not LETTER.search(pwd.group()):
                return None
            
            return pwd.group()
        
        return None

    def parse_section(self, text: str) -> Optional[zoom.Data]:
        name: data.Field[Optional[str]] = data.Field(None)
        url:  data.Field[Optional[str]] = data.Field(None)
        id:   data.Field[Optional[str]] = data.Field(None)
        pwd:  data.Field[Optional[str]] = data.Field(None)

        lines: list[str] = text.split("\n")

        for line in lines:
            line = line.rstrip().lstrip()

            if line == "":
                continue

            # if name is not found yet
            if name.value is None:
                parsed = self.parse_name(line)

                if parsed is not None:
                    name.value = parsed
                    continue
                    
            # if url is not found yet
            if url.value is None:   
                parsed = parse.urlparse(line)

                if "zoom" in parsed.netloc and "/j/" in parsed.path:
                    clean_url = line.lstrip().rstrip().replace("\n", "")
                    url.value = clean_url

                    if id.value is None:
                        id.value = self.parse_id(parsed.path)
                    
                    continue

            # if id is not found yet
            if id.value is None:
                id.value = self.parse_id(line)

                if id.value is not None:
                    continue

            # if pwd is not found yet
            if pwd.value is None:
                pwd.value = self.parse_pwd(line)

                if pwd.value is not None:
                    continue

        if name.value is None:
            return None

        model = zoom.Data(
            name = name,
            url  = url,
            id   = id,
            pwd  = pwd
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