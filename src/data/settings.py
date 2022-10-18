from __future__ import annotations
from typing import Optional, Any
from dataclasses import dataclass

from src.data import zoom
from src.svc.common.states import State, Values
from src.svc.common.states.tree import Init, Settings as SettingsState


@dataclass
class Group:
    typed: Optional[str] = None
    valid: Optional[str] = None
    confirmed: Optional[str] = None

@dataclass
class Settings(Values):
    group: Group
    zoom: zoom.Container
    updates: Optional[bool] = None
    should_pin: Optional[bool] = None

    @classmethod
    def default(cls: type[Settings]):
        return cls(
            group = Group(),
            zoom  = zoom.Container.default(),
        )

    def get_from_state(self, state: State) -> Any:
        VALUES = {
            SettingsState.I_GROUP:       self.group.confirmed,
            SettingsState.I_UPDATES:     self.updates,
            SettingsState.II_SHOULD_PIN: self.should_pin,
            SettingsState.I_ZOOM:        len(self.zoom.entries) if self.zoom.is_finished else None
        }

        return VALUES.get(state)