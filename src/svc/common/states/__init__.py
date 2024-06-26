from __future__ import annotations
from dataclasses import dataclass
from pydantic import BaseModel
from typing import Callable, ClassVar, Optional, Literal, Iterable

from src.data import zoom
from src.svc import common
from src.svc.common import error


class Space:
    """ ## In what space the user currently in """
    INIT = "init"
    """
    Where user gets first time with welcome message
    """
    SETTINGS = "settings"
    """
    Common area, where user can specify:
        - his group
        - if he wants to get broadcast
        - if the bot should pin the broadcast
        - if he wants to add zoom data
    """
    HUB = "hub"
    """
    The main user area, where he can 
        - view schedule, 
        - view links,
        - can change settings
    """
    ZOOM = "zoom"
    """
    Where user can:
        - add multiple zoom entries from one message
        - edit every signle one of them manually
        - delete them
    """
    RESET = "reset"
    """
    Where user can reset their settings
    """

SPACE_LITERAL = Literal["init", "settings", "hub", "zoom", "reset"]


class Values(BaseModel):
    def get_from_state(self, state: State): ...

def default_action(everything: common.CommonEverything) -> None: ...
def default_condition(everything: common.CommonEverything) -> bool: return True


@dataclass
class State:
    name: str
    """
    # Friendly readable name
    """
    back_trace: bool = True
    """
    # Should this state be back traced

    ## In other words
    - can you go here by pressing `next` button?
    """
    tree: Optional[str] = None
    """
    # Where this state is located
    """
    space: Optional[SPACE_LITERAL] = None
    """
    # Type of space this state in
    """
    anchor: Optional[str] = None
    """
    # Original name as it was in a class

    ## Example
    - `II_UNKNOWN_GROUP`
    """
    level: Optional[int] = None
    """
    # How much `I's` in `anchor`

    - `I` -> 1
    - `III` -> 3
    """
    parent: Optional[State] = None
    """
    # Parent of this state

    - `I_MAIN` -> no parent
    - `II_SETTINGS` -> `I_MAIN` is a parent
    """
    child: Optional[list[State]] = None
    """
    # All childs for this state

    - `I_MAIN` -> `[II_SETTINGS, II_GARBAGE]` are childs
    - `II_SETTINGS` -> `[III_FUCKME]` is a child
    - `III_FUCKME` -> no childs
    - `II_GARBAGE` -> no childs
    """
    tags: Optional[list[str]] = None
    """
    # Identification tags

    - `["teacher"]`: this state is teacher-specific
    - `["group"]`: this state is group-specific
    - `["common"]`: this state is common
    """

    on_enter: Callable[[common.CommonEverything], None] = default_action
    """
    # Executes
    - when `navigator` enters this state
    for the first time (it wasn't in trace)
    """
    on_traced_enter: Callable[[common.CommonEverything], None] = default_action
    """
    # Executes
    - when `navigator` enters this state
    by going back (it was in trace)
    """
    on_exit: Callable[[common.CommonEverything], None] = default_action
    """
    # Executes
    - when `navigator` exits this state
    by going back (it does not remain in trace)
    """
    on_traced_exit: Callable[[common.CommonEverything], None] = default_action
    """
    # Executes
    - when `navigator` exits this state
    by going further (it remains in trace)
    """
    on_delete: Callable[[common.CommonEverything], None] = default_action
    """
    # Executes
    - when `navigator` deletes this state
    from trace, no matter where it was
    """
    should_display_in_tree: Callable[[common.CommonEverything], bool] = default_condition

    def __str__(self) -> str:
        return f"{self.tree}:{self.anchor}"

    def __hash__(self) -> int:
        return hash(f"{self.tree}:{self.anchor}")
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, State):
            return hash(self) == hash(other)
        
        return hash(self) == other

@dataclass
class Tree:
    __space__: ClassVar[SPACE_LITERAL] = None
    __states__: ClassVar[list[State]] = None

    def __init__(self) -> None:
        if self.__space__ is None:
            raise error.NoSpaceSpecified(
                f"tree {self} doesn't have __space__ variable set"
            )
        
        self.__states__ = []

        filtered_states = self.__filter_states__()

        parent_trace: list[State] = []

        def last_parent() -> Optional[State]:
            if len(parent_trace) > 0:
                return parent_trace[-1]

        for anchor, state in filtered_states:
            state.tree = type(self).__name__
            state.space = self.__space__
            state.anchor = anchor
            state.level = self.__level__(anchor)
            state.child = []

            if (last_parent() is None):
                parent_trace.append(state)
            elif (last_parent().level < state.level):
                state.parent = last_parent()
                parent_trace.append(state)
            elif (last_parent().level == state.level):
                del parent_trace[-1]
                parent_trace.append(state)
            elif (last_parent().level > state.level):
                if state.level < 2:
                    state.parent = last_parent()
                else:
                    while last_parent().level != state.level - 1:
                        del parent_trace[-1]

                    state.parent = last_parent()
            else:
                state.parent = last_parent()

            self.__states__.append(state)

        for stateA in self.__states__:
            stateA: State

            for stateB in self.__states__:
                stateB: State

                if stateA.parent == stateB:
                    stateB.child.append(stateA)
                    break

    def from_str(self, state: str) -> Optional[State]:
        for tree_state in self.__filter_states__():
            name = tree_state[0]
            state_data = tree_state[1]

            if tree_state[0] == state:
                return state_data

    def __iter__(self) -> Iterable[State]:
        return iter(self.__states__)

    @staticmethod
    def __states_filter__(attr: tuple[str, State]):
        """
        ## Called by `filter` as a condition check
        - `attr` - a tuple of `( KEY, VALUE )`
        """

        # ( KEY, ...
        key = attr[0]
        # ..., VALUE )
        value = attr[1]

        return key.startswith("I")
    
    def __filter_states__(self) -> filter[tuple[str, State]]:
                      # filter by condition              for trees
        return filter(self.__states_filter__, type(self).__dict__.items())


    @staticmethod
    def __level__(name: str) -> int:
        """
        ## Get how much `I`'s in `name`
        - `I` -> 1
        - `IIII` -> 4
        """

        return len(name.split("_")[0])

def from_encoded(encoded: str) -> Optional[State]:
    from .tree import from_str

    (str_tree, str_state) = encoded.split(":")
    class_tree = from_str(str_tree)

    return class_tree.from_str(str_state)

INIT_MAIN = {
    "name": "Категорически приветствую",
}
HUB_MAIN = {
    "name": "Главная",
}
def _ctx_stop_switching_modes(everything: common.CommonEverything):
    everything.ctx.is_switching_modes = False
SETTINGS_MAIN = {
    "name": "Настройки",
    "back_trace": False,
    "on_enter": _ctx_stop_switching_modes
}
MODE = {
    "name": "Режим",
}
def _ctx_should_show_identification_state(everything: common.CommonEverything) -> bool:
    return everything.ctx.settings.mode is None
IDENTIFICATION = {
    "name": "Идентификация",
    "should_display_in_tree": _ctx_should_show_identification_state
}
def _ctx_should_show_group_state(everything: common.CommonEverything) -> bool:
    from src.data.settings import Mode
    return everything.ctx.settings.mode == Mode.GROUP
GROUP = {
    "name": "Группа",
    "should_display_in_tree": _ctx_should_show_group_state,
    "tags": ["group"]
}
UNKNOWN_GROUP = {
    "name": "Неизвестная группа",
    "back_trace": False,
    "tags": ["group"]
}
def _ctx_should_show_teacher_state(everything: common.CommonEverything) -> bool:
    from src.data.settings import Mode
    return everything.ctx.settings.mode == Mode.TEACHER
TEACHER = {
    "name": "Препод",
    "should_display_in_tree": _ctx_should_show_teacher_state,
    "tags": ["teacher"]
}
UNKNOWN_TEACHER = {
    "name": "Неизвестный препод",
    "back_trace": False,
    "tags": ["teacher"]
}
BROADCAST = {
    "name": "Рассылка расписания",
}
SHOULD_PIN = {
    "name": "Закреп расписания",
}
INIT_ZOOM = {
    "name": "Zoom данные",
}
def _ctx_false(everything: common.CommonEverything) -> False: return False
TIME_OVERRIDE = {
    "name": "Замена времени",
    "should_display_in_tree": _ctx_false
}
INIT_FINISH = {
    "name": "ФИНААААЛ СУЧКИ",
}
ZOOM_MASS = {
    "name": "Сообщение с ссылками",
    "back_trace": False,
}
ZOOM_MASS_CHECK = {
    "name": "Подтверждение изменений",
}
ZOOM_BROWSE = {
    "name": "Выбор препода",
    "on_enter": zoom.focus_auto,
    "on_traced_enter": zoom.focus_auto,
    "on_exit": zoom.unfocus,
}
ZOOM_ENTRY = {
    "name": "Редактирование",
    "on_exit": zoom.unselect
}
ZOOM_EDIT_NAME = {
    "name": "Имя препода",
    "on_enter": zoom.focus_auto,
}
ZOOM_EDIT_URL = {
    "name": "Ссылка",
}
ZOOM_EDIT_ID = {
    "name": "ID",
}
ZOOM_EDIT_PWD = {
    "name": "Пароль",
}
ZOOM_EDIT_HOST_KEY = {
    "name": "Ключ хоста",
}
ZOOM_EDIT_NOTES = {
    "name": "Заметки",
}
ZOOM_DUMP = {
    "name": "Дамп",
}
ZOOM_CONFIRM_REMOVE_ALL = {
    "name": "Подтверждение удаления"
}
ZOOM_CONFIRM_CLEAR_ALL = {
    "name": "Подтверждение удаления"
}
EXECUTE_CODE = {
    "name": "Выполнить код",
}
RESET_MAIN = {
    "name": "Сброс"
}

__all__ = (
    "INIT_MAIN",
    "HUB_MAIN",
    "SETTINGS_MAIN",
    "MODE",
    "IDENTIFICATION",
    "GROUP",
    "TEACHER",
    "UNKNOWN_GROUP",
    "UNKNOWN_TEACHER",
    "BROADCAST",
    "SHOULD_PIN",
    "INIT_ZOOM",
    "TIME_OVERRIDE",
    "INIT_FINISH",
    "ZOOM_MASS",
    "ZOOM_MASS_CHECK",
    "ZOOM_BROWSE",
    "ZOOM_ENTRY",
    "ZOOM_EDIT_NAME",
    "ZOOM_EDIT_URL",
    "ZOOM_EDIT_ID",
    "ZOOM_EDIT_PWD",
    "ZOOM_EDIT_HOST_KEY",
    "ZOOM_EDIT_NOTES",
    "ZOOM_DUMP",
    "ZOOM_CONFIRM_REMOVE_ALL",
    "ZOOM_CONFIRM_CLEAR_ALL",
    "EXECUTE_CODE",
    "RESET_MAIN",
    "Tree",
    "State",
    "Space"
)