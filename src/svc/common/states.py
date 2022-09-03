from enum import Enum, auto


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
    MAIN               = auto()
    GROUP              = auto()
    UNKNOWN_GROUP      = auto()
    SCHEDULE_BROADCAST = auto()
    SHOULD_PIN         = auto()
    FINISH             = auto()

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
    MAIN               = auto()
    SETTINGS           = auto()
    GROUP              = auto()
    UNKNOWN_GROUP      = auto()
    SCHEDULE_BROADCAST = auto()
    SHOULD_PIN         = auto()
