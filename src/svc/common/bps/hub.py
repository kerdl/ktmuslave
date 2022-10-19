from loguru import logger
import re

from src import defs
from src.parse import pattern
from src.svc.common import CommonEverything, messages
from src.svc.common.bps import zoom as zoom_bp
from src.data import zoom as zoom_data
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import Init, Zoom, Hub
from src.svc.common.router import r
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
    MANUALLY_BUTTON,
    NEXT_ZOOM_BUTTON,
    FINISH_BUTTON,
    UPDATE_BUTTON,
    SETTINGS_BUTTON
)


async def hub(everything: CommonEverything):
    answer_text = (
        messages.Builder()
                .add("hub")
    )
    answer_keyboard = Keyboard([
        [UPDATE_BUTTON],
        [SETTINGS_BUTTON]
    ], add_back = False)

    return await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard
    )

async def to_hub(everything: CommonEverything):
    everything.navigator.clear()
    everything.navigator.append(Hub.I_MAIN)

    everything.navigator.auto_ignored()

    return await hub(everything)


STATE_MAP = {
    Hub.I_MAIN: hub,
}