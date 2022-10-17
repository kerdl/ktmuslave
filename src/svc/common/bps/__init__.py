from typing import Any, Awaitable, Callable, Coroutine, Optional, Union
from types import ModuleType
from aiogram.exceptions import TelegramBadRequest

from src.svc.common import CommonEverything, Navigator
from src.svc.common.filters import PayloadFilter
from src.svc.common.keyboard import Payload
from src.svc.common.states import SPACE_LITERAL, Space, State
from src.svc.common.router import r


class SpaceType(ModuleType):
    STATE_MAP: dict[State, Callable[[CommonEverything], Any]]
    page_back: Callable[[CommonEverything], Awaitable[None]]
    page_next: Callable[[CommonEverything], Awaitable[None]]


def get_module_space(space: SPACE_LITERAL) -> Optional[SpaceType]:
    from . import init, settings, hub, zoom

    MAP = {
        Space.INIT:     init,
        Space.SETTINGS: settings,
        Space.HUB:      hub,
        Space.ZOOM:     zoom,
    }

    return MAP.get(space)

def choose_handler(space_module: SpaceType, state: State):
    return space_module.STATE_MAP.get(state)

async def auto_execute(everything: CommonEverything):
    ctx = everything.ctx

    space = get_module_space(ctx.navigator.space)
    handler = choose_handler(space, ctx.navigator.current)

    return await handler(everything)


@r.on_callback(PayloadFilter(Payload.PAGE_BACK))
async def page_back(everything: CommonEverything):
    ctx = everything.ctx

    if ctx.pages.current_num > 0:
        ctx.pages.current_num -= 1

    answer_text = ctx.pages.current.text
    answer_keyboard = ctx.pages.current.keyboard

    try:
        return await everything.edit_or_answer(
            text        = answer_text,
            keyboard    = answer_keyboard,
            add_tree    = ctx.last_bot_message.add_tree,
            tree_values = ctx.last_bot_message.tree_values,
        )
    except TelegramBadRequest:
        pass

@r.on_callback(PayloadFilter(Payload.PAGE_NEXT))
async def page_next(everything: CommonEverything):
    ctx = everything.ctx

    if ctx.pages.current_num < len(ctx.pages.list) - 1:
        ctx.pages.current_num += 1

    answer_text = ctx.pages.current.text
    answer_keyboard = ctx.pages.current.keyboard

    try:
        return await everything.edit_or_answer(
            text        = answer_text,
            keyboard    = answer_keyboard,
            add_tree    = ctx.last_bot_message.add_tree,
            tree_values = ctx.last_bot_message.tree_values,
        )
    except TelegramBadRequest:
        pass


@r.on_callback(PayloadFilter(Payload.BACK))
async def back(everything: CommonEverything):
    everything.navigator.back()
    return await auto_execute(everything)

@r.on_callback(PayloadFilter(Payload.NEXT))
async def next(everything: CommonEverything):
    everything.navigator.next()
    return await auto_execute(everything)
