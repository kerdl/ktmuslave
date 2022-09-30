from typing import Optional, Any
from dataclasses import dataclass

from src.data import zoom
from src.svc.common.states import State, Values
from src.svc.common.states.tree import Init


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
    zoom_entries: Optional[zoom.Container] = None

    def get_from_state(self, state: State) -> Any:
        VALUES = {
            Init.I_GROUP:              self.group.confirmed,
            Init.I_SCHEDULE_BROADCAST: self.schedule_broadcast,
            Init.II_SHOULD_PIN:        self.should_pin,
            Init.I_ZOOM:               len(self.zoom_entries) if self.zoom_entries is not None else None
        }

        return VALUES.get(state)