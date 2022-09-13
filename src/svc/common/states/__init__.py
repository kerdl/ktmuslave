from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal, Iterable

from src.svc.common import error


class Space:
    """
    ## In what space the user currently in

    By space I mean two types of environments:
    - `init` - where user gets first time to specify
        - his group
        - if he wants to get updates
        - if the bot should pin the updates
    - `hub` - the main user area, where he can 
        - view schedule, 
        - view links,
        - can change settings
    """
    INIT = "init"
    HUB = "hub"

SPACE_LITERAL = Literal["init", "hub"]

@dataclass
class State:
    name: str
    emoji: str
    tree: Optional[Tree] = None
    space: Optional[SPACE_LITERAL] = None
    anchor: Optional[str] = None
    level: Optional[int] = None

    def __hash__(self) -> int:
        return hash(self.anchor)

@dataclass
class Tree:
    __space__: SPACE_LITERAL = None
    __states__: list[State] = None

    def __init__(self) -> None:
        if self.__space__ is None:
            raise error.NoSpaceSpecified(
                f"tree {self} doesn't have __space__ variable set"
            )
        
        self.__states__ = []

        filtered_states: filter[tuple[str, State]] = (
            # filter by condition              for "Init" or "Hub" trees
            filter(self.__filter_condition__, type(self).__dict__.items())
        )

        for anchor, state in filtered_states:
            state.tree = self
            state.space = self.__space__
            state.anchor = anchor
            state.level = self.__level__(anchor)
            self.__states__.append(state)

    def __iter__(self) -> Iterable[State]:
        return iter(self.__states__)

    @staticmethod
    def __filter_condition__(attr: tuple[str, State]):
        """
        ## Called by `filter` as a condition check
        - `attr` - a tuple of `( KEY, VALUE )`
        """

        # ( KEY, ...
        key = attr[0]
        # ..., VALUE )
        value = attr[1]

        return key.startswith("I")

    @staticmethod
    def __level__(name: str) -> int:
        """
        ## Get how much `I`'s in `name`
        - `I` -> 1
        - `IIII` -> 4
        """

        return len(name.split("_")[0])

INIT_MAIN          = { "name": "Категорически приветствую", "emoji": "🚽" }
HUB_MAIN           = { "name": "Главная",                   "emoji": "🚽" }
HUB_SETTINGS       = { "name": "Настройки",                 "emoji": "🚽" }
GROUP              = { "name": "Группа",                    "emoji": "🚽" }
UNKNOWN_GROUP      = { "name": "Неизвестная группа",        "emoji": "🚽" }
SCHEDULE_BROADCAST = { "name": "Рассылка расписания",       "emoji": "🚽" }
SHOULD_PIN         = { "name": "Закреп расписания",         "emoji": "🚽" }
INIT_FINISH        = { "name": "ФИНААААЛ СУЧКИ",            "emoji": "🚽" }
