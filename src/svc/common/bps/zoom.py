from loguru import logger
from aiogram.exceptions import TelegramBadRequest

from src import defs
from src.parse import pattern
from src.svc.common import CommonEverything, messages, pagination
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import Zoom
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



@r.on_callback(StateFilter(Zoom.II_BROWSE), PayloadFilter(Payload.ADD_ALL))
async def mass_check(everything: CommonEverything):
    return await to_entry(everything)


async def pwd(everything: CommonEverything):
    ...


async def id_(everything: CommonEverything):
    ...


async def url(everything: CommonEverything):
    ...


async def name(everything: CommonEverything):
    ...


async def entry(everything: CommonEverything):
    answer_text = (
        messages.Builder()
                .add("пососи жопу пока что пупс")
    )
    answer_keyboard = Keyboard.default()

    await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard
    )

async def to_entry(everything: CommonEverything):
    everything.navigator.append(Zoom.III_ENTRY)
    return await entry(everything)


@r.on_callback(StateFilter(Zoom.II_BROWSE))
async def browse(everything: CommonEverything):
    ctx = everything.ctx

    if everything.is_from_event:
        # user selected an entry in list
        event = everything.event
        payload = event.payload

        in_zoom_entries = ctx.settings.zoom.has_in_entries(payload)
        in_zoom_new_entries = ctx.settings.zoom.has_in_new_entries(payload)

        related_to_entry = in_zoom_entries or in_zoom_new_entries

        if related_to_entry:
            return await to_entry(everything)

    if Zoom.I_MASS in ctx.navigator.trace:
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

async def to_browse(everything: CommonEverything):
    everything.navigator.append(Zoom.II_BROWSE)
    return await browse(everything)


@r.on_everything(StateFilter(Zoom.I_MASS))
async def mass(everything: CommonEverything):
    ctx = everything.ctx

    if everything.is_from_event:
        # user came to this state from button
        event = everything.event

        footer_addition = messages.default_footer_addition(everything)
        has_new_entries = ctx.settings.zoom.has_new_entries

        answer_text = (
            messages.Builder()
                    .add(messages.format_zoom_data_format())
                    .add(messages.format_send_zoom_data(everything.src, everything.is_group_chat))
                    .add(footer_addition)
        )
        answer_keyboard = Keyboard.default().assign_next(NEXT_BUTTON.only_if(has_new_entries))

        await event.edit_message(
            text        = answer_text.make(),
            keyboard    = answer_keyboard,
        )

    elif everything.is_from_message:
        # user sent a message with links
        message = everything.message

        # parse from text
        parsed = zoom.Data.parse(message.text)

        # if no data found in text
        if len(parsed) < 1:

            footer_addition = messages.default_footer_addition(everything)

            answer_text = (
                messages.Builder()
                        .add(messages.format_zoom_data_format())
                        .add(messages.format_doesnt_contain_zoom())
                        .add(footer_addition)
            )
            answer_keyboard = Keyboard.default()

            return await message.answer(
                text     = answer_text.make(),
                keyboard = answer_keyboard
            )

        # add everything parsed
        ctx.settings.zoom.add_new_entry(parsed)

        return await to_browse(everything)

async def to_mass(everything: CommonEverything):
    everything.navigator.append(Zoom.I_MASS)
    return await mass(everything)


STATE_MAP = {
    Zoom.I_MASS: mass,
    Zoom.II_BROWSE: browse,
    Zoom.III_ENTRY: entry,
    Zoom.IIII_NAME: name,
    Zoom.IIII_URL: url,
    Zoom.IIII_ID: id_,
    Zoom.IIII_PWD: pwd,
    Zoom.I_MASS_CHECK: mass_check,
}