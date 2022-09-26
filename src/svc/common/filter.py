from dataclasses import dataclass

from src.svc.common import CommonEverything, Source
from src.svc.common.states import State
from src.svc.vk.keyboard import CMD


@dataclass
class BaseFilter:
    async def __call__(self, everything: CommonEverything) -> bool: 
        ...

@dataclass
class MessageOnlyFilter(BaseFilter):
    async def __call__(self, everything: CommonEverything) -> bool:
        return everything.event_src == Source.MESSAGE

@dataclass
class EventOnlyFilter(BaseFilter):
    async def __call__(self, everything: CommonEverything) -> bool:
        return everything.event_src == Source.EVENT

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
            return event.tg.data == self.payload
        
        return False

@dataclass
class UnionFilter(BaseFilter):
    filters: tuple[BaseFilter]

    async def __call__(self, everything: CommonEverything) -> bool:
        filter_results: list[bool] = []

        for filter_ in self.filters:
            result = await filter_(everything)
            filter_results.append(result)
        
        return any(filter_results)
