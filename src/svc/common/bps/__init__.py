from typing import Any, Awaitable, Callable, Coroutine, Optional, Union
from types import ModuleType
from aiogram.exceptions import TelegramBadRequest

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
    from . import init, hub, zoom

    MAP = {
        Space.INIT: init,
        Space.HUB:  hub,
        Space.ZOOM: zoom,
    }

    return MAP.get(space)


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
