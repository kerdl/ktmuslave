from loguru import logger

from src import defs
from src.conv import pattern
from src.svc.common import CommonEverything, messages
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import ZoomMass
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

    BEGIN_BUTTON,
    DO_PIN_BUTTON,
    FROM_TEXT_BUTTON,
    MANUALLY_BUTTON,
    FINISH_BUTTON
)

async def main(everything: CommonEverything):
    mention = ""
    mention_addition = ""


    if everything.is_group_chat:
        if everything.is_from_vk:
            mention = defs.vk_bot_mention
        elif everything.is_from_tg:
            mention = defs.tg_bot_mention
        
        mention_addition = messages.format_mention_me(mention)


    answer_text = (
        messages.Builder(everything=everything)
                .add(states_fmt.tree(everything.navigator.trace, ))
                .add(messages.format_explain_mass_zoom_add())
                .add_if(mention_addition, everything.is_group_chat)
    )
    answer_keyboard = Keyboard([
        [BACK_BUTTON]
    ])

    await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard
    )

async def to_main(everything: CommonEverything):
    everything.navigator.append(ZoomMass.I_MAIN)

    return await main(everything)

STATE_MAP = {
    ZoomMass.I_MAIN: main
}