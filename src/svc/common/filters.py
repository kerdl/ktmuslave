from dataclasses import dataclass

from src.svc.common import CommonEverything, Source
from src.svc.common.states import State
from src.svc.vk.keyboard import CMD




@dataclass
class BaseFilter:
    """
    # Base class to create filters
    """
    async def __call__(self, everything: CommonEverything) -> bool: 
        ...

@dataclass
class MessageOnlyFilter(BaseFilter):
    """
    # Only works on messages
    """
    async def __call__(self, everything: CommonEverything) -> bool:
        return everything.is_from_message

@dataclass
class EventOnlyFilter(BaseFilter):
    """
    # Only works on event
    """
    async def __call__(self, everything: CommonEverything) -> bool:
        return everything.is_from_event

@dataclass
class StateFilter(BaseFilter):
    """
    # Current state filter

    ## Returns
    - `True` if state user's currently on
    is equal to one defined here
    - `False` if not
    """
    state: State

    async def __call__(self, everything: CommonEverything) -> bool:
        return everything.navigator.current == self.state

@dataclass
class PayloadFilter(BaseFilter):
    """
    # Exact payload filter

    ## Returns
    - `True` if user sent a payload
    that is equal to one defined here
    - `False` if not
    """
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
class PayloadIsNotFilter(BaseFilter):
    """
    # Not exact payload filter

    ## Returns
    - `True` if user sent a payload
    that is not equal to one defined here
    - `False` if it is equal
    """
    payload: str

    async def __call__(self, everything: CommonEverything) -> bool:
        if everything.is_from_message:
            return False
        
        event = everything.event

        if event.is_from_vk:
            return event.vk['object']['payload'] != {CMD: self.payload}
        elif event.is_from_tg:
            return event.tg.data != self.payload
        
        return False

@dataclass
class UnionFilter(BaseFilter):
    """
    # Combines multiple filters

    ## Returns
    - `True` - if ANY filter was positive
    - `False` - if no filters were successful
    """
    filters: tuple[BaseFilter]

    async def __call__(self, everything: CommonEverything) -> bool:
        filter_results: list[bool] = []

        for filter_ in self.filters:
            result = await filter_(everything)
            filter_results.append(result)
        
        return any(filter_results)
