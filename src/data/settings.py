from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, Field as PydField

from src.data import zoom
from src.svc import common
from src.parse import pattern
from src.svc.common.states import State, Values
from src.svc.common.states.tree import INIT, SETTINGS as SettingsTree


class Group(BaseModel):
    typed: Optional[str] = None
    valid: Optional[str] = None
    confirmed: Optional[str] = None

    def generate_valid(self):
        # remove nonword from group (separators like "-")
        group_nonword: str = pattern.NON_LETTER.sub("", self.typed)
        # make group all caps
        group_caps = group_nonword.upper()
        # add validated group to context as valid group
        self.valid = group_caps
    
    def set_valid_as_confirmed(self):
        self.confirmed = self.valid

class Settings(Values):
    group: Group = PydField(default_factory=Group)
    zoom: zoom.Container = PydField(default_factory=zoom.Container)
    broadcast: Optional[bool] = None
    should_pin: Optional[bool] = None

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