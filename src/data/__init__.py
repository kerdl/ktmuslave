from __future__ import annotations

if __name__ == "__main__":
    import sys
    sys.path.append(".")

from dataclasses import dataclass
from typing import Optional, Any

from src.svc.common.states import State, Values
from src.svc.common.states.tree import Init
from src.data import error


@dataclass
class ZoomData:
    name: str
    url: Optional[str]
    id: Optional[str]
    pwd: Optional[str]

    @classmethod
    def parse(cls: type[ZoomData], text: str) -> Optional[list[ZoomData]]:
        from src.data import zoom
        return zoom.Parser(text).parse()

    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        return self.name == other


@dataclass
class ZoomContainer:
    entries: set[ZoomData]
    """ ## Main database of zoom, takes links for schedule here """
    new_entries: set[ZoomData]
    """ ## Temp storage for unconfirmed new entries """
    overwrite_entries: set[ZoomData]
    """ ## Temp storage for unconfirmed entries, that should be overwritten"""


    @staticmethod
    def add(data: ZoomData, destination: set[ZoomData]) -> None:
        if data in destination:
            raise error.ZoomNameInDatabase(
                "this entry already in databased"
            )

        destination.add(data)
    
    def add_entry(self, data: ZoomData):
        return self.add(data, self.entries)
    
    def add_new_entry(self, data: ZoomData):
        return self.add(data, self.new_entries)
    
    def add_overwrite_entry(self, data: ZoomData):
        return self.add(data, self.overwrite_entries)


    @staticmethod
    def remove(name: str, destination: set[ZoomData]) -> bool:
        dummy = ZoomData(name, "", "", "")
        return destination.remove(dummy)
    
    def remove_entry(self, name: str):
        return self.remove(name, self.entries)

    def remove_new_entry(self, name: str):
        return self.remove(name, self.new_entries)

    def remove_overwrite_entry(self, name: str):
        return self.remove(name, self.overwrite_entries)


    @staticmethod
    def get(name: str, destination: set[ZoomData]) -> Optional[ZoomData]:
        for entry in destination:
            if entry.name == name:
                return entry

        return None
    
    def get_entry(self, data: ZoomData):
        return self.get(data, self.entries)

    def get_new_entry(self, data: ZoomData):
        return self.get(data, self.new_entries)

    def get_overwrite_entry(self, data: ZoomData):
        return self.get(data, self.overwrite_entries)
    

    def __len__(self):
        return len(self.entries)

@dataclass
class Group:
    typed: Optional[str] = None
    valid: Optional[str] = None
    confirmed: Optional[str] = None

@dataclass
class Settings(Values):
    group: Group
    schedule_broadcast: Optional[bool] = None
    should_pin: Optional[bool] = None
    zoom_entries: Optional[ZoomContainer] = None

    def get_from_state(self, state: State) -> Any:
        VALUES = {
            Init.I_GROUP:              self.group.confirmed,
            Init.I_SCHEDULE_BROADCAST: self.schedule_broadcast,
            Init.II_SHOULD_PIN:        self.should_pin,
            Init.I_ZOOM:               len(self.zoom_entries) if self.zoom_entries is not None else None
        }

        return VALUES.get(state)

if __name__ == "__main__":
    text = """"""
    parsed = ZoomData.parse(text)
    print(parsed)