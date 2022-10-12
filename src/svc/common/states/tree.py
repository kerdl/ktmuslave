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
    INIT_ZOOM,
    ZOOM_MASS,
    ZOOM_MASS_CHECK,
    ZOOM_BROWSE,
    ZOOM_ENTRY,
    ZOOM_EDIT_NAME,
    ZOOM_EDIT_URL,
    ZOOM_EDIT_ID,
    ZOOM_EDIT_PWD
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
    ZOOM
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
    I_ZOOM               = State(**INIT_ZOOM)
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


class Zoom(Tree):
    __space__ = Space.ZOOM

    I_MASS       = State(**ZOOM_MASS)
    II_BROWSE    = State(**ZOOM_BROWSE)
    III_ENTRY    = State(**ZOOM_ENTRY)
    IIII_NAME    = State(**ZOOM_EDIT_NAME)
    IIII_URL     = State(**ZOOM_EDIT_URL)
    IIII_ID      = State(**ZOOM_EDIT_ID)
    IIII_PWD     = State(**ZOOM_EDIT_PWD)
    I_MASS_CHECK = State(**ZOOM_MASS_CHECK)


INIT = Init()
HUB  = Hub()
ZOOM = Zoom()
