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

    BEGIN_BUTTON,
    DO_PIN_BUTTON,
    FROM_TEXT_BUTTON,
    MANUALLY_BUTTON,
    FINISH_BUTTON
)
from src.data import zoom


async def page_back(everything: CommonEverything):
    ctx = everything.ctx

    pages = ctx.settings.zoom_entries.new_entries.pages
    cur_page = ctx.settings.zoom_entries.new_entries.cur_page

    if cur_page > 0:
        ctx.settings.zoom_entries.new_entries.cur_page -= 1
        cur_page = ctx.settings.zoom_entries.new_entries.cur_page

    page = pages[cur_page]

    answer_text = page.text
    answer_keyboard = page.keyboard

    try:
        return await everything.edit_or_answer(
            text     = answer_text,
            keyboard = answer_keyboard
        )
    except TelegramBadRequest:
        pass

async def page_next(everything: CommonEverything):
    ctx = everything.ctx

    pages = ctx.settings.zoom_entries.new_entries.pages
    cur_page = ctx.settings.zoom_entries.new_entries.cur_page

    if cur_page < len(pages) - 1:
        ctx.settings.zoom_entries.new_entries.cur_page += 1
        cur_page = ctx.settings.zoom_entries.new_entries.cur_page

    page = pages[cur_page]

    answer_text = page.text
    answer_keyboard = page.keyboard

    try:
        return await everything.edit_or_answer(
            text     = answer_text,
            keyboard = answer_keyboard
        )
    except TelegramBadRequest:
        pass


@r.on_everything(StateFilter(ZoomMass.I_MAIN))
async def main(everything: CommonEverything):
    ctx = everything.ctx

    mention = ""
    footer_addition = ""

    if everything.is_group_chat:
        if everything.is_from_vk:
            mention = defs.vk_bot_mention
            footer_addition = messages.format_mention_me(mention)
        elif everything.is_from_tg:
            footer_addition = messages.format_reply_to_me()

    answer_keyboard = Keyboard([
        [BACK_BUTTON]
    ])

    if everything.is_from_event:
        # user came to this state from button

        event = everything.event

        answer_text = (
            messages.Builder(everything=everything)
                    .add(states_fmt.tree(everything.navigator, ))
                    .add(messages.format_zoom_data_format())
                    .add(messages.format_send_zoom_data(everything.src, everything.is_group_chat))
                    .add_if(footer_addition, everything.is_group_chat)
        )

        await event.edit_message(
            text     = answer_text.make(),
            keyboard = answer_keyboard
        )

    elif everything.is_from_message:
        # user sent a message with links

        message = everything.message

        ctx.settings.zoom_entries = zoom.Container.default()

        parsed = zoom.Data.parse(message.text)
        ctx.settings.zoom_entries.add_new_entry(parsed)

        pages = pagination.from_zoom(parsed)
        ctx.settings.zoom_entries.new_entries.pages = pages
        ctx.settings.zoom_entries.new_entries.cur_page = 0

        cur_page = ctx.settings.zoom_entries.new_entries.cur_page
        page = ctx.settings.zoom_entries.new_entries.pages[cur_page]

        if len(parsed) < 1:
            answer_text = (
                messages.Builder(everything=everything)
                        .add(states_fmt.tree(everything.navigator, ))
                        .add(messages.format_zoom_data_format())
                        .add(messages.format_doesnt_contain_zoom())
                        .add_if(footer_addition, everything.is_group_chat)
            )
        else:
            answer_text = (
                messages.Builder(everything=everything)
                        .add(states_fmt.tree(everything.navigator, ))
                        .add(page.text)
            )
            answer_keyboard = page.keyboard

        await message.answer(
            text     = answer_text.make(),
            keyboard = answer_keyboard
        )

async def to_main(everything: CommonEverything):
    everything.navigator.append(ZoomMass.I_MAIN)

    return await main(everything)

STATE_MAP = {
    ZoomMass.I_MAIN: main
}