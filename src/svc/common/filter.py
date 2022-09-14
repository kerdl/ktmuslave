from dataclasses import dataclass

from src.svc.common import CommonEverything
from src.svc.common.states import State
from src.svc.vk.keyboard import CMD


@dataclass
class BaseFilter:
    async def __call__(self, everything: CommonEverything) -> bool: 
        ...

@dataclass
class StateFilter(BaseFilter):
    state: State

    async def __call__(self, everything: CommonEverything) -> bool:
        return everything.navigator.current == self.state

@dataclass
class PayloadFilter(BaseFilter):
    payload: str

    async def __call__(self, everything: CommonEverything) -> bool:
        if everything.is_from_message:
            return False
        
        event = everything.event

        if event.is_from_vk:
            return event.vk['object']['payload'] == {CMD: self.payload}
        elif event.is_from_tg:
            return event.tg_callback_query.data == self.payload
        
        return False