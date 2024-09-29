from __future__ import annotations
from typing import Optional, Any, Literal
from pydantic import BaseModel, Field as PydField
import difflib

from src.data import zoom as zoom_mod
from src.svc import common
from src.parse import pattern, group, teacher
from src.svc.common.states import State, Values
from src.svc.common.states.tree import INIT, SETTINGS as SettingsTree


MODE_LITERAL = Literal["group", "teacher"]

class Mode:
    GROUP = "group"
    TEACHER = "teacher"

class Group(BaseModel):
    typed: Optional[str] = None
    valid: Optional[str] = None
    confirmed: Optional[str] = None

    def generate_valid(self):
        self.valid = group.validate(self.typed)
    
    def set_valid_as_confirmed(self):
        self.confirmed = self.valid

class Teacher(BaseModel):
    typed: Optional[str] = None
    valid: Optional[str] = None
    confirmed: Optional[str] = None

    def generate_valid(self, reference: list[str]) -> bool:
        self.valid = teacher.validate(self.typed, reference)
        return self.valid is not None
    
    def set_valid_as_confirmed(self):
        self.confirmed = self.valid

class Settings(Values):
    mode: Optional[MODE_LITERAL] = None
    group: Group = PydField(default_factory=Group)
    teacher: Teacher = PydField(default_factory=Teacher)
    zoom: zoom_mod.Container = PydField(default_factory=zoom_mod.Container.as_group)
    tchr_zoom: zoom_mod.Container = PydField(default_factory=zoom_mod.Container.as_tchr)
    broadcast: Optional[bool] = None
    should_pin: Optional[bool] = None

    def get_from_state(self, state: State) -> Any:
        storage = None

        if self.mode == Mode.GROUP:
            storage = self.zoom
        elif self.mode == Mode.TEACHER:
            storage = self.tchr_zoom
        
        VALUES = {
            SettingsTree.II_MODE: self.mode,
            SettingsTree.II_GROUP: self.group.confirmed,
            SettingsTree.II_TEACHER: self.teacher.confirmed,
            SettingsTree.II_BROADCAST: self.broadcast,
            SettingsTree.III_SHOULD_PIN: self.should_pin,
            SettingsTree.II_ZOOM: len(storage.entries) if storage and storage.is_finished else None
        }

        return VALUES.get(state)
    
    def defaults_from_everything(self, everything: common.CommonEverything):
        if SettingsTree.III_SHOULD_PIN in everything.navigator.ignored:
            self.should_pin = False
