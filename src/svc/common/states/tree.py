from typing import Optional
from . import *


class Init(Tree):
    __space__ = Space.INIT

    I_MAIN = State(**INIT_MAIN)
    I_FINISH = State(**INIT_FINISH)

class Settings(Tree):
    __space__ = Space.SETTINGS

    I_MAIN = State(**SETTINGS_MAIN)
    II_MODE = State(**MODE)
    II_IDENTIFICATION = State(**IDENTIFICATION)
    II_GROUP = State(**GROUP)
    III_UNKNOWN_GROUP = State(**UNKNOWN_GROUP)
    II_TEACHER = State(**TEACHER)
    III_UNKNOWN_TEACHER = State(**UNKNOWN_TEACHER)
    II_BROADCAST = State(**BROADCAST)
    III_SHOULD_PIN = State(**SHOULD_PIN)
    II_ZOOM = State(**INIT_ZOOM)


class Hub(Tree):
    __space__ = Space.HUB

    I_MAIN = State(**HUB_MAIN)


class Reset(Tree):
    __space__ = Space.RESET

    I_MAIN = State(**RESET_MAIN)


class Zoom(Tree):
    __space__ = Space.ZOOM

    I_MASS = State(**ZOOM_MASS)
    II_BROWSE = State(**ZOOM_BROWSE)
    III_ENTRY = State(**ZOOM_ENTRY)
    IIII_NAME = State(**ZOOM_EDIT_NAME)
    IIII_URL = State(**ZOOM_EDIT_URL)
    IIII_ID = State(**ZOOM_EDIT_ID)
    IIII_PWD = State(**ZOOM_EDIT_PWD)
    IIII_HOST_KEY = State(**ZOOM_EDIT_HOST_KEY)
    IIII_NOTES = State(**ZOOM_EDIT_NOTES)
    III_DUMP = State(**ZOOM_DUMP)
    IIII_CONFIRM_REMOVE_ALL = State(**ZOOM_CONFIRM_REMOVE_ALL)
    IIII_CONFIRM_CLEAR_ALL = State(**ZOOM_CONFIRM_CLEAR_ALL)
    I_MASS_CHECK = State(**ZOOM_MASS_CHECK)


class Admin(Tree):
    __space__ = Space.RESET

    I_EXECUTE_CODE = State(**EXECUTE_CODE)


INIT = Init()
HUB = Hub()
ZOOM = Zoom()
SETTINGS = Settings()
RESET = Reset()
ADMIN = Admin()

STR_MAP = {
    Init.__name__: INIT,
    Hub.__name__: HUB,
    Zoom.__name__: ZOOM,
    Settings.__name__: SETTINGS,
    Reset.__name__: RESET,
    Admin.__name__: ADMIN,
}

def from_str(tree: str) -> Optional[Tree]:
    return STR_MAP.get(tree)
