from loguru import logger
import re

from src import defs
from src.conv import pattern
from src.svc.common import CommonEverything, messages
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import Init
from src.svc.common.router import r
from src.svc.common.filter import PayloadFilter, StateFilter, UnionFilter
from src.svc.common.keyboard import (
    Keyboard, 
    Payload,
    TRUE_BUTTON,
    FALSE_BUTTON,
    SKIP_BUTTON,
    BACK_BUTTON,

    BEGIN_BUTTON,
    DO_PIN_BUTTON,
    FINISH_BUTTON
)


GROUPS = ["1кдд69", "соси", "губой", "тряси"]



@r.on_everything(StateFilter(Init.I_FINISH))
async def finish(everything: CommonEverything):
    answer_text = (
        messages.Builder(everything=everything)
                .add(states_fmt.tree(everything.navigator.trace))
                .add(messages.format_finish())
    )
    answer_keyboard = Keyboard([
        [BACK_BUTTON, FINISH_BUTTON]
    ])


    await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard
    )


async def to_finish(everything: CommonEverything):
    everything.navigator.append(Init.I_FINISH)

    return await finish(everything)


@r.on_callback(StateFilter(Init.II_SHOULD_PIN), PayloadFilter(Payload.DO_PIN))
async def check_do_pin(everything: CommonEverything):

    if not await everything.can_pin():
        answer_text = messages.format_cant_pin(everything.src)

        if everything.is_from_event:
            event = everything.event
            await event.show_notification(answer_text)

    else:
        everything.navigator.back()
        return await to_finish(everything)


@r.on_callback(StateFilter(Init.II_SHOULD_PIN), PayloadFilter(Payload.SKIP))
async def skip_pin(everything: CommonEverything):
    everything.navigator.back()
    return await to_finish(everything)


@r.on_callback(StateFilter(Init.II_SHOULD_PIN), PayloadFilter(Payload.FALSE))
async def deny_pin(everything: CommonEverything):
    everything.navigator.back()
    return await to_finish(everything)


@r.on_callback(StateFilter(Init.II_SHOULD_PIN), PayloadFilter(Payload.TRUE))
async def approve_pin(everything: CommonEverything):
    #everything.navigator.back()
    return await to_finish(everything)


@r.on_everything(StateFilter(Init.II_SHOULD_PIN))
async def should_pin(everything: CommonEverything):
    answer_text = (
        messages.Builder(everything=everything)
                .add(states_fmt.tree(everything.navigator.trace))
    )

    # if we can pin messages
    if await everything.can_pin():
        # make a keyboard where we ask if
        # we should pin (TRUE) or not (FALSE)
        answer_keyboard = Keyboard([
            [TRUE_BUTTON, FALSE_BUTTON],
            [BACK_BUTTON]
        ])
        # simply ask if user wants to pin
        answer_text.add(messages.format_do_pin())

    else:
        # we're not allowed to pin yet,
        # make a keyboard where user
        # can retry after he gives us permission,
        # or skip if he doesn't want to pin
        answer_keyboard = Keyboard([
            [DO_PIN_BUTTON, SKIP_BUTTON],
            [BACK_BUTTON]
        ])
        # make recommendation messages
        answer_text.add(messages.format_recommend_pin())
        answer_text.add(messages.format_permit_pin(everything.src))

        # if message was from telegram,
        # giving admin rights to bots
        # will migrate "group" chat type to "supergroup",
        # warn about it
        if everything.is_from_tg and everything.is_tg_group:
            answer_text.add(messages.format_chat_will_migrate())


    await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard
    )


async def to_should_pin(everything: CommonEverything):
    everything.navigator.append(Init.II_SHOULD_PIN)

    return await should_pin(everything)


@r.on_callback(StateFilter(Init.I_SCHEDULE_BROADCAST), PayloadFilter(Payload.FALSE))
async def deny_broadcast(everything: CommonEverything):
    return await to_finish(everything)


@r.on_callback(StateFilter(Init.I_SCHEDULE_BROADCAST), PayloadFilter(Payload.TRUE))
async def approve_broadcast(everything: CommonEverything):
    if everything.is_group_chat:
        return await to_should_pin(everything)
    
    return await to_finish(everything)


@r.on_everything(StateFilter(Init.I_SCHEDULE_BROADCAST))
async def schedule_broadcast(everything: CommonEverything):
    answer_text = (
        messages.Builder(everything=everything)
                .add(states_fmt.tree(everything.navigator.trace))
                .add(messages.format_schedule_broadcast())
    )
    answer_keyboard = Keyboard([
        [TRUE_BUTTON, FALSE_BUTTON],
        [BACK_BUTTON]
    ])


    await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard
    )


async def to_schedule_broadcast(everything: CommonEverything):
    if everything.navigator.current == Init.II_UNKNOWN_GROUP:
        everything.navigator.back()

    everything.navigator.append(Init.I_SCHEDULE_BROADCAST)

    return await schedule_broadcast(everything)


@r.on_callback(StateFilter(Init.II_UNKNOWN_GROUP), PayloadFilter(Payload.TRUE))
async def confirm_unknown_group(everything: CommonEverything):
    everything.navigator.back()
    
    return await to_schedule_broadcast(everything)


async def unknown_group(everything: CommonEverything, group: str):

    if everything.is_from_message:
        message = everything.message

        answer_text = (
            messages.Builder(everything=everything)
                    .add(states_fmt.tree(everything.navigator.trace))
                    .add(messages.format_unknown_group(group))
        )

        answer_keyboard = Keyboard([
            [TRUE_BUTTON],
            [BACK_BUTTON]
        ])


        await message.answer(
            text     = answer_text.make(),
            keyboard = answer_keyboard
        )


async def to_unknown_group(everything: CommonEverything, group: str):
    everything.navigator.append(Init.II_UNKNOWN_GROUP)

    return await unknown_group(everything, group)


@r.on_everything(UnionFilter([
    StateFilter(Init.I_GROUP), 
    StateFilter(Init.II_UNKNOWN_GROUP)
]))
async def group(everything: CommonEverything):

    if everything.navigator.current == Init.II_UNKNOWN_GROUP:
        everything.navigator.back()

    footer_addition = ""

    if everything.is_group_chat:
        if everything.is_from_vk:
            footer_addition = messages.format_mention_me("@pizda")

        elif everything.is_from_tg:
            footer_addition = messages.format_reply_to_me()
    
    answer_keyboard = Keyboard([
        [BACK_BUTTON]
    ])


    if everything.is_from_message:
        # most likely user sent a group in his message
        message = everything.message

        # search group regex in user's message text
        group_match = pattern.group.search(message.text)

        # if no group in text
        if group_match is None:

            # send a message saying "your input is invalid"
            answer_text = (
                messages.Builder(everything=everything)
                        .add(states_fmt.tree(everything.navigator.trace))
                        .add(messages.format_groups(GROUPS))
                        .add(messages.format_invalid_group())
                        .add(footer_addition)
            )
            await message.answer(
                text           = answer_text.make(),
                keyboard       = answer_keyboard,
            )

        # else if this group not in list of all available groups
        elif group_match.group() not in GROUPS:
            # ask if we should still set this unknown group
            return await to_unknown_group(everything, group_match.group())

        else:
            # everything is ok, proceed to the next state
            return await to_schedule_broadcast(everything)

    elif everything.is_from_event:
        # user proceeded to this state from callback button "begin"
        event = everything.event

        answer_text = (
            messages.Builder(everything=everything)
                    .add(states_fmt.tree(everything.navigator.trace))
                    .add(messages.format_groups(GROUPS))
                    .add(messages.format_group_input())
                    .add(footer_addition)
        )
        await event.edit_message(
            text           = answer_text.make(),
            keyboard       = answer_keyboard,
        )


@r.on_callback(StateFilter(Init.I_MAIN), PayloadFilter(Payload.BEGIN))
async def begin(everything: CommonEverything):
    everything.navigator.append(Init.I_GROUP)

    return await group(everything)


@r.on_everything(StateFilter(Init.I_MAIN))
async def main(everything: CommonEverything):
    answer_text = (
        messages.Builder(everything=everything)
                .add(messages.format_welcome(everything.is_group_chat))
                .add(messages.format_press_begin())
    )
    answer_keyboard = Keyboard([
        [BEGIN_BUTTON]
    ])


    await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard
    )


STATE_MAP = {
    Init.I_MAIN: main,
    Init.I_GROUP: group,
    Init.II_UNKNOWN_GROUP: unknown_group,
    Init.I_SCHEDULE_BROADCAST: schedule_broadcast,
    Init.II_SHOULD_PIN: should_pin,
    Init.I_FINISH: finish
}