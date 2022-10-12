from loguru import logger
from aiogram.exceptions import TelegramBadRequest

from src import defs
from src.parse import pattern
from src.svc.common import CommonEverything, messages, pagination
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import ZoomBrowse, ZoomMass
from src.svc.common.router import r
from src.svc.common.filter import PayloadFilter, StateFilter, UnionFilter
from src.svc.common.keyboard import (
    NEXT_BUTTON,
    Keyboard, 
    Payload,
    TRUE_BUTTON,
    FALSE_BUTTON,
    SKIP_BUTTON,
    BACK_BUTTON,
    ADD_BUTTON,
    ADD_ALL_BUTTON,

    BEGIN_BUTTON,
    DO_PIN_BUTTON,
    FROM_TEXT_BUTTON,
    MANUALLY_BUTTON,
    FINISH_BUTTON
)
from src.data import zoom


async def main(everything: CommonEverything):
    ctx = everything.ctx

    if everything.is_from_message:
        message = everything.message
    
    elif everything.is_from_event:
        event = everything.event

    if ZoomMass.I_MAIN in ctx.navigator.trace:
        # user came here from adding mass zoom data
        ctx.pages.list = pagination.from_zoom(
            data = ctx.settings.zoom.new_entries,
            keyboard_footer = [BACK_BUTTON, ADD_ALL_BUTTON]
        )
    else:
        # user came here from regular browser
        ctx.pages.list = pagination.from_zoom(
            data = ctx.settings.zoom.entries,
            keyboard_header = [ADD_BUTTON]
        )

    return await everything.edit_or_answer(
        text     = ctx.pages.current.text,
        keyboard = ctx.pages.current.keyboard,
    )

async def to_main(everything: CommonEverything):
    ctx = everything.ctx

    ctx.navigator.append(ZoomBrowse.I_MAIN)
    return await main(everything)


STATE_MAP = {
    ZoomBrowse.I_MAIN: main
}