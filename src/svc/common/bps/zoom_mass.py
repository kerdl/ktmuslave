from loguru import logger

from src import defs
from src.parse import pattern
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
from src.data import zoom

@r.on_everything(StateFilter(ZoomMass.I_MAIN))
async def main(everything: CommonEverything):

    answer_keyboard = Keyboard([
        [BACK_BUTTON]
    ])

    if everything.is_from_event:
        # user came to this state from button

        event = everything.event
        mention = ""
        footer_addition = ""

        if everything.is_group_chat:
            if everything.is_from_vk:
                mention = defs.vk_bot_mention
                footer_addition = messages.format_mention_me(mention)
            elif everything.is_from_tg:
                footer_addition = messages.format_reply_to_me()

        answer_text = (
            messages.Builder(everything=everything)
                    .add(states_fmt.tree(everything.navigator, ))
                    .add(messages.format_send_zoom_data(everything.src, everything.is_group_chat))
                    .add(messages.format_zoom_data_format())
                    .add_if(footer_addition, everything.is_group_chat)
        )

        await event.edit_message(
            text     = answer_text.make(),
            keyboard = answer_keyboard
        )

    elif everything.is_from_message:
        # user sent a message with links
        
        message = everything.message

        parsed = zoom.Data.parse(message.text)

        await message.answer(
            text     = str(parsed),
            keyboard = answer_keyboard
        )

async def to_main(everything: CommonEverything):
    everything.navigator.append(ZoomMass.I_MAIN)

    return await main(everything)

STATE_MAP = {
    ZoomMass.I_MAIN: main
}