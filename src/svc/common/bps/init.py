from loguru import logger
import re

from src import defs
from src.conv import pattern
from src.svc.common import CommonEverything, messages
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import Init
from src.svc.common.keyboard import Keyboard, Button, Payload, Color
from src.svc.common.filter import StateFilter, PayloadFilter
from src.svc.common.router import r


GROUPS = ["хуй", "соси", "губой", "тряси"]



async def finish(everything: CommonEverything):
    ...


async def should_pin(everything: CommonEverything):
    ...


async def schedule_broadcast(everything: CommonEverything):
    ...


async def to_schedule_broadcast(everything: CommonEverything):
    everything.navigator.append(Init.I_SCHEDULE_BROADCAST)

    return await schedule_broadcast(everything)


async def unknown_group(everything: CommonEverything):

    if everything.is_from_message:
        message = everything.message

        answer_message = (
            messages.Builder()
                    .add(states_fmt.tree(everything.navigator.trace))
                    .add(messages.format_unknown_group(message.text))
                    .make()
        )

        answer_keyboard = Keyboard([
            [Button("✓ ПизДА!", Payload.TRUE, Color.GREEN)],
            [Button("← Назад", Payload.BACK)]
        ])

        await message.answer(
            text     = answer_message,
            keyboard = answer_keyboard
        )

async def to_unknown_group(everything: CommonEverything):
    everything.navigator.append(Init.II_UNKNOWN_GROUP)

    return await unknown_group(everything)

@r.on_everything(StateFilter(Init.I_GROUP))
async def group(everything: CommonEverything):

    footer_addition = ""

    if everything.is_group_chat:
        if everything.is_from_vk:
            footer_addition = messages.format_mention_me("@pizda")

        elif everything.is_from_tg:
            footer_addition = messages.format_reply_to_me()
    
    answer_keyboard = Keyboard([
        [Button("← Назад", Payload.BACK)]
    ])


    if everything.is_from_message:
        # most likely user sent a group in his message
        message = everything.message

        # match group regex in user's message text
        group_match = pattern.group.match(message.text)

        # if no group in text
        if group_match is None:

            # send a message saying "your input is invalid"
            answer_text = (
                messages.Builder()
                        .add(states_fmt.tree(everything.navigator.trace))
                        .add(messages.format_groups(GROUPS))
                        .add(messages.format_invalid_group())
                        .add(footer_addition)
                        .make()
            )
            await message.answer(
                text     = answer_text,
                keyboard = answer_keyboard
            )

        # else if this group not in list of all available groups
        elif group_match.group() not in GROUPS:
            # ask if we should still set this unknown group
            return await to_unknown_group(everything)

        else:
            # everything is ok, proceed to the next state
            return await to_schedule_broadcast(everything)

    elif everything.is_from_event:
        # user proceeded to this state from callback button "begin"
        event = everything.event

        answer_text = (
            messages.Builder()
                    .add(states_fmt.tree(everything.navigator.trace))
                    .add(messages.format_groups(GROUPS))
                    .add(messages.format_group_input())
                    .add(footer_addition)
                    .make()
        )
        await event.edit_message(
            text     = answer_text,
            keyboard = answer_keyboard
        )


@r.on_callback(StateFilter(Init.I_MAIN), PayloadFilter(Payload.BEGIN))
async def begin(everything: CommonEverything):
    everything.navigator.append(Init.I_GROUP)

    return await group(everything)


@r.on_everything(StateFilter(Init.I_MAIN))
async def main(everything: CommonEverything):
    answer_message = (
        messages.Builder()
                .add(messages.format_welcome(everything.is_group_chat))
                .add(messages.format_press_begin())
                .make()
    )
    answer_keyboard = Keyboard([
        [Button("→ Начать", Payload.BEGIN)]
    ])

    if everything.is_from_message:
        message = everything.message

        await message.answer(
            text     = answer_message,
            keyboard = answer_keyboard,
        )
    
    elif everything.is_from_event:
        event = everything.event

        await event.edit_message(
            text     = answer_message,
            keyboard = answer_keyboard,
        )


STATE_MAP = {
    Init.I_MAIN: main,
    Init.I_GROUP: group,
    Init.II_UNKNOWN_GROUP: unknown_group,
    Init.I_SCHEDULE_BROADCAST: schedule_broadcast,
    Init.II_SHOULD_PIN: should_pin,
    Init.I_FINISH: finish
}