from dataclasses import dataclass
from typing import Optional, Any

from src.svc.common.states import State, Values
from src.svc.common.states.tree import Init


@dataclass
class Group:
    typed: Optional[str] = None
    valid: Optional[str] = None
    confirmed: Optional[str] = None

@dataclass
class Settings(Values):
    group: Group
    schedule_broadcast: Optional[bool] = None
    should_pin: Optional[bool] = None

    def get_from_state(self, state: State) -> Any:
        VALUES = {
            Init.I_GROUP:              self.group.confirmed,
            Init.I_SCHEDULE_BROADCAST: self.schedule_broadcast,
            Init.II_SHOULD_PIN:        self.should_pin
        }

        return VALUES.get(state)
