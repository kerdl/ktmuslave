from loguru import logger
from aiogram.exceptions import TelegramBadRequest

from src import defs
from src.parse import pattern
from src.svc.common import CommonEverything, messages, pagination
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
    ADD_BUTTON,
    ADD_ALL_BUTTON,

    BEGIN_BUTTON,
    DO_PIN_BUTTON,
    FROM_TEXT_BUTTON,
    MANUALLY_BUTTON,
    FINISH_BUTTON
)
from src.data import zoom
from . import zoom_browse


async def edit(everything: CommonEverything):
    ctx = everything.ctx

    footer_addition = messages.default_footer_addition(everything)


    if everything.is_from_message:
        # user sent a message with links

        message = everything.message

        ctx.settings.zoom = zoom.Container.default()

        parsed = zoom.Data.parse(message.text)
        ctx.settings.zoom.add_new_entry(parsed)

        pages = pagination.from_zoom(
            data            = parsed,
            keyboard_footer = [BACK_BUTTON, ADD_ALL_BUTTON]
        )
        ctx.pages.list = pages

    if not ctx.settings.zoom.has_new_entries:
        answer_text = (
            messages.Builder(everything=everything)
                    .add(messages.format_zoom_data_format())
                    .add(messages.format_doesnt_contain_zoom())
                    .add_if(footer_addition, everything.is_group_chat)
        )
        answer_keyboard = Keyboard.default()
    else:
        answer_text = (
            messages.Builder(everything=everything)
                    .add(ctx.pages.current.text)
        )
        answer_keyboard = ctx.pages.current.keyboard
    
    await everything.edit_or_answer(
        text        = answer_text.make(),
        keyboard    = answer_keyboard,
        add_tree    = True,
        tree_values = ctx.settings
    )

@r.on_everything(StateFilter(ZoomMass.I_MAIN))
async def main(everything: CommonEverything):
    ctx = everything.ctx

    if everything.is_from_event:
        # user came to this state from button
        event = everything.event

        footer_addition = messages.default_footer_addition(everything)
        has_new_entries = ctx.settings.zoom.has_new_entries

        answer_text = (
            messages.Builder(everything=everything)
                    .add(messages.format_zoom_data_format())
                    .add(messages.format_send_zoom_data(everything.src, everything.is_group_chat))
                    .add_if(footer_addition, everything.is_group_chat)
        )
        answer_keyboard = Keyboard.default().assign_next(NEXT_BUTTON.only_if(has_new_entries))

        await event.edit_message(
            text        = answer_text.make(),
            keyboard    = answer_keyboard,
            add_tree    = True,
            tree_values = ctx.settings
        )

    elif everything.is_from_message:
        # user sent a message with links
        message = everything.message

        # parse from text
        parsed = zoom.Data.parse(message.text)

        # add everything parsed
        ctx.settings.zoom.add_new_entry(parsed)

        return await zoom_browse.main(everything)


async def to_main(everything: CommonEverything):
    everything.navigator.append(ZoomMass.I_MAIN)

    return await main(everything)

STATE_MAP = {
    ZoomMass.I_MAIN: main,
}