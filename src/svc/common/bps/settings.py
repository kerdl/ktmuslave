from loguru import logger
import re

from src import defs
from src.api.schedule import SCHEDULE_API
from src.parse import pattern
from src.svc.common import CommonEverything, messages
from src.svc.common.bps import zoom as zoom_bp
from src.data import zoom as zoom_data
from src.data.schedule import TimeMode, format as sc_format
from src.data.weekday import Weekday
from src.data.settings import Mode
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


    if current_state == SETTINGS.II_MODE:
        if everything.ctx.settings.mode == Mode.GROUP:
            return await to_group(everything)
        if everything.ctx.settings.mode == Mode.TEACHER:
            return await to_teacher(everything)

    if current_state in [
        SETTINGS.II_GROUP,
        SETTINGS.III_UNKNOWN_GROUP,
        SETTINGS.II_TEACHER,
        SETTINGS.III_UNKNOWN_TEACHER
    ]:
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


""" TIME OVERRIDE ACTIONS """

@r.on_callback(
    StateFilter(SETTINGS.II_TIME_OVERRIDE),
    PayloadFilter(Payload.FALSE)
)
async def deny_time_override(everything: CommonEverything):
    ctx = everything.ctx
    ctx.settings.time_mode = TimeMode.ORIGINAL
    return await auto_route(everything)

@r.on_callback(
    StateFilter(SETTINGS.II_TIME_OVERRIDE),
    PayloadFilter(Payload.TRUE)
)
async def approve_time_override(everything: CommonEverything):
    ctx = everything.ctx
    ctx.settings.time_mode = TimeMode.OVERRIDE
    return await auto_route(everything)


""" TIME OVERRIDE STATE """

@r.on_everything(StateFilter(SETTINGS.II_TIME_OVERRIDE))
async def time_override(everything: CommonEverything):
    ctx = everything.ctx

    answer_text = (
        messages.Builder()
            .add(messages.format_time_override(sc_format.time_overrides_table(ignored=Weekday.SUNDAY)))
    )
    answer_keyboard = Keyboard([
        [kb.FALSE_BUTTON, kb.TRUE_BUTTON],
    ])

    await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard,
    )

@r.on_callback(
    PayloadFilter(Payload.TIME),
    StateFilter(SETTINGS.I_MAIN)
)
async def to_time_override(everything: CommonEverything):
    everything.navigator.append(SETTINGS.II_TIME_OVERRIDE)
    return await time_override(everything)


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
        is_finished = None
        if ctx.settings.mode == Mode.GROUP:
            is_finished = ctx.settings.zoom.is_finished
        elif ctx.settings.mode == Mode.TEACHER:
            is_finished = ctx.settings.tchr_zoom.is_finished

        answer_keyboard.assign_next(
            kb.NEXT_ZOOM_BUTTON.only_if(
                is_finished
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
            [kb.FALSE_BUTTON, kb.TRUE_BUTTON],
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
            .add_if(messages.format_broadcast(), ctx.settings.mode == Mode.GROUP)
            .add_if(messages.format_tchr_broadcast(), ctx.settings.mode == Mode.TEACHER)
    )
    answer_keyboard = Keyboard([
        [kb.FALSE_BUTTON, kb.TRUE_BUTTON],
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


""" UNKNOWN_TEACHER ACTIONS """

@r.on_callback(
    StateFilter(SETTINGS.III_UNKNOWN_TEACHER),
    PayloadFilter(Payload.TRUE)
)
async def confirm_unknown_teacher(everything: CommonEverything):
    # get valid teacher
    valid_teacher = everything.ctx.settings.teacher.valid

    # set it as confirmed
    everything.ctx.settings.teacher.confirmed = valid_teacher

    everything.navigator.jump_back_to_or_append(SETTINGS.II_TEACHER)

    if everything.ctx.is_switching_modes:
        everything.ctx.settings.mode = Mode.TEACHER
        everything.ctx.is_switching_modes = False

    return await auto_route(everything)



""" UNKNOWN_TEACHER STATE """

async def unknown_teacher(everything: CommonEverything):
    ctx = everything.ctx
    teacher = everything.ctx.settings.teacher.valid
    is_from_hub = HUB.I_MAIN in ctx.navigator.trace

    if everything.is_from_message:
        message = everything.message

        answer_text = (
            messages.Builder()
                    .add(messages.format_unknown_identifier(teacher))
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

async def to_unknown_teacher(everything: CommonEverything):
    everything.navigator.append(SETTINGS.III_UNKNOWN_TEACHER)
    return await unknown_teacher(everything)



""" TEACHER STATE """

@r.on_callback(StateFilter(SETTINGS.II_TEACHER), PayloadFilter(Payload.GROUP_MODE))
async def switch_to_group_mode(everything: CommonEverything):
    ctx = everything.ctx

    if ctx.navigator.current.anchor == SETTINGS.II_TEACHER.anchor:
        ctx.navigator.back(trace_it=False, execute_actions=False)
    
    if ctx.settings.group.confirmed is None:
        ctx.is_switching_modes = True
        return await to_group(everything)

    ctx.settings.mode = Mode.GROUP

    return await main(everything)

@r.on_everything(UnionFilter([
    StateFilter(SETTINGS.II_TEACHER),
    StateFilter(SETTINGS.III_UNKNOWN_TEACHER),
]))
async def teacher(everything: CommonEverything):
    ctx = everything.ctx
    is_teacher_set = ctx.settings.teacher.confirmed is not None
    is_from_hub = HUB.I_MAIN in ctx.navigator.trace
    is_show_names_payload = (
        everything.is_from_event and
        everything.event.payload == kb.Payload.SHOW_NAMES
    )
    original_valid = ctx.settings.teacher.valid
    footer_addition = messages.default_footer_addition(everything)

    if ctx.navigator.current != SETTINGS.II_TEACHER:
        ctx.navigator.jump_back_to_or_append(SETTINGS.II_TEACHER)

    answer_keyboard = Keyboard([
        [kb.SHOW_NAMES_BUTTON.only_if(not is_show_names_payload)],
        [kb.GROUP_MODE_BUTTON.only_if(is_from_hub and not ctx.is_switching_modes)],
    ]).assign_next(
        kb.NEXT_BUTTON.only_if(is_teacher_set and not is_from_hub)
    )

    teachers_fmt = None

    if SCHEDULE_API.is_online and is_show_names_payload:
        teachers_fmt = messages.format_teachers(await SCHEDULE_API.teachers())
    elif is_show_names_payload:
        teachers_fmt = messages.format_cant_connect_to_schedule_server()


    if everything.is_from_message:
        # most likely user sent a teacher in his message
        message = everything.message

        # search teacher regex in user's message text
        matched_regex = None
        teacher_match = None

        regexes = {
            "teacher": pattern.TEACHER,
            "teacher_case_ignored": pattern.TEACHER_CASE_IGNORED,
            "teacher_no_dots_case_ignored": pattern.TEACHER_NO_DOTS_CASE_IGNORED,
            "teacher_last_name_case_ignored": pattern.TEACHER_LAST_NAME_CASE_IGNORED
        }

        for (key, tchr_regex) in regexes.items():
            result = tchr_regex.search(message.text)
            if result is not None:
                matched_regex = key
                teacher_match = result
                break

        # if no teacher in text
        if teacher_match is None:
            # send a message saying "your input is invalid"
            answer_text = (
                messages.Builder()
                    .add(teachers_fmt)
                    .add(messages.format_invalid_teacher())
                    .add(footer_addition)
            )
            return await message.answer(
                text        = answer_text.make(),
                keyboard    = answer_keyboard,
                add_tree    = not is_from_hub,
                tree_values = ctx.settings
            )

        if SCHEDULE_API.is_online:
            teachers = await SCHEDULE_API.teachers()
        else:
            teachers = []

        # add user's teacher to context as typed teacher
        ctx.settings.teacher.typed = teacher_match.group()
        is_validation_ok = ctx.settings.teacher.generate_valid(reference=teachers)

        if ctx.settings.teacher.valid == original_valid and matched_regex == "teacher_last_name_case_ignored":
            answer_text = (
                messages.Builder()
                    .add(teachers_fmt)
                    .add(messages.format_forbidden_format_teacher())
                    .add(footer_addition)
            )
            return await message.answer(
                text        = answer_text.make(),
                keyboard    = answer_keyboard,
                add_tree    = not is_from_hub,
                tree_values = ctx.settings
            )
        elif ctx.settings.teacher.valid == original_valid or not is_validation_ok:
            answer_text = (
                messages.Builder()
                        .add(teachers_fmt)
                        .add(messages.format_invalid_teacher())
                        .add(footer_addition)
            )
            return await message.answer(
                text        = answer_text.make(),
                keyboard    = answer_keyboard,
                add_tree    = not is_from_hub,
                tree_values = ctx.settings
            )

        # if this teacher not in list of all available teachers
        if ctx.settings.teacher.valid not in teachers and SCHEDULE_API.is_online:
            # ask if we should still set this unknown teacher
            return await to_unknown_teacher(everything)

        # everything is ok, set this teacher as confirmed
        everything.ctx.settings.teacher.set_valid_as_confirmed()

        if ctx.is_switching_modes:
            ctx.settings.mode = Mode.TEACHER
            ctx.is_switching_modes = False

        return await auto_route(everything)

    elif everything.is_from_event:
        # user proceeded to this state from callback button "begin"
        event = everything.event

        answer_text = (
            messages.Builder()
                .add(teachers_fmt)
                .add(messages.format_teacher_input())
                .add(footer_addition)
        )
        await event.edit_message(
            text        = answer_text.make(),
            keyboard    = answer_keyboard,
            add_tree    = not is_from_hub,
            tree_values = ctx.settings
        )

@r.on_callback(
    PayloadFilter(Payload.TEACHER),
    UnionFilter((
        StateFilter(INIT.I_MAIN),
        StateFilter(SETTINGS.I_MAIN)
    ))
)
async def to_teacher(everything: CommonEverything):
    everything.navigator.append(SETTINGS.II_TEACHER)
    return await teacher(everything)


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

    if everything.ctx.is_switching_modes:
        everything.ctx.settings.mode = Mode.GROUP
        everything.ctx.is_switching_modes = False

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
                .add(messages.format_unknown_identifier(group))
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

@r.on_callback(StateFilter(SETTINGS.II_GROUP), PayloadFilter(Payload.TEACHER_MODE))
async def switch_to_teacher_mode(everything: CommonEverything):
    ctx = everything.ctx

    if ctx.navigator.current.anchor == SETTINGS.II_GROUP.anchor:
        ctx.navigator.back(trace_it=False, execute_actions=False)
    
    if ctx.settings.teacher.confirmed is None:
        ctx.is_switching_modes = True
        return await to_teacher(everything)

    ctx.settings.mode = Mode.TEACHER

    return await main(everything)

@r.on_everything(UnionFilter([
    StateFilter(SETTINGS.II_GROUP),
    StateFilter(SETTINGS.III_UNKNOWN_GROUP)
]))
async def group(everything: CommonEverything):
    ctx = everything.ctx
    is_group_set = ctx.settings.group.confirmed is not None
    is_from_hub = HUB.I_MAIN in ctx.navigator.trace
    is_show_names_payload = (
        everything.is_from_event and
        everything.event.payload == kb.Payload.SHOW_NAMES
    )
    footer_addition = messages.default_footer_addition(everything)

    if ctx.navigator.current != SETTINGS.II_GROUP:
        ctx.navigator.jump_back_to_or_append(SETTINGS.II_GROUP)

    answer_keyboard = Keyboard([
        [kb.SHOW_NAMES_BUTTON.only_if(not is_show_names_payload)],
        [kb.TEACHER_MODE_BUTTON.only_if(is_from_hub and not ctx.is_switching_modes)],
    ]).assign_next(
        kb.NEXT_BUTTON.only_if(is_group_set and not is_from_hub)
    )

    if everything.is_from_message:
        # most likely user sent a group in his message
        message = everything.message

        # search group regex in user's message text
        group_match = pattern.GROUP.search(message.text)

        # if no group in text
        if group_match is None:
            groups_fmt = None

            if SCHEDULE_API.is_online and is_show_names_payload:
                groups_fmt = messages.format_groups(await SCHEDULE_API.groups())
            elif is_show_names_payload:
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
        ctx.settings.group.generate_valid()


        if SCHEDULE_API.is_online:
            groups = await SCHEDULE_API.groups()
        else:
            groups = []

        # if this group not in list of all available groups
        if ctx.settings.group.valid not in groups and SCHEDULE_API.is_online:
            # ask if we should still set this unknown group
            return await to_unknown_group(everything)

        # everything is ok, set this group as confirmed
        everything.ctx.settings.group.set_valid_as_confirmed()

        if ctx.is_switching_modes:
            ctx.settings.mode = Mode.GROUP
            ctx.is_switching_modes = False

        return await auto_route(everything)

    elif everything.is_from_event:
        # user proceeded to this state from callback button "begin"
        event = everything.event
        groups_fmt = None

        if SCHEDULE_API.is_online and is_show_names_payload:
            groups_fmt = messages.format_groups(await SCHEDULE_API.groups())
        elif is_show_names_payload:
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
    PayloadFilter(Payload.GROUP),
    UnionFilter((
        StateFilter(INIT.I_MAIN),
        StateFilter(SETTINGS.I_MAIN)
    ))
)
async def to_group(everything: CommonEverything):
    everything.navigator.append(SETTINGS.II_GROUP)
    return await group(everything)

""" MODE STATE """

@r.on_everything(
    StateFilter(SETTINGS.II_MODE),
    PayloadFilter(Payload.ME_STUDENT)
)
async def me_student_mode(everything: CommonEverything):
    ctx = everything.ctx

    ctx.settings.mode = Mode.GROUP
    # clear teacher-specific states from back trace
    ctx.navigator.replace_back_trace({
        SETTINGS.II_TEACHER.anchor: SETTINGS.II_GROUP,
        SETTINGS.III_UNKNOWN_TEACHER.anchor: SETTINGS.III_UNKNOWN_GROUP
    })

    return await auto_route(everything)

@r.on_everything(
    StateFilter(SETTINGS.II_MODE),
    PayloadFilter(Payload.ME_TEACHER)
)
async def me_teacher_mode(everything: CommonEverything):
    ctx = everything.ctx

    ctx.settings.mode = Mode.TEACHER
    # clear group-specific states from back trace
    ctx.navigator.replace_back_trace({
        SETTINGS.II_GROUP.anchor: SETTINGS.II_TEACHER,
        SETTINGS.III_UNKNOWN_GROUP.anchor: SETTINGS.III_UNKNOWN_TEACHER
    })

    return await auto_route(everything)

@r.on_everything(StateFilter(SETTINGS.II_MODE))
async def mode(everything: CommonEverything):
    ctx = everything.ctx
    is_mode_set = everything.ctx.settings.mode is not None
    is_from_hub = HUB.I_MAIN in ctx.navigator.trace

    answer_text = (
        messages.Builder()
                .add(messages.format_choose_schedule_mode())
    )
    answer_keyboard = Keyboard([
        [kb.ME_STUDENT_BUTTON, kb.ME_TEACHER_BUTTON],
    ]).assign_next(kb.NEXT_BUTTON.only_if(
        is_mode_set and not is_from_hub
    ))


    await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard,
        add_tree    = not is_from_hub,
        tree_values = ctx.settings
    )

@r.on_callback(
    UnionFilter((
        PayloadFilter(Payload.BEGIN),
        PayloadFilter(Payload.MODE)
    )),
    UnionFilter((
        StateFilter(INIT.I_MAIN),
        StateFilter(SETTINGS.I_MAIN)
    ))
)
async def to_mode(everything: CommonEverything):
    everything.navigator.append(SETTINGS.II_MODE)
    return await mode(everything)


""" MAIN STATE """
@r.on_everything(StateFilter(SETTINGS.I_MAIN))
async def main(everything: CommonEverything):
    ctx = everything.ctx

    if ctx.navigator.first == HUB.I_MAIN:
        ctx.navigator.clear_all()
        ctx.navigator.auto_ignored()
        ctx.navigator.append(HUB.I_MAIN)
        ctx.navigator.append(SETTINGS.I_MAIN)
    
    entries_len = 0
    if ctx.settings.mode == Mode.GROUP:
        entries_len = len(ctx.settings.zoom.entries)
    elif ctx.settings.mode == Mode.TEACHER:
        entries_len = len(ctx.settings.tchr_zoom.entries)

    answer_text = (
        messages.Builder()
            .add_if(messages.format_settings_main(
                everything.is_group_chat,
                ctx.settings.group.confirmed,
                ctx.settings.broadcast,
                ctx.settings.should_pin,
                len(ctx.settings.zoom.entries),
                ctx.settings.time_mode
            ), ctx.settings.mode == Mode.GROUP)
            .add_if(messages.format_tchr_settings_main(
                everything.is_group_chat,
                ctx.settings.teacher.confirmed,
                ctx.settings.broadcast,
                ctx.settings.should_pin,
                len(ctx.settings.tchr_zoom.entries),
                ctx.settings.time_mode
            ), ctx.settings.mode == Mode.TEACHER)
    )
    answer_keyboard = Keyboard([
        [kb.GROUP_BUTTON.with_value(ctx.settings.group.confirmed).only_if(ctx.settings.mode == Mode.GROUP)],
        [kb.TEACHER_BUTTON.with_value(ctx.settings.teacher.confirmed).only_if(ctx.settings.mode == Mode.TEACHER)],
        [
            kb.BROADCAST_BUTTON.with_value(ctx.settings.broadcast),
            kb.PIN_BUTTON.with_value(ctx.settings.should_pin).only_if(
                SETTINGS.III_SHOULD_PIN not in ctx.navigator.ignored
            )
        ],
        [kb.ZOOM_BUTTON.with_value(entries_len)],
        [kb.TIME_BUTTON.with_value(ctx.settings.time_mode)],
        [kb.EXECUTE_CODE_BUTTON.only_if(everything.ctx.is_admin)],
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
    SETTINGS.II_MODE: mode,
    SETTINGS.II_GROUP: group,
    SETTINGS.III_UNKNOWN_GROUP: unknown_group,
    SETTINGS.II_TEACHER: teacher,
    SETTINGS.III_UNKNOWN_TEACHER: unknown_teacher,
    SETTINGS.II_BROADCAST: broadcast,
    SETTINGS.III_SHOULD_PIN: should_pin,
    SETTINGS.II_ZOOM: add_zoom,
    SETTINGS.II_TIME_OVERRIDE: time_override,
}
