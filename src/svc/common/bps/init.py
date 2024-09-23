from loguru import logger
import re

from src import defs
from src.parse import pattern
from src.svc.common import CommonEverything, messages
from src.svc.common.bps import zoom as zoom_bp, hub as hub_bp
from src.data import zoom as zoom_data
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import INIT, ZOOM, SETTINGS
from src.svc.common.router import router
from src.svc.common.filters import PayloadFilter, StateFilter, UnionFilter
from src.svc.common.keyboard import (
    NEXT_BUTTON,
    Keyboard,
    Payload,
    TRUE_BUTTON,
    FALSE_BUTTON,
    SKIP_BUTTON,
    BACK_BUTTON,

    BEGIN_BUTTON,
    DO_PIN_BUTTON,
    FROM_TEXT_BUTTON,
    MANUALLY_INIT_BUTTON,
    NEXT_ZOOM_BUTTON,
    FINISH_BUTTON
)


@router.on_callback(
    StateFilter(INIT.I_FINISH),
    PayloadFilter(Payload.FINISH)
)
async def to_hub(everything: CommonEverything):
    ctx = everything.ctx

    ctx.register()

    return await hub_bp.to_hub(everything)


@router.on_everything(StateFilter(INIT.I_FINISH))
async def finish(everything: CommonEverything):
    ctx = everything.ctx

    answer_text = (
        messages.Builder()
                .add(messages.format_finish())
    )
    answer_keyboard = Keyboard().assign_next(FINISH_BUTTON)

    await everything.edit_or_answer(
        text        = answer_text.make(),
        keyboard    = answer_keyboard,
    )


async def to_finish(everything: CommonEverything):
    everything.navigator.append(INIT.I_FINISH)

    return await finish(everything)


@router.on_everything(StateFilter(INIT.I_MAIN))
async def main(everything: CommonEverything, force_send: bool = False):
    answer_text = (
        messages.Builder()
            .add(messages.format_welcome(everything.is_group_chat))
            .add(messages.format_press_begin())
    )
    answer_keyboard = Keyboard([
        [BEGIN_BUTTON]
    ], add_back=False)


    if force_send:
        return await everything.answer(
            text     = answer_text.make(),
            keyboard = answer_keyboard
        )
    else:
        return await everything.edit_or_answer(
            text     = answer_text.make(),
            keyboard = answer_keyboard
        )


STATE_MAP = {
    INIT.I_MAIN: main,
    INIT.I_FINISH: finish
}
