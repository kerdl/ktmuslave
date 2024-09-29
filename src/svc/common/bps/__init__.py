from typing import Any, Awaitable, Callable, Coroutine, Optional, Union
from types import ModuleType
from aiogram.exceptions import TelegramBadRequest
from src.data import week
from src.svc.common import CommonEverything, Navigator, messages
from src.svc.common.filters import PayloadFilter
from src.svc.common.keyboard import Payload
from src.svc.common.states import SPACE_LITERAL, Space, State
from src.svc.common.states.tree import HUB
from src.svc.common.router import router


class SpaceType(ModuleType):
    STATE_MAP: dict[State, Callable[[CommonEverything], Any]]
    page_back: Callable[[CommonEverything], Awaitable[None]]
    page_next: Callable[[CommonEverything], Awaitable[None]]


def get_module_space(space: SPACE_LITERAL) -> Optional[SpaceType]:
    from . import init, settings, hub, zoom, reset

    MAP = {
        Space.INIT: init,
        Space.SETTINGS: settings,
        Space.HUB: hub,
        Space.ZOOM: zoom,
        Space.RESET: reset
    }

    return MAP.get(space)

def choose_handler(space_module: SpaceType, state: State):
    return space_module.STATE_MAP.get(state)

async def auto_execute(everything: CommonEverything):
    ctx = everything.ctx

    space = get_module_space(ctx.navigator.space)
    handler = choose_handler(space, ctx.navigator.current)

    return await handler(everything)


@router.on_callback(PayloadFilter(Payload.GO_TO_HUB))
async def to_hub(everything: CommonEverything):
    from . import hub
    return await hub.to_hub(everything, allow_edit=False)

@router.on_callback(PayloadFilter(Payload.PAGE_PREVIOUS))
async def page_previous(everything: CommonEverything):
    from . import hub
    
    ctx = everything.ctx
    is_hub_space = everything.navigator.current == HUB.I_MAIN
    is_allowed = False

    if is_hub_space:
        is_allowed = ctx.shift_week_backward()
    else:
        is_allowed = ctx.pages.current_num > 0

    if not is_allowed:
        return await everything.event.pong()

    if is_hub_space:
        return await hub.hub(
            everything=everything,
            allow_edit=ctx.last_bot_message.can_edit
        )
    else:
        ctx.pages.current_num -= 1
        
        answer_text = ctx.pages.current.text
        answer_keyboard = ctx.pages.current.keyboard
        
        return await everything.edit_or_answer(
            text=answer_text,
            keyboard=answer_keyboard,
            add_tree=ctx.last_bot_message.add_tree,
            tree_values=ctx.last_bot_message.tree_values,
        )

@router.on_callback(PayloadFilter(Payload.PAGE_NEXT))
async def page_next(everything: CommonEverything):
    from . import hub
    
    ctx = everything.ctx
    is_hub = everything.navigator.current == HUB.I_MAIN
    is_allowed = False

    if is_hub:
        is_allowed = ctx.shift_week_forward()
    else:
        is_allowed = ctx.pages.current_num < len(ctx.pages.list) - 1

    if not is_allowed:
        return await everything.event.pong()

    if is_hub:
        return await hub.hub(
            everything=everything,
            allow_edit=ctx.last_bot_message.can_edit
        )
    else:
        ctx.pages.current_num += 1
        
        answer_text = ctx.pages.current.text
        answer_keyboard = ctx.pages.current.keyboard
        
        return await everything.edit_or_answer(
            text=answer_text,
            keyboard=answer_keyboard,
            add_tree=ctx.last_bot_message.add_tree,
            tree_values=ctx.last_bot_message.tree_values,
        )

@router.on_callback(PayloadFilter(Payload.PAGE_PREVIOUS_JUMP))
async def page_jump_previous(everything: CommonEverything):
    from . import hub
    
    ctx = everything.ctx
    is_hub_space = everything.navigator.current == HUB.I_MAIN
    is_allowed = False

    if is_hub_space:
        is_allowed = ctx.jump_week_backward()
    else:
        is_allowed = ctx.pages.current_num > 0

    if not is_allowed:
        return await everything.event.pong()

    if is_hub_space:
        return await hub.hub(
            everything=everything,
            allow_edit=ctx.last_bot_message.can_edit
        )
    else:
        ctx.pages.current_num = 0
        
        answer_text = ctx.pages.current.text
        answer_keyboard = ctx.pages.current.keyboard
        
        return await everything.edit_or_answer(
            text=answer_text,
            keyboard=answer_keyboard,
            add_tree=ctx.last_bot_message.add_tree,
            tree_values=ctx.last_bot_message.tree_values,
        )

@router.on_callback(PayloadFilter(Payload.PAGE_NEXT_JUMP))
async def page_jump_next(everything: CommonEverything):
    from . import hub
    
    ctx = everything.ctx
    is_hub = everything.navigator.current == HUB.I_MAIN
    is_allowed = False

    if is_hub:
        is_allowed = ctx.jump_week_forward()
    else:
        is_allowed = ctx.pages.current_num < len(ctx.pages.list) - 1

    if not is_allowed:
        return await everything.event.pong()

    if is_hub:
        return await hub.hub(
            everything=everything,
            allow_edit=ctx.last_bot_message.can_edit
        )
    else:
        ctx.pages.current_num = len(ctx.pages.list) - 1
        
        answer_text = ctx.pages.current.text
        answer_keyboard = ctx.pages.current.keyboard
        
        return await everything.edit_or_answer(
            text=answer_text,
            keyboard=answer_keyboard,
            add_tree=ctx.last_bot_message.add_tree,
            tree_values=ctx.last_bot_message.tree_values,
        )

@router.on_callback(PayloadFilter(Payload.BACK))
async def back(everything: CommonEverything):
    everything.navigator.back()
    return await auto_execute(everything)

@router.on_callback(PayloadFilter(Payload.FORWARD))
async def next(everything: CommonEverything):
    everything.navigator.next()
    return await auto_execute(everything)
