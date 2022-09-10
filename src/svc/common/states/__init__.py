from dataclasses import dataclass
from typing import Optional, Literal


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
    space: Optional[SPACE_LITERAL] = None
    anchor: Optional[str] = None
    level: Optional[int] = None

INIT_MAIN          = { "name": "Категорически приветствую", "emoji": "🚽" }
HUB_MAIN           = { "name": "Главная",                   "emoji": "🚽" }
HUB_SETTINGS       = { "name": "Настройки",                 "emoji": "🚽" }
GROUP              = { "name": "Группа",                    "emoji": "🚽" }
UNKNOWN_GROUP      = { "name": "Неизвестная группа",        "emoji": "🚽" }
SCHEDULE_BROADCAST = { "name": "Рассылка расписания",       "emoji": "🚽" }
SHOULD_PIN         = { "name": "Закреп расписания",         "emoji": "🚽" }
INIT_FINISH        = { "name": "ФИНААААЛ СУЧКИ",            "emoji": "🚽" }
