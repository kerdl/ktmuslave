from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal, Iterable

from src.svc.common import error


class Space:
    """
    ## In what space the user currently in

    By space I mean these types of environments:
    - `init` - where user gets first time to specify
        - his group
        - if he wants to get updates
        - if the bot should pin the updates
        - if he wants to add zoom data
    - `hub` - the main user area, where he can 
        - view schedule, 
        - view links,
        - can change settings
    - `zoom_mass` - where user can
        - add new zoom links from one big message of links
    - `zoom_browse` - where user can
        - browse all zoom links he added
    - `zoom_edit` - where user can
        - edit specific zoom data
    """
    INIT        = "init"
    HUB         = "hub"
    ZOOM_MASS   = "zoom_mass"
    ZOOM_BROWSE = "zoom_browse"
    ZOOM_EDIT   = "zoom_edit"

SPACE_LITERAL = Literal["init", "hub", "zoom_mass", "zoom_browse", "zoom_edit"]


class Values:
    def get_from_state(self, state: State): ...


@dataclass
class State:
    name: str
    tree: Optional[Tree] = None
    space: Optional[SPACE_LITERAL] = None
    anchor: Optional[str] = None
    level: Optional[int] = None
    parent: Optional[State] = None
    child: Optional[list[State]] = None

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
            # filter by condition              for trees
            filter(self.__filter_states__, type(self).__dict__.items())
        )

        parent_trace: list[State] = []

        def last_parent() -> Optional[State]:
            if len(parent_trace) > 0:
                return parent_trace[-1]

        for anchor, state in filtered_states:
            state.tree = self
            state.space = self.__space__
            state.anchor = anchor
            state.level = self.__level__(anchor)
            state.child = []

            if (last_parent() is None):
                parent_trace.append(state)
            elif (last_parent().level == state.level):
                del parent_trace[-1]
                parent_trace.append(state)
            else:
                state.parent = last_parent()

            self.__states__.append(state)

        for stateA in self.__states__:
            stateA: State

            for stateB in self.__states__:
                stateB: State

                if stateA.parent == stateB:
                    stateB.child.append(stateA)
                    break

    def __iter__(self) -> Iterable[State]:
        return iter(self.__states__)

    @staticmethod
    def __filter_states__(attr: tuple[str, State]):
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

INIT_MAIN               = { "name": "Категорически приветствую", }
HUB_MAIN                = { "name": "Главная",                   }
HUB_SETTINGS            = { "name": "Настройки",                 }
GROUP                   = { "name": "Группа",                    }
UNKNOWN_GROUP           = { "name": "Неизвестная группа",        }
SCHEDULE_BROADCAST      = { "name": "Рассылка расписания",       }
SHOULD_PIN              = { "name": "Закреп расписания",         }
INIT_ZOOM               = { "name": "Zoom данные",               }
INIT_FINISH             = { "name": "ФИНААААЛ СУЧКИ",            }
ZOOM_MASS_MAIN          = { "name": "Сообщение с ссылками",      }
ZOOM_MASS_NEW_DATA      = { "name": "Новые данные",              }
ZOOM_MASS_OVERRIDE_DATA = { "name": "Перезапись данных",         }
ZOOM_MASS_EDIT          = { "name": "Редактирование",            }
ZOOM_MASS_CHECK         = { "name": "Подтверждение изменений"    }
ZOOM_BROWSE_MAIN        = { "name": "Выбор препода",             }
ZOOM_EDIT_NAME          = { "name": "Имя препода",               }
ZOOM_EDIT_URL           = { "name": "Ссылка",                    }
ZOOM_EDIT_ID            = { "name": "ID",                        }
ZOOM_EDIT_PWD           = { "name": "Пароль",                    }
