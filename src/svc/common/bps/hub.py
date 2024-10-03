import asyncio
from time import time
from loguru import logger
from aiohttp.client_exceptions import ClientConnectorError
from aiogram.exceptions import TelegramBadRequest
from src import defs
from src.parse import pattern
from src.svc.common import CommonEverything, messages
from src.svc.common.bps import zoom as zoom_bp
from src.data import zoom as zoom_data, week
from src.data.settings import Group, Mode, Teacher
from src.data.schedule import format as sc_format
from src.parse import group, teacher
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

    if everything.is_from_message:
        if (
            everything.is_from_tg_generally and
            everything.message.tg_did_user_used_bot_command()
        ):
            ...
        elif everything.message.text:
            group_match = pattern.GROUP.match(everything.message.text)
            if group_match is None:
                valid_teacher = teacher.validate(
                    everything.message.text,
                    defs.schedule.teacher_names()
                )
                identifier_match = pattern.TEACHER.match(
                    valid_teacher
                ) if valid_teacher else None
                if valid_teacher is not None:
                    ctx.schedule.temp_mode = Mode.TEACHER
            else:
                valid_group = group.validate(group_match.group())
                identifier_match = pattern.GROUP.match(
                    valid_group
                )
                ctx.schedule.temp_mode = Mode.GROUP

            if identifier_match is None:
                return
        
            identifier = identifier_match.group()
            
            if (
                ctx.schedule.temp_mode == Mode.GROUP and
                identifier not in defs.schedule.group_names()
            ):
                return

            if (
                ctx.schedule.temp_mode == Mode.TEACHER and
                identifier not in defs.schedule.teacher_names()
            ):
                return
            
            if identifier != ctx.identifier:
                if ctx.mode == Mode.GROUP:
                    ctx.schedule.temp_group = identifier
                elif ctx.mode == Mode.TEACHER:
                    ctx.schedule.temp_teacher = identifier
                
                ctx.schedule.reset_temp_week()
    
    if not defs.schedule.is_cached_available:
        schedule_text = messages.format_cant_connect_to_schedule_server()
    elif not ctx.identifier_exists:
        if ctx.is_group_mode:
            schedule_text = messages.format_no_schedule()
        elif ctx.is_teacher_mode:
            schedule_text = messages.format_tchr_no_schedule()
    elif defs.schedule.is_cached_available:
        schedule_text = ctx.fmt_schedule()
    else:
        schedule_text = messages.format_schedule_unavailable()

    answer_text = (
        messages.Builder()
            .add(schedule_text)
    )
    if ctx.is_temp_mode:
        answer_keyboard = kb.Keyboard.temp_identifier_hub(
            is_previous_dead_end=(
                not ctx.is_backward_week_shift_allowed()
            ),
            is_previous_jump_dead_end=(
                not ctx.is_backward_week_shift_allowed()
            ),
            is_next_dead_end=(
                not ctx.is_forward_week_shift_allowed()
            ),
            is_next_jump_dead_end=(
                not ctx.is_forward_week_shift_allowed()
            )
        )
    else:
        answer_keyboard = kb.Keyboard.hub_default(
            is_previous_dead_end=(
                not ctx.is_backward_week_shift_allowed()
            ),
            is_previous_jump_dead_end=(
                not ctx.is_backward_week_shift_allowed()
            ),
            is_next_dead_end=(
                not ctx.is_forward_week_shift_allowed()
            ),
            is_next_jump_dead_end=(
                not ctx.is_forward_week_shift_allowed()
            )
        )

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
