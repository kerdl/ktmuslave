from dataclasses import dataclass
from typing import Any, Iterable, Optional
from . import (
    INIT_MAIN,
    HUB_MAIN,
    HUB_SETTINGS,
    GROUP,
    UNKNOWN_GROUP,
    SCHEDULE_BROADCAST,
    SHOULD_PIN,
    INIT_FINISH,
    State
)

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

@dataclass
class Tree:
    __states__: list[State] = None

    def __init__(self) -> None:
        self.__states__ = []

        filtered_states: filter[tuple[str, State]] = (
            # filter by condition              for "Init" or "Hub" trees
            filter(self.__filter_condition__, type(self).__dict__.items())
        )

        for anchor, state in filtered_states:
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

class Init(Tree):
    """
    ```
    MAIN
      ↓
    GROUP
      ┝ UNKNOWN_GROUP
      ↓
    SCHEDULE_BROADCAST
      ↓
    SHOULD_PIN
      ↓
    FINISH
    ```notpython
    """
    I_MAIN               = State(**INIT_MAIN)
    I_GROUP              = State(**GROUP)
    II_UNKNOWN_GROUP     = State(**UNKNOWN_GROUP)
    I_SCHEDULE_BROADCAST = State(**SCHEDULE_BROADCAST)
    I_SHOULD_PIN         = State(**SHOULD_PIN)
    I_FINISH             = State(**INIT_FINISH)

class Hub(Tree):
    """
    ```
    MAIN
      ┕ SETTINGS
           ┝ GROUP
           |   ┕ UNKNOWN_GROUP
           ┝ SCHEDULE_BROADCAST
           ┕ SHOULD_PIN
    ```notpython
    """
    I_MAIN                 = State(**HUB_MAIN)
    II_SETTINGS            = State(**HUB_SETTINGS)
    III_GROUP              = State(**GROUP)
    IIII_UNKNOWN_GROUP     = State(**UNKNOWN_GROUP)
    III_SCHEDULE_BROADCAST = State(**SCHEDULE_BROADCAST)
    III_SHOULD_PIN         = State(**SHOULD_PIN)

INIT = Init()
HUB = Hub()
