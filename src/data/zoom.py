from __future__ import annotations

if __name__ == "__main__":
    import sys
    sys.path.append(".")

from typing import Optional
from dataclasses import dataclass

from src.data import error


@dataclass
class Data:
    name: str
    url: Optional[str]
    id: Optional[str]
    pwd: Optional[str]

    @classmethod
    def parse(cls: type[Data], text: str) -> Optional[list[Data]]:
        from src.parse import zoom
        return zoom.Parser(text).parse()

    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        return self.name == other

@dataclass
class Container:
    entries: set[Data]
    """ ## Main database of zoom, takes links for schedule here """
    new_entries: set[Data]
    """ ## Temp storage for unconfirmed new entries """
    overwrite_entries: set[Data]
    """ ## Temp storage for unconfirmed entries, that should be overwritten"""


    @staticmethod
    def add(data: Data, destination: set[Data]) -> None:
        if data in destination:
            raise error.ZoomNameInDatabase(
                "this entry already in databased"
            )

        destination.add(data)
    
    def add_entry(self, data: Data):
        return self.add(data, self.entries)
    
    def add_new_entry(self, data: Data):
        return self.add(data, self.new_entries)
    
    def add_overwrite_entry(self, data: Data):
        return self.add(data, self.overwrite_entries)


    @staticmethod
    def remove(name: str, destination: set[Data]) -> bool:
        dummy = Data(name, "", "", "")
        return destination.remove(dummy)
    
    def remove_entry(self, name: str):
        return self.remove(name, self.entries)

    def remove_new_entry(self, name: str):
        return self.remove(name, self.new_entries)

    def remove_overwrite_entry(self, name: str):
        return self.remove(name, self.overwrite_entries)


    @staticmethod
    def get(name: str, destination: set[Data]) -> Optional[Data]:
        for entry in destination:
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
    def format(self, destination: set[Data]):
        ...
    

    def __len__(self):
        return len(self.entries)

