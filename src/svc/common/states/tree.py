from . import (
    Space,
    State,
    Tree,
    INIT_MAIN,
    HUB_MAIN,
    HUB_SETTINGS,
    GROUP,
    UNKNOWN_GROUP,
    SCHEDULE_BROADCAST,
    SHOULD_PIN,
    INIT_FINISH,
)


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
    __space__ = Space.INIT

    I_MAIN               = State(**INIT_MAIN)
    I_GROUP              = State(**GROUP)
    II_UNKNOWN_GROUP     = State(**UNKNOWN_GROUP)
    I_SCHEDULE_BROADCAST = State(**SCHEDULE_BROADCAST)
    II_SHOULD_PIN        = State(**SHOULD_PIN)
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
    __space__ = Space.HUB

    I_MAIN                 = State(**HUB_MAIN)
    II_SETTINGS            = State(**HUB_SETTINGS)
    III_GROUP              = State(**GROUP)
    IIII_UNKNOWN_GROUP     = State(**UNKNOWN_GROUP)
    III_SCHEDULE_BROADCAST = State(**SCHEDULE_BROADCAST)
    III_SHOULD_PIN         = State(**SHOULD_PIN)


INIT = Init()
HUB = Hub()
