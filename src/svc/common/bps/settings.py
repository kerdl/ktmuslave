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


async def auto_route(everything: CommonEverything):
    ctx = everything.ctx

    previous_space = ctx.navigator.previous_space
    current_state = ctx.navigator.current

    if SETTINGS.I_MAIN in ctx.navigator.trace:
        ctx.navigator.jump_back_to(SETTINGS.I_MAIN)

        return await main(everything)

    if previous_space != Space.INIT:
        return None


    if current_state in [SETTINGS.II_GROUP, SETTINGS.III_UNKNOWN_GROUP]:
        return await to_broadcast(everything)
    
    if (
        current_state == SETTINGS.II_BROADCAST 
        and ctx.settings.broadcast 
        and everything.is_group_chat
    ):
        return await to_should_pin(everything)
    
    if current_state in [SETTINGS.II_BROADCAST, SETTINGS.III_SHOULD_PIN]:
        return await to_add_zoom(everything)
    
    if current_state in [SETTINGS.II_ZOOM]:
        from src.svc.common.bps import init
        return await init.to_finish(everything)


""" ZOOM ACTIONS """

@r.on_callback(
    StateFilter(SETTINGS.II_ZOOM), 
    PayloadFilter(Payload.NEXT_ZOOM)
)
async def next_add_zoom(everything: CommonEverything):
    return await auto_route(everything)

@r.on_callback(
    StateFilter(SETTINGS.II_ZOOM), 
    PayloadFilter(Payload.SKIP)
)
async def skip_add_zoom(everything: CommonEverything):
    ctx = everything.ctx

    # reset the container
    ctx.settings.zoom = zoom_data.Container()

    # remove back traced zoom browse state, 
    # since after container reset 
    # we can't go there with "next" button
    ctx.navigator.delete_back_trace(ZOOM.II_BROWSE)

    # set this state as finished
    # (so number of added entries is shown)
    ctx.settings.zoom.finish()

    return await auto_route(everything)

@r.on_callback(
    StateFilter(SETTINGS.II_ZOOM), 
    PayloadFilter(Payload.MANUALLY_HUB)
)
async def add_zoom_manually_hub(everything: CommonEverything):
    return await zoom_bp.to_name(everything)

@r.on_callback(
    StateFilter(SETTINGS.II_ZOOM), 
    PayloadFilter(Payload.FROM_TEXT)
)
async def add_zoom_from_text(everything: CommonEverything):
    return await zoom_bp.to_mass(everything)


@r.on_callback(
    StateFilter(ZOOM.I_MASS), 
    PayloadFilter(Payload.CONTINUE)
)
async def continue_mass_adding(everything: CommonEverything):
    return await zoom_bp.to_browse(everything)


@r.on_callback(
    StateFilter(SETTINGS.II_ZOOM), 
    PayloadFilter(Payload.MANUALLY_INIT)
)
async def add_zoom_manually(everything: CommonEverything):
    return await zoom_bp.to_browse(everything)



""" ZOOM STATE """

@r.on_everything(StateFilter(SETTINGS.II_ZOOM))
async def add_zoom(everything: CommonEverything):
    ctx = everything.ctx

    is_from_init = Space.INIT in ctx.navigator.spaces
    is_from_hub  = Space.HUB in ctx.navigator.spaces

    adding_types = ""

    if is_from_init:
        adding_types = "\n".join([
            messages.format_zoom_add_from_text_explain(),
            messages.format_zoom_add_manually_init_explain()
        ])
    elif is_from_hub:
        adding_types = "\n".join([
            messages.format_zoom_add_from_text_explain(),
            messages.format_zoom_add_manually_hub_explain()
        ])

    answer_text = (
        messages.Builder()
            .add_if(messages.format_recommend_adding_zoom(), is_from_init)
            .add_if(messages.format_choose_adding_type(), is_from_hub)
            .add(adding_types)
    )
    answer_keyboard = Keyboard([
        [
            kb.FROM_TEXT_BUTTON,
            kb.MANUALLY_INIT_BUTTON.only_if(is_from_init),
            kb.MANUALLY_HUB_BUTTON.only_if(is_from_hub)
        ],
    ])

    if not is_from_hub:
        answer_keyboard.assign_next(
            kb.NEXT_ZOOM_BUTTON.only_if(
                ctx.settings.zoom.is_finished
            ) or kb.SKIP_BUTTON
        )

    await everything.edit_or_answer(
        text        = answer_text.make(),
        keyboard    = answer_keyboard,
        add_tree    = not is_from_hub,
        tree_values = ctx.settings
    )

@r.on_callback(
    PayloadFilter(Payload.ADD_HUB),
    StateFilter(ZOOM.II_BROWSE)
)
async def to_add_zoom(everything: CommonEverything):
    everything.navigator.append(SETTINGS.II_ZOOM)
    return await add_zoom(everything)


@r.on_callback(
    PayloadFilter(Payload.ZOOM),
    StateFilter(SETTINGS.I_MAIN)
)
async def to_browse_zoom(everything: CommonEverything):
    return await zoom_bp.to_browse(everything)



""" PIN ACTIONS """

@r.on_callback(
    StateFilter(SETTINGS.III_SHOULD_PIN), 
    PayloadFilter(Payload.DO_PIN)
)
async def check_do_pin(everything: CommonEverything):
    ctx = everything.ctx

    if not await everything.can_pin():
        answer_text = messages.format_cant_pin(everything.src)

        if everything.is_from_event:
            event = everything.event
            await event.show_notification(answer_text)

    else:
        ctx.settings.should_pin = True
        return await auto_route(everything)

@r.on_callback(
    StateFilter(SETTINGS.III_SHOULD_PIN), 
    PayloadFilter(Payload.SKIP)
)
async def skip_pin(everything: CommonEverything):
    return await deny_pin(everything)

@r.on_callback(
    StateFilter(SETTINGS.III_SHOULD_PIN),
    PayloadFilter(Payload.FALSE)
)
async def deny_pin(everything: CommonEverything):
    ctx = everything.ctx

    ctx.settings.should_pin = False

    return await auto_route(everything)

@r.on_callback(
    StateFilter(SETTINGS.III_SHOULD_PIN), 
    PayloadFilter(Payload.TRUE)
)
async def approve_pin(everything: CommonEverything):
    ctx = everything.ctx

    ctx.settings.should_pin = True

    return await auto_route(everything)



""" PIN STATE """

@r.on_everything(StateFilter(SETTINGS.III_SHOULD_PIN))
async def should_pin(everything: CommonEverything):
    ctx = everything.ctx
    is_should_pin_set = everything.ctx.settings.should_pin is not None
    is_from_hub = HUB.I_MAIN in ctx.navigator.trace

    answer_text = (
        messages.Builder()
    )

    # if we can pin messages
    if await everything.can_pin():
        # make a keyboard where we ask if
        # we should pin (TRUE) or not (FALSE)
        answer_keyboard = Keyboard([
            [kb.TRUE_BUTTON, kb.FALSE_BUTTON],
        ])

        if not is_from_hub:
            answer_keyboard.assign_next(
                kb.NEXT_BUTTON.only_if(is_should_pin_set)
            )
    
        # simply ask if user wants to pin
        answer_text.add(messages.format_do_pin())

    else:
        # we're not allowed to pin yet,
        # make a keyboard where user
        # can retry after he gives us permission,
        # or skip if he doesn't want to pin
        answer_keyboard = Keyboard([
            [kb.DO_PIN_BUTTON],
        ])
        
        if not is_from_hub:
            answer_keyboard.assign_next(kb.SKIP_BUTTON)

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
        add_tree    = not is_from_hub,
        tree_values = ctx.settings
    )

@r.on_callback(
    PayloadFilter(Payload.PIN),
    StateFilter(SETTINGS.I_MAIN)
)
async def to_should_pin(everything: CommonEverything):
    everything.navigator.append(SETTINGS.III_SHOULD_PIN)
    return await should_pin(everything)



""" BROADCAST ACTIONS """

@r.on_callback(
    StateFilter(SETTINGS.II_BROADCAST), 
    PayloadFilter(Payload.FALSE)
)
async def deny_broadcast(everything: CommonEverything):
    ctx = everything.ctx

    ctx.settings.broadcast = False
    ctx.settings.should_pin = False

    # after deny, it's impossible to
    # get to `should_pin`
    ctx.navigator.delete_back_trace(SETTINGS.III_SHOULD_PIN)

    return await auto_route(everything)

@r.on_callback(
    StateFilter(SETTINGS.II_BROADCAST), 
    PayloadFilter(Payload.TRUE)
)
async def approve_broadcast(everything: CommonEverything):
    ctx = everything.ctx

    ctx.settings.broadcast = True
    
    return await auto_route(everything)



""" BROADCAST STATE """

@r.on_everything(StateFilter(SETTINGS.II_BROADCAST))
async def broadcast(everything: CommonEverything):
    ctx = everything.ctx
    is_broadcast_set = everything.ctx.settings.broadcast is not None
    is_from_hub = HUB.I_MAIN in ctx.navigator.trace

    answer_text = (
        messages.Builder()
                .add(messages.format_broadcast())
    )
    answer_keyboard = Keyboard([
        [kb.TRUE_BUTTON, kb.FALSE_BUTTON],
    ]).assign_next(kb.NEXT_BUTTON.only_if(
        is_broadcast_set and not is_from_hub
    ))


    await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard,
        add_tree    = not is_from_hub,
        tree_values = ctx.settings
    )

@r.on_callback(
    PayloadFilter(Payload.BROADCAST),
    StateFilter(SETTINGS.I_MAIN)
)
async def to_broadcast(everything: CommonEverything):
    everything.navigator.append(SETTINGS.II_BROADCAST)
    return await broadcast(everything)



""" UNKNOWN_GROUP ACTIONS """

@r.on_callback(
    StateFilter(SETTINGS.III_UNKNOWN_GROUP), 
    PayloadFilter(Payload.TRUE)
)
async def confirm_unknown_group(everything: CommonEverything):
    # get valid group
    valid_group = everything.ctx.settings.group.valid

    # set it as confirmed
    everything.ctx.settings.group.confirmed = valid_group
    
    everything.navigator.jump_back_to_or_append(SETTINGS.II_GROUP)

    return await auto_route(everything)



""" UNKNOWN_GROUP STATE """

async def unknown_group(everything: CommonEverything):
    ctx = everything.ctx
    group = everything.ctx.settings.group.valid
    is_from_hub = HUB.I_MAIN in ctx.navigator.trace

    if everything.is_from_message:
        message = everything.message

        answer_text = (
            messages.Builder()
                    .add(messages.format_unknown_group(group))
        )
        answer_keyboard = Keyboard([
            [kb.TRUE_BUTTON],
        ])

        await message.answer(
            text        = answer_text.make(),
            keyboard    = answer_keyboard,
            add_tree    = not is_from_hub,
            tree_values = ctx.settings
        )

async def to_unknown_group(everything: CommonEverything):
    everything.navigator.append(SETTINGS.III_UNKNOWN_GROUP)
    return await unknown_group(everything)



""" GROUP STATE """

@r.on_everything(UnionFilter([
    StateFilter(SETTINGS.II_GROUP), 
    StateFilter(SETTINGS.III_UNKNOWN_GROUP)
]))
async def group(everything: CommonEverything):
    ctx = everything.ctx
    is_group_set = ctx.settings.group.confirmed is not None
    is_from_hub = HUB.I_MAIN in ctx.navigator.trace
    footer_addition = messages.default_footer_addition(everything)

    if ctx.navigator.current != SETTINGS.II_GROUP:
        ctx.navigator.jump_back_to_or_append(SETTINGS.II_GROUP)
    
    answer_keyboard = Keyboard().assign_next(
        kb.NEXT_BUTTON.only_if(is_group_set and not is_from_hub)
    )


    if everything.is_from_message:
        # most likely user sent a group in his message
        message = everything.message

        # search group regex in user's message text
        group_match = pattern.GROUP.search(message.text)

        # if no group in text
        if group_match is None:
            if SCHEDULE_API.is_online:
                groups_fmt = messages.format_groups(await SCHEDULE_API.groups())
            else:
                groups_fmt = messages.format_cant_connect_to_schedule_server()
            
            # send a message saying "your input is invalid"
            answer_text = (
                messages.Builder()
                        .add(groups_fmt)
                        .add(messages.format_invalid_group())
                        .add(footer_addition)
            )
            return await message.answer(
                text        = answer_text.make(),
                keyboard    = answer_keyboard,
                add_tree    = not is_from_hub,
                tree_values = ctx.settings
            )


        # add user's group to context as typed group
        ctx.settings.group.typed = group_match.group()

        # remove nonword from group (separators like "-")
        group_nonword = pattern.NON_LETTER.sub("", group_match.group())

        # make group all caps
        group_caps = group_nonword.upper()

        # add validated group to context as valid group
        ctx.settings.group.valid = group_caps

        
        if SCHEDULE_API.is_online:
            groups = await SCHEDULE_API.groups()
        else:
            groups = []

        # if this group not in list of all available groups
        if group_caps not in groups:
            # ask if we should still set this unknown group
            return await to_unknown_group(everything)

        # everything is ok, set this group as confirmed
        everything.ctx.settings.group.confirmed = group_caps

        return await auto_route(everything)

    elif everything.is_from_event:
        # user proceeded to this state from callback button "begin"
        event = everything.event

        if SCHEDULE_API.is_online:
            groups_fmt = messages.format_groups(await SCHEDULE_API.groups())
        else:
            groups_fmt = messages.format_cant_connect_to_schedule_server()

        answer_text = (
            messages.Builder()
                    .add(groups_fmt)
                    .add(messages.format_group_input())
                    .add(footer_addition)
        )
        await event.edit_message(
            text        = answer_text.make(),
            keyboard    = answer_keyboard,
            add_tree    = not is_from_hub,
            tree_values = ctx.settings
        )

@r.on_callback(
    UnionFilter((
        PayloadFilter(Payload.BEGIN),
        PayloadFilter(Payload.GROUP)
    )),
    UnionFilter((
        StateFilter(INIT.I_MAIN),
        StateFilter(SETTINGS.I_MAIN)
    ))
)
async def to_group(everything: CommonEverything):
    everything.navigator.append(SETTINGS.II_GROUP)
    return await group(everything)



""" MAIN STATE """

async def main(everything: CommonEverything):
    ctx = everything.ctx

    if ctx.navigator.first == HUB.I_MAIN:
        ctx.navigator.clear()
        ctx.navigator.auto_ignored()
        ctx.navigator.append(HUB.I_MAIN)
        ctx.navigator.append(SETTINGS.I_MAIN)

    answer_text = (
        messages.Builder()
                .add(messages.format_settings_main(is_group_chat=everything.is_group_chat))
    )
    answer_keyboard = Keyboard([
        [kb.GROUP_BUTTON.with_value(ctx.settings.group.confirmed)],
        [kb.BROADCAST_BUTTON.with_value(ctx.settings.broadcast)],
        [kb.PIN_BUTTON.with_value(ctx.settings.should_pin).only_if(
            SETTINGS.III_SHOULD_PIN not in ctx.navigator.ignored
        )],
        [kb.ZOOM_BUTTON.with_value(len(ctx.settings.zoom.entries))],
        [kb.RESET_BUTTON]
    ])

    return await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard
    )

@r.on_callback(
    StateFilter(HUB.I_MAIN),
    PayloadFilter(Payload.SETTINGS)
)
async def to_main(everything: CommonEverything):
    everything.navigator.append(SETTINGS.I_MAIN)
    return await main(everything)



STATE_MAP = {
    SETTINGS.I_MAIN: main,
    SETTINGS.II_GROUP: group,
    SETTINGS.III_UNKNOWN_GROUP: unknown_group,
    SETTINGS.II_BROADCAST: broadcast,
    SETTINGS.III_SHOULD_PIN: should_pin,
    SETTINGS.II_ZOOM: add_zoom,
}