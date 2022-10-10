from typing import Any, Awaitable, Callable, Coroutine, Optional, Union
from types import ModuleType

from src.svc.common import CommonEverything
from src.svc.common.filter import PayloadFilter
from src.svc.common.keyboard import Payload
from src.svc.common.states import SPACE_LITERAL, Space, State
from src.svc.common.router import r


class SpaceType(ModuleType):
    STATE_MAP: dict[State, Callable[[CommonEverything], Any]]
    page_back: Callable[[CommonEverything], Awaitable[None]]
    page_next: Callable[[CommonEverything], Awaitable[None]]

def get_module_space(space: SPACE_LITERAL) -> Optional[SpaceType]:
    from . import init, hub, zoom_mass, zoom_browse, zoom_edit

    MAP = {
        Space.INIT:        init,
        Space.HUB:         hub,
        Space.ZOOM_MASS:   zoom_mass,
        Space.ZOOM_BROWSE: zoom_browse,
        Space.ZOOM_EDIT:   zoom_edit
    }

    return MAP.get(space)


@r.on_callback(PayloadFilter(Payload.PAGE_BACK))
async def page_back(everything: CommonEverything):
    navigator = everything.navigator

    space = get_module_space(navigator.space)

    await space.page_back(everything)


@r.on_callback(PayloadFilter(Payload.PAGE_NEXT))
async def page_next(everything: CommonEverything):
    navigator = everything.navigator

    space = get_module_space(navigator.space)

    await space.page_next(everything)


@r.on_callback(PayloadFilter(Payload.BACK))
async def back(everything: CommonEverything):
    navigator = everything.navigator
    navigator.back()

    space = get_module_space(navigator.space)

    handler = space.STATE_MAP.get(navigator.current)
    return await handler(everything)


@r.on_callback(PayloadFilter(Payload.NEXT))
async def next(everything: CommonEverything):
    navigator = everything.navigator
    navigator.next()

    space = get_module_space(navigator.space)

    handler = space.STATE_MAP.get(navigator.current)
    return await handler(everything)
