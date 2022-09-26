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
    ZOOM_MASS_MAIN,
    ZOOM_MASS_NEW_DATA,
    ZOOM_MASS_OVERRIDE_DATA,
    ZOOM_MASS_CHECK,
    ZOOM_BROWSE_MAIN,
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


class ZoomMass(Tree):
    """
    
    """
    __space__ = Space.ZOOM_MASS

    I_MAIN           = State(**ZOOM_MASS_MAIN)
    II_NEW_DATA      = State(**ZOOM_MASS_NEW_DATA)
    II_OVERRIDE_DATA = State(**ZOOM_MASS_OVERRIDE_DATA)
    I_CHECK          = State(**ZOOM_MASS_CHECK)

class ZoomBrowse(Tree):
    """
    """
    __space__ = Space.ZOOM_BROWSE

    I_MAIN = State(**ZOOM_BROWSE_MAIN)


class ZoomEdit(Tree):
    """
    ```
    NAME
    ↓
    URL
    ↓
    ID
    ↓
    PWD
    ```notpython
    """
    __space__ = Space.ZOOM_EDIT

    I_NAME = State(**ZOOM_EDIT_NAME)
    I_URL  = State(**ZOOM_EDIT_URL)
    I_ID   = State(**ZOOM_EDIT_ID)
    I_PWD  = State(**ZOOM_EDIT_PWD)


INIT        = Init()
HUB         = Hub()
ZOOM_MASS   = ZoomMass()
ZOOM_BROWSE = ZoomBrowse()
ZOOM_EDIT   = ZoomEdit()
