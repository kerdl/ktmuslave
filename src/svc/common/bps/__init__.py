from src.svc.common import CommonEverything
from src.svc.common.states import Space
from . import init, hub


async def back(everything: CommonEverything):
    navigator = everything.navigator
    
    if navigator.space == Space.INIT:
        space = init
    elif navigator.space == Space.HUB:
        space = hub
    
    navigator.back()

    handler = space.STATE_MAP.get(navigator.current)
    return await handler(everything)