from __future__ import annotations

if __name__ == "__main__":
    import sys
    sys.path.append(".")

from typing import Optional, Union
from dataclasses import dataclass

from src.svc import common
from src.data import error


COMPLETE   = "🔹"
INCOMPLETE = "🔸"
URL        = "🌐"
ID         = "📍"
PWD        = "🔑"
NONE       = "❓"


FIELDS_EMOJIS = {
    "url": URL,
    "id":  ID,
    "pwd": PWD
}
FIELDS_TRANSLATIONS = {
    "url": "Ссылка",
    "id":  "ID",
    "pwd": "Пароль"
}

NAME = (
    "{emoji} | {name}"
)
def format_name(emoji: str, name: str):
    return NAME.format(emoji=emoji, name=name)

FIELD = (
    "{emoji} {name}: {value}"
)
def format_field(emoji: str, name: str, value: str):
    return FIELD.format(emoji=emoji, name=name, value=value)

SECTION = (
    "{name}\n"
    "{fields}"
)
def format_section(name: str, fields: list[str]):
    indented_fields = []
    merged_fields = ""

    for field in fields:
        indented_fields.append(f"   ╰ {field}")
    
    merged_fields = "\n".join(indented_fields)

    return SECTION.format(
        name = name,
        fields = merged_fields
    )

NO = "нет"


@dataclass
class Data:
    name: str
    url: Optional[str]
    id: Optional[str]
    pwd: Optional[str]

    @classmethod
    def parse(cls: type[Data], text: str) -> list[Data]:
        from src.parse import zoom
        return zoom.Parser(text).parse()
    
    def format(self) -> str:
        name = self.name
        fmt_name = ""

        fields = [field for field in self.__dict__.items() if field[0] != "name"]
        fmt_fields = []

        completeness = COMPLETE

        if not all([field[1] for field in fields]):
            completeness = INCOMPLETE
        
        fmt_name = format_name(completeness, name)

        for field in fields:
            field_name = field[0]
            field_value = field[1]

            if field_value is not None:
                emoji = FIELDS_EMOJIS.get(field_name)
            else:
                emoji = NONE
            
            translation = FIELDS_TRANSLATIONS.get(field_name)
            
            line = format_field(emoji, translation, field_value or NO)
            
            fmt_fields.append(line)

        return format_section(fmt_name, fmt_fields)

    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        return self.name == other

@dataclass
class Entries:
    set: set[Data]
    pages: list[common.CommonBotTemplate]
    cur_page: int

    @classmethod
    def default(cls: type[Entries]):
        return cls(set(), [], 0)

@dataclass
class Container:
    entries: Entries
    """ ## Main database of zoom, takes links for schedule here """
    new_entries: Entries
    """ ## Temp storage for unconfirmed new entries """
    overwrite_entries: Entries
    """ ## Temp storage for unconfirmed entries, that should be overwritten"""

    @classmethod
    def default(cls: type[Container]):
        return cls(
            Entries.default(), 
            Entries.default(), 
            Entries.default()
        )

    @staticmethod
    def add(data: Union[Data, set[Data]], destination: Entries) -> None:
        if isinstance(data, set):
            for data_obj in data:
                destination.set.add(data_obj)
    
            return None
        
        if isinstance(data, Data):
            destination.set.add(data)

            return None
    
    def add_entry(self, data: Union[Data, set[Data]]):
        return self.add(data, self.entries)
    
    def add_new_entry(self, data: Union[Data, set[Data]]):
        return self.add(data, self.new_entries)
    
    def add_overwrite_entry(self, data: Union[Data, set[Data]]):
        return self.add(data, self.overwrite_entries)


    @staticmethod
    def remove(name: Union[str, set[str]], destination: Entries) -> Union[bool, list[bool]]:
        if isinstance(name, set):
            results = []

            for n in name:
                dummy = Data(n, "", "", "")
                result = destination.set.remove(dummy)

                results.append(result)
            
            return results

        if isinstance(name, str):
            dummy = Data(name, "", "", "")
            return destination.set.remove(dummy)
    
    def remove_entry(self, name: str):
        return self.remove(name, self.entries)

    def remove_new_entry(self, name: str):
        return self.remove(name, self.new_entries)

    def remove_overwrite_entry(self, name: str):
        return self.remove(name, self.overwrite_entries)


    @staticmethod
    def get(name: str, destination: Entries) -> Optional[Data]:
        for entry in destination.set:
            if entry.name == name:
                return entry

        return None
    
    def get_entry(self, name: str):
        return self.get(name, self.entries)

    def get_new_entry(self, name: str):
        return self.get(name, self.new_entries)

    def get_overwrite_entry(self, name: str):
        return self.get(name, self.overwrite_entries)
    

    @staticmethod
    def format(self, destination: Entries):
        ...
    

    def __len__(self):
        return len(self.entries.set)

