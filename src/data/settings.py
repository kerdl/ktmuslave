from __future__ import annotations
from typing import Optional, Any
from dataclasses import dataclass

from src.data import zoom
from src.svc import common
from src.svc.common.states import State, Values
from src.svc.common.states.tree import INIT, SETTINGS as SettingsTree


@dataclass
class Group:
    typed: Optional[str] = None
    valid: Optional[str] = None
    confirmed: Optional[str] = None

@dataclass
class Settings(Values):
    group: Group
    zoom: zoom.Container
    broadcast: Optional[bool] = None
    should_pin: Optional[bool] = None

    @classmethod
    def default(cls: type[Settings]):
        return cls(
            group = Group(),
            zoom  = zoom.Container.default(),
        )

    def get_from_state(self, state: State) -> Any:
        VALUES = {
            SettingsTree.II_GROUP:       self.group.confirmed,
            SettingsTree.II_BROADCAST:   self.broadcast,
            SettingsTree.III_SHOULD_PIN: self.should_pin,
            SettingsTree.II_ZOOM:        len(self.zoom.entries) if self.zoom.is_finished else None
        }

        return VALUES.get(state)
    
    def defaults_from_everything(self, everything: common.CommonEverything):
        if SettingsTree.III_SHOULD_PIN in everything.navigator.ignored:
            self.should_pin = False