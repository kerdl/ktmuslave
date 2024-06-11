from __future__ import annotations
from typing import Optional, Any, Literal
from pydantic import BaseModel, Field as PydField
import difflib

from src.data import zoom as zoom_mod
from src.data.schedule import TIME_MODE_LITERAL, TimeMode
from src.svc import common
from src.parse import pattern
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
        # remove nonword from group (separators like "-")
        group_nonword: str = pattern.NON_LETTER.sub("", self.typed)
        # make group all caps
        group_caps = group_nonword.upper()
        # add validated group to context as valid group
        self.valid = group_caps
    
    def set_valid_as_confirmed(self):
        self.confirmed = self.valid

class Teacher(BaseModel):
    typed: Optional[str] = None
    valid: Optional[str] = None
    confirmed: Optional[str] = None

    def generate_valid(self, reference: list[str]) -> bool:
        teacher = pattern.TEACHER.search(self.typed)
        if teacher is not None:
            teacher: str = teacher.group()
            if not teacher.endswith("."):
                teacher += "."
            
            self.valid = teacher
            return True
        
        teacher_case_ignored = pattern.TEACHER_CASE_IGNORED.search(self.typed)
        if teacher_case_ignored is not None:
            teacher_case_ignored: str = teacher_case_ignored.group()
            last_name = pattern.TEACHER_LAST_NAME_CASE_IGNORED.search(teacher_case_ignored)
            rest = teacher_case_ignored[:last_name.pos]
            rest = rest.upper()
            last_name = last_name.group().capitalize()
            self.valid = f"{last_name} {rest}"
            return True
        
        teacher_no_dots_case_ignored = pattern.TEACHER_NO_DOTS_CASE_IGNORED.search(self.typed)
        if teacher_no_dots_case_ignored is not None:
            teacher_no_dots_case_ignored: str = teacher_no_dots_case_ignored.group()
            last_name = pattern.TEACHER_LAST_NAME_CASE_IGNORED.search(teacher_no_dots_case_ignored)
            rest = teacher_no_dots_case_ignored[last_name.end():]
            rest = rest.strip()
            rest = rest.upper()
            last_name = last_name.group().capitalize()
            dotted_rest = ""

            for char in rest:
                dotted_rest += f"{char}." 
            
            self.valid = f"{last_name} {dotted_rest}"
            return True
        
        teacher_last_name_case_ignored = pattern.TEACHER_LAST_NAME_CASE_IGNORED.search(self.typed)
        if teacher_last_name_case_ignored is not None:
            teacher_last_name_case_ignored: str = teacher_last_name_case_ignored.group()
            capitalized = teacher_last_name_case_ignored.capitalize()

            last_name_short_map = {}
            for ref in reference:
                short = ref.split(" ")[0] if " " in ref else ref
                last_name_short_map[short] = ref

            matches = difflib.get_close_matches(
                capitalized,
                [short for short in last_name_short_map.keys()],
                cutoff=0.8
            )
            if len(matches) < 1:
                return False

            first_match = matches[0]
            self.valid = last_name_short_map[first_match]
            return True
        
        return False
        
    
    def set_valid_as_confirmed(self):
        self.confirmed = self.valid

class Settings(Values):
    mode: Optional[MODE_LITERAL]
    group: Group = PydField(default_factory=Group)
    teacher: Teacher = PydField(default_factory=Teacher)
    zoom: zoom_mod.Container = PydField(default_factory=zoom_mod.Container.as_group)
    tchr_zoom: zoom_mod.Container = PydField(default_factory=zoom_mod.Container.as_tchr)
    broadcast: Optional[bool] = None
    should_pin: Optional[bool] = None
    time_mode: Optional[TIME_MODE_LITERAL] = TimeMode.OVERRIDE

    def get_from_state(self, state: State) -> Any:
        storage = None

        if self.mode == Mode.GROUP:
            storage = self.zoom
        elif self.mode == Mode.TEACHER:
            storage = self.tchr_zoom
        
        VALUES = {
            SettingsTree.II_MODE:        self.mode,
            SettingsTree.II_GROUP:       self.group.confirmed,
            SettingsTree.II_TEACHER:     self.teacher.confirmed,
            SettingsTree.II_BROADCAST:   self.broadcast,
            SettingsTree.III_SHOULD_PIN: self.should_pin,
            SettingsTree.II_ZOOM:        len(storage.entries) if storage and storage.is_finished else None
        }

        return VALUES.get(state)
    
    def defaults_from_everything(self, everything: common.CommonEverything):
        if SettingsTree.III_SHOULD_PIN in everything.navigator.ignored:
            self.should_pin = False
