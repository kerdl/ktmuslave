from time import time
from loguru import logger
from aiohttp.client_exceptions import ClientConnectorError
import asyncio

from src import defs
from src.parse import pattern
from src.svc.common import CommonEverything, messages
from src.svc.common.bps import zoom as zoom_bp
from src.data import zoom as zoom_data, week
from src.data.settings import Group, Mode, Teacher
from src.data.schedule import format as sc_format
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import INIT, ZOOM, HUB
from src.svc.common.router import router
from src.svc.common.filters import PayloadFilter, StateFilter, UnionFilter
from src.svc.common import keyboard as kb


@router.on_callback(PayloadFilter(kb.Payload.RESEND))
async def resend(everything: CommonEverything):
    everything.ctx.schedule.reset_temps()
    return await to_hub(everything, allow_edit=False)

@router.on_everything(StateFilter(HUB.I_MAIN))
async def hub(
    everything: CommonEverything,
    allow_edit: bool = True,
    allow_send: bool = True
):    
    ctx = everything.ctx
    current_mode = (
        ctx.schedule.temp_mode if ctx.schedule.temp_mode else ctx.settings.mode
    )

    identifier = None
    if current_mode == Mode.GROUP:
        identifier = ctx.settings.group.valid
    elif current_mode == Mode.TEACHER:
        identifier = ctx.settings.teacher.valid
    
    temp_identifier = None
    if current_mode == Mode.GROUP:
        temp_identifier = ctx.schedule.temp_group
    elif current_mode == Mode.TEACHER:
        temp_identifier = ctx.schedule.temp_teacher

    if everything.is_from_message:
        if (
            everything.is_from_tg_generally and
            everything.message.tg_did_user_used_bot_command()
        ):
            ...
        elif everything.message.text:
            group_match = pattern.GROUP.match(everything.message.text)
            if group_match is None:
                teacher = Teacher(typed=everything.message.text)
                teacher.generate_valid(await defs.schedule.teacher_names())
                identifier_match = pattern.TEACHER.match(teacher.valid) if teacher.valid else None
                if identifier_match is not None:
                    current_mode = Mode.TEACHER
                    ctx.schedule.temp_mode = current_mode
            else:
                identifier_match = group_match
                current_mode = Mode.GROUP
                ctx.schedule.temp_mode = current_mode

            if identifier_match is None:
                return
        
            identifier_match = identifier_match.group()

            if current_mode == Mode.GROUP:
                identifier_object = Group(typed=identifier_match)
                identifier_object.generate_valid()
            elif current_mode == Mode.TEACHER:
                identifier_object = teacher
            
            if identifier_object.valid != identifier:
                if current_mode == Mode.GROUP:
                    ctx.schedule.temp_group = identifier_object.valid
                    temp_identifier = ctx.schedule.temp_group
                elif current_mode == Mode.TEACHER:
                    ctx.schedule.temp_teacher = identifier_object.valid
                    temp_identifier = ctx.schedule.temp_teacher

    schedule_text = messages.format_schedule_unavailable()

    if defs.schedule.is_online:
        if current_mode == Mode.GROUP:
            page = await defs.schedule.get_groups(
                temp_identifier if temp_identifier else identifier
            )
        elif current_mode == Mode.TEACHER:
            page = await defs.schedule.get_teachers(
                temp_identifier if temp_identifier else identifier
            )

        users_formation = page.get_by_name(
            temp_identifier if temp_identifier else identifier
        ) if page is not None else None

        zoom_entries = None
        if current_mode == Mode.GROUP:
            zoom_entries = ctx.settings.zoom.entries.list
        elif current_mode == Mode.TEACHER:
            zoom_entries = ctx.settings.tchr_zoom.entries.list
        
        users_formation = users_formation.retain_days(
            week.current_active()
        )
        
        schedule_text = await sc_format.formation(
            form=users_formation,
            entries=zoom_entries,
            mode=current_mode,
            do_tg_markup=everything.is_from_tg_generally
        )
    else:
        schedule_text = messages.format_cant_connect_to_schedule_server()

    answer_text = (
        messages.Builder()
            .add(schedule_text)
    )
    if temp_identifier:
        answer_keyboard = kb.Keyboard.temp_identifier_hub()
    else:
        answer_keyboard = kb.Keyboard.hub_default()

    if (
        everything.is_from_event and (
            (allow_send and not allow_edit)
            or everything.event.payload == kb.Payload.RESEND
        )
    ):
        await everything.event.show_notification(
            text=messages.format_sent_as_new_message()
        )

        return await everything.event.send_message(
            text=answer_text.make(),
            keyboard=answer_keyboard
        )

    if everything.is_from_event and allow_edit:
        return await everything.event.edit_message(
            text=answer_text.make(),
            keyboard=answer_keyboard
        )

    if everything.is_from_message and allow_send:
        return await everything.message.answer(
            text=answer_text.make(),
            keyboard=answer_keyboard
        )


async def to_hub(
    everything: CommonEverything,
    allow_edit: bool = True,
    allow_send: bool = True
):
    everything.navigator.clear_all()
    everything.navigator.append(HUB.I_MAIN)

    everything.navigator.auto_ignored()

    return await hub(
        everything=everything,
        allow_edit=allow_edit,
        allow_send=allow_send
    )


STATE_MAP = {
    HUB.I_MAIN: hub,
}
