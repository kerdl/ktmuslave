from . import (
    Space,
    State,
    Tree,
    INIT_MAIN,
    HUB_MAIN,
    SETTINGS_MAIN,
    GROUP,
    UNKNOWN_GROUP,
    BROADCAST,
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
    (Settings space)
      ↓
    FINISH
    ```notpython
    """
    __space__ = Space.INIT

    I_MAIN   = State(**INIT_MAIN)
    I_FINISH = State(**INIT_FINISH)

class Settings(Tree):
    """
    ```
    MAIN
      ┝ GROUP
      |   ┝ UNKNOWN_GROUP
      ┝ BROADCAST
      |   ┝ SHOULD_PIN
      ┕ ZOOM
    ```notpython
    """

    __space__ = Space.SETTINGS

    I_MAIN            = State(**SETTINGS_MAIN)
    II_GROUP          = State(**GROUP)
    III_UNKNOWN_GROUP = State(**UNKNOWN_GROUP)
    II_BROADCAST      = State(**BROADCAST)
    III_SHOULD_PIN    = State(**SHOULD_PIN)
    II_ZOOM           = State(**INIT_ZOOM)


class Hub(Tree):
    """
    ```
    MAIN
      ┕ SETTINGS
        ┕ (other states inherited from Init)
    ```notpython
    """
    __space__ = Space.HUB

    I_MAIN                 = State(**HUB_MAIN)


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


Init     = Init()
HUB      = Hub()
ZOOM     = Zoom()
SETTINGS = Settings()
