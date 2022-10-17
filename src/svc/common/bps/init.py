from loguru import logger
import re

from src import defs
from src.parse import pattern
from src.svc.common import CommonEverything, messages
from src.svc.common.bps import zoom as zoom_bp
from src.data import zoom as zoom_data
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import Init, Zoom
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
    FINISH_BUTTON
)


GROUPS = ["хуй", "соси", "губой", "тряси"]



@r.on_everything(StateFilter(Init.I_FINISH))
async def finish(everything: CommonEverything):
    ctx = everything.ctx

    answer_text = (
        messages.Builder()
                .add(messages.format_finish())
    )
    answer_keyboard = Keyboard.default().assign_next(FINISH_BUTTON)

    await everything.edit_or_answer(
        text        = answer_text.make(),
        keyboard    = answer_keyboard,
        add_tree    = True,
        tree_values = ctx.settings
    )


async def to_finish(everything: CommonEverything):
    everything.navigator.append(Init.I_FINISH)

    return await finish(everything)


@r.on_callback(StateFilter(Init.I_ZOOM), PayloadFilter(Payload.NEXT_ZOOM))
async def next_add_zoom(everything: CommonEverything):
    return await to_finish(everything)

@r.on_callback(StateFilter(Init.I_ZOOM), PayloadFilter(Payload.SKIP))
async def skip_add_zoom(everything: CommonEverything):
    ctx = everything.ctx

    # reset the container
    ctx.settings.zoom = zoom_data.Container.default()

    # remove back traced zoom browse state, 
    # since after container reset 
    # we can't go there with "next" button
    ctx.navigator.delete_back_trace(Zoom.II_BROWSE)

    # set this state as finished
    # (so number of added entries is shown)
    ctx.settings.zoom.finish()

    return await to_finish(everything)


@r.on_callback(StateFilter(Init.I_ZOOM), PayloadFilter(Payload.FROM_TEXT))
async def add_zoom_from_text(everything: CommonEverything):
    return await zoom_bp.to_mass(everything)


@r.on_callback(StateFilter(Init.I_ZOOM), PayloadFilter(Payload.MANUALLY))
async def add_zoom_manually(everything: CommonEverything):
    return await zoom_bp.to_browse(everything)


@r.on_everything(StateFilter(Init.I_ZOOM))
async def add_zoom(everything: CommonEverything):
    ctx = everything.ctx

    answer_text = (
        messages.Builder()
                .add(messages.format_recommend_adding_zoom())
                .add(messages.format_zoom_adding_types_explain())
    )
    answer_keyboard = Keyboard([
        [FROM_TEXT_BUTTON, MANUALLY_BUTTON],
    ]).assign_next(
        NEXT_ZOOM_BUTTON.only_if(
            ctx.settings.zoom.entries.has_something
        ) or SKIP_BUTTON
    )

    await everything.edit_or_answer(
        text        = answer_text.make(),
        keyboard    = answer_keyboard,
        add_tree    = True,
        tree_values = ctx.settings
    )

async def to_add_zoom(everything: CommonEverything):
    everything.navigator.append(Init.I_ZOOM)

    return await add_zoom(everything)


@r.on_callback(StateFilter(Init.II_SHOULD_PIN), PayloadFilter(Payload.DO_PIN))
async def check_do_pin(everything: CommonEverything):

    if not await everything.can_pin():
        answer_text = messages.format_cant_pin(everything.src)

        if everything.is_from_event:
            event = everything.event
            await event.show_notification(answer_text)

    else:
        everything.navigator.back(trace_it = False)
        return await to_finish(everything)


@r.on_callback(StateFilter(Init.II_SHOULD_PIN), PayloadFilter(Payload.SKIP))
async def skip_pin(everything: CommonEverything):

    everything.ctx.settings.should_pin = False

    return await to_add_zoom(everything)


@r.on_callback(StateFilter(Init.II_SHOULD_PIN), PayloadFilter(Payload.FALSE))
async def deny_pin(everything: CommonEverything):

    everything.ctx.settings.should_pin = False

    return await to_add_zoom(everything)


@r.on_callback(StateFilter(Init.II_SHOULD_PIN), PayloadFilter(Payload.TRUE))
async def approve_pin(everything: CommonEverything):
    
    everything.ctx.settings.should_pin = True

    return await to_add_zoom(everything)


@r.on_everything(StateFilter(Init.II_SHOULD_PIN))
async def should_pin(everything: CommonEverything):
    ctx = everything.ctx
    is_should_pin_set = everything.ctx.settings.should_pin is not None

    answer_text = (
        messages.Builder()
    )

    # if we can pin messages
    if await everything.can_pin():
        # make a keyboard where we ask if
        # we should pin (TRUE) or not (FALSE)
        answer_keyboard = Keyboard([
            [TRUE_BUTTON, FALSE_BUTTON],
        ]).assign_next(NEXT_BUTTON.only_if(is_should_pin_set))
    
        # simply ask if user wants to pin
        answer_text.add(messages.format_do_pin())

    else:
        # we're not allowed to pin yet,
        # make a keyboard where user
        # can retry after he gives us permission,
        # or skip if he doesn't want to pin
        answer_keyboard = Keyboard([
            [DO_PIN_BUTTON],
        ]).assign_next(SKIP_BUTTON)

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
        text        = answer_text.make(),
        keyboard    = answer_keyboard,
        add_tree    = True,
        tree_values = ctx.settings
    )


async def to_should_pin(everything: CommonEverything):
    everything.navigator.append(Init.II_SHOULD_PIN)

    return await should_pin(everything)


@r.on_callback(StateFilter(Init.I_SCHEDULE_BROADCAST), PayloadFilter(Payload.FALSE))
async def deny_broadcast(everything: CommonEverything):
    ctx = everything.ctx

    everything.ctx.settings.schedule_broadcast = False

    # after deny, it's impossible to
    # get to `should_pin`
    ctx.navigator.delete_back_trace(Init.II_SHOULD_PIN)

    return await to_add_zoom(everything)


@r.on_callback(StateFilter(Init.I_SCHEDULE_BROADCAST), PayloadFilter(Payload.TRUE))
async def approve_broadcast(everything: CommonEverything):

    everything.ctx.settings.schedule_broadcast = True
    
    if everything.is_group_chat:
        return await to_should_pin(everything)
    
    return await to_add_zoom(everything)


@r.on_everything(StateFilter(Init.I_SCHEDULE_BROADCAST))
async def schedule_broadcast(everything: CommonEverything):
    ctx = everything.ctx
    is_schedule_broadcast_set = everything.ctx.settings.schedule_broadcast is not None

    answer_text = (
        messages.Builder()
                .add(messages.format_schedule_broadcast())
    )
    answer_keyboard = Keyboard([
        [TRUE_BUTTON, FALSE_BUTTON],
    ]).assign_next(NEXT_BUTTON.only_if(is_schedule_broadcast_set))


    await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard,
        add_tree    = True,
        tree_values = ctx.settings
    )


async def to_schedule_broadcast(everything: CommonEverything):
    everything.navigator.jump_back_to_or_append(Init.I_GROUP)

    everything.navigator.append(Init.I_SCHEDULE_BROADCAST)

    return await schedule_broadcast(everything)


@r.on_callback(StateFilter(Init.II_UNKNOWN_GROUP), PayloadFilter(Payload.TRUE))
async def confirm_unknown_group(everything: CommonEverything):
    # get valid group
    valid_group = everything.ctx.settings.group.valid

    # set it as confirmed
    everything.ctx.settings.group.confirmed = valid_group

    everything.navigator.back(trace_it = False)
    
    return await to_schedule_broadcast(everything)


async def unknown_group(everything: CommonEverything):
    ctx = everything.ctx
    group = everything.ctx.settings.group.valid

    if everything.is_from_message:
        message = everything.message

        answer_text = (
            messages.Builder()
                    .add(messages.format_unknown_group(group))
        )

        answer_keyboard = Keyboard([
            [TRUE_BUTTON],
        ])


        await message.answer(
            text     = answer_text.make(),
            keyboard = answer_keyboard,
            add_tree    = True,
            tree_values = ctx.settings
        )


async def to_unknown_group(everything: CommonEverything):
    everything.navigator.append(Init.II_UNKNOWN_GROUP)

    return await unknown_group(everything)


@r.on_everything(UnionFilter([
    StateFilter(Init.I_GROUP), 
    StateFilter(Init.II_UNKNOWN_GROUP)
]))
async def group(everything: CommonEverything):
    ctx = everything.ctx
    is_group_set = ctx.settings.group.confirmed is not None

    everything.navigator.jump_back_to_or_append(Init.I_GROUP)

    footer_addition = ""


    if (everything.is_group_chat and everything.is_from_vk):
        if await everything.vk_has_admin_rights():
            footer_addition = messages.format_reply_to_me()
        else:
            footer_addition = messages.format_mention_me(defs.vk_bot_mention)

    elif (everything.is_group_chat and everything.is_from_tg):
        footer_addition = messages.format_reply_to_me()
    
    answer_keyboard = Keyboard.default().assign_next(NEXT_BUTTON.only_if(is_group_set))


    if everything.is_from_message:
        # most likely user sent a group in his message
        message = everything.message

        # search group regex in user's message text
        group_match = pattern.GROUP.search(message.text)

        # if no group in text
        if group_match is None:

            # send a message saying "your input is invalid"
            answer_text = (
                messages.Builder()
                        .add(messages.format_groups(GROUPS))
                        .add(messages.format_invalid_group())
                        .add(footer_addition)
            )
            return await message.answer(
                text        = answer_text.make(),
                keyboard    = answer_keyboard,
                add_tree    = True,
                tree_values = ctx.settings
            )


        ## add user's group to context as typed group ##
        ctx.settings.group.typed = group_match.group()
        ################################################


        # remove nonword from group (separators like "-")
        group_nonword = pattern.NON_LETTER.sub("", group_match.group())

        # make group all caps
        group_caps = group_nonword.upper()


        ## add validated group to context as valid group ##
        ctx.settings.group.valid = group_caps
        ###################################################


        # if this group not in list of all available groups
        if group_caps not in GROUPS:
            # ask if we should still set this unknown group
            return await to_unknown_group(everything)


        # everything is ok, set this group as confirmed
        everything.ctx.settings.group.confirmed = group_caps

        # proceed to the next state
        return await to_schedule_broadcast(everything)

    elif everything.is_from_event:
        # user proceeded to this state from callback button "begin"
        event = everything.event

        answer_text = (
            messages.Builder()
                    .add(messages.format_groups(GROUPS))
                    .add(messages.format_group_input())
                    .add(footer_addition)
        )
        await event.edit_message(
            text           = answer_text.make(),
            keyboard       = answer_keyboard,
            add_tree    = True,
            tree_values = ctx.settings
        )


@r.on_callback(StateFilter(Init.I_MAIN), PayloadFilter(Payload.BEGIN))
async def begin(everything: CommonEverything):
    everything.navigator.append(Init.I_GROUP)

    return await group(everything)


@r.on_everything(StateFilter(Init.I_MAIN))
async def main(everything: CommonEverything):
    answer_text = (
        messages.Builder()
                .add(messages.format_welcome(everything.is_group_chat))
                .add(messages.format_press_begin())
    )
    answer_keyboard = Keyboard([
        [BEGIN_BUTTON]
    ], add_back=False)


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
    Init.I_ZOOM: add_zoom,
    Init.I_FINISH: finish
}