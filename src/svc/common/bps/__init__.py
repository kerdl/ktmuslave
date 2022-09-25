from src.svc.common import CommonEverything
from src.svc.common.filter import PayloadFilter
from src.svc.common.keyboard import Payload
from src.svc.common.states import Space
from src.svc.common.router import r


@r.on_callback(PayloadFilter(Payload.BACK))
async def back(everything: CommonEverything):
    from . import init, hub


    navigator = everything.navigator
    
    if navigator.space == Space.INIT:
        space = init
    elif navigator.space == Space.HUB:
        space = hub
    
    navigator.back()

    handler = space.STATE_MAP.get(navigator.current)
    return await handler(everything)

@r.on_callback(PayloadFilter(Payload.NEXT))
async def next(everything: CommonEverything):
    from . import init, hub


    navigator = everything.navigator

    if navigator.space == Space.INIT:
        space = init
    elif navigator.space == Space.HUB:
        space = hub
    
    navigator.next()

    handler = space.STATE_MAP.get(navigator.current)
    return await handler(everything)