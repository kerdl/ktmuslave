from loguru import logger
import re

from src import defs
from src.api.schedule import SCHEDULE_API
from src.parse import pattern
from src.svc.common import CommonEverything, messages
from src.svc.common.bps import zoom as zoom_bp
from src.data import zoom as zoom_data
from src.svc.common.states import formatter as states_fmt, Space
from src.svc.common.states.tree import INIT, ZOOM, SETTINGS, RESET, HUB
from src.svc.common.router import r
from src.svc.common.filters import PayloadFilter, StateFilter, UnionFilter
from src.svc.common.keyboard import Keyboard, Payload
from src.svc.common import keyboard as kb


""" RESET ACTIONS """

@r.on_callback(
    StateFilter(RESET.I_MAIN), 
    PayloadFilter(Payload.RESET)
)
async def confirm_reset(everything: CommonEverything):
    await defs.ctx.delete(everything.ctx.db_key)
    everything.del_ctx()
    return await r.choose_handler(everything)

""" RESET STATE """

async def reset(everything: CommonEverything):
    answer_text = (
        messages.Builder()
            .add(messages.format_reset_explain())
    )
    answer_keyboard = Keyboard([
        [kb.RESET_BUTTON]
    ])

    await everything.edit_or_answer(
        text=answer_text.make(),
        keyboard=answer_keyboard
    )

@r.on_callback(
    StateFilter(SETTINGS.I_MAIN), 
    PayloadFilter(Payload.RESET)
)
async def to_reset(everything: CommonEverything):
    everything.navigator.append(RESET.I_MAIN)
    return await reset(everything)