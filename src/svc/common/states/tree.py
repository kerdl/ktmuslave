from enum import Enum
from . import (
    InitMain,
    HubMain,
    HubSettings,
    Group,
    UnknownGroup,
    ScheduleBroadcast,
    ShouldPin,
    InitFinish
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

class Init(Enum):
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
    I_MAIN               = InitMain
    I_GROUP              = Group
    II_UNKNOWN_GROUP     = UnknownGroup
    I_SCHEDULE_BROADCAST = ScheduleBroadcast
    I_SHOULD_PIN         = ShouldPin
    I_FINISH             = InitFinish

class Hub(Enum):
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
    I_MAIN                 = HubMain
    II_SETTINGS            = HubSettings
    III_GROUP              = Group
    IIII_UNKNOWN_GROUP     = UnknownGroup
    III_SCHEDULE_BROADCAST = ScheduleBroadcast
    III_SHOULD_PIN         = ShouldPin
