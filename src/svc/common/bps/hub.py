from time import time
from loguru import logger
from aiohttp.client_exceptions import ClientConnectorError
import asyncio
import async_timeout

from src import defs, UpdateWaiter
from src.api.schedule import SCHEDULE_API
from src.parse import pattern
from src.svc.common import CommonEverything, messages
from src.svc.common.bps import zoom as zoom_bp
from src.data import zoom as zoom_data
from src.data.settings import Group, Mode, Teacher, TimeMode
from src.data.schedule import format as sc_format
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import INIT, ZOOM, HUB
from src.svc.common.router import r
from src.svc.common.filters import PayloadFilter, StateFilter, UnionFilter
from src.svc.common import keyboard as kb


@r.on_callback(PayloadFilter(kb.Payload.UPDATE))
async def update(everything: CommonEverything):
    ctx = everything.ctx

    if not ctx.schedule.can_update:
        message = messages.format_too_fast_retry_after(
            int(ctx.schedule.until_allowed)
        )
        return await everything.event.show_notification(message)
    if not SCHEDULE_API.is_online:
        message = messages.format_cant_connect_to_schedule_server()
        return await everything.event.show_notification(message)

    with UpdateWaiter(ctx):
        try:
            async with async_timeout.timeout(10):
                notify = await ctx.schedule.update()
        except asyncio.TimeoutError:
            message = messages.format_updates_timeout()
            return await everything.event.show_notification(message)

        if notify.is_manually_invoked:
            defs.create_task(defs.ctx.broadcast(notify, invoker = ctx))

        if notify.has_updates_for_group(ctx.settings.group.confirmed):
            message = messages.format_updates_sent()
            return await everything.event.show_notification(message)
        else:
            message = messages.format_no_updates()
            await everything.event.show_notification(message)

            allow_edit = (
                everything.event.message_id == ctx.last_bot_message.id
                and everything.event.message_id not in [
                    ctx.last_weekly_message.id if ctx.last_weekly_message is not None else None,
                    ctx.last_daily_message.id if ctx.last_daily_message is not None else None
                ]
            )

            return await hub(
                everything,
                allow_edit = allow_edit,
                allow_send = False,
            )

@r.on_callback(PayloadFilter(kb.Payload.WEEKLY))
async def switch_to_weekly(everything: CommonEverything):
    ctx = everything.ctx
    ctx.schedule.message.switch_to_weekly()

    return await hub(everything)

@r.on_callback(PayloadFilter(kb.Payload.DAILY))
async def switch_to_daily(everything: CommonEverything):
    ctx = everything.ctx
    ctx.schedule.message.switch_to_daily()

    return await hub(everything)

@r.on_callback(PayloadFilter(kb.Payload.RESEND))
async def resend(everything: CommonEverything):
    everything.ctx.schedule.reset_temps()
    return await to_hub(everything, allow_edit=False)

@r.on_everything(StateFilter(HUB.I_MAIN))
async def hub(
    everything: CommonEverything,
    allow_edit: bool = True,
    allow_send: bool = True
):
    ctx = everything.ctx
    temp_mode = ctx.schedule.temp_mode if ctx.schedule.temp_mode else ctx.settings.mode

    identifier = None
    if temp_mode == Mode.GROUP:
        identifier = ctx.settings.group.valid
    elif temp_mode == Mode.TEACHER:
        identifier = ctx.settings.teacher.valid
    
    temp_identifier = None
    if temp_mode == Mode.GROUP:
        temp_identifier = ctx.schedule.temp_group
    elif temp_mode == Mode.TEACHER:
        temp_identifier = ctx.schedule.temp_teacher

    if everything.is_from_message:
        if everything.is_from_tg_generally and everything.message.tg_did_user_used_bot_command():
            ...
        elif everything.message.text:
            group_match = pattern.GROUP.match(everything.message.text)
            if group_match is None:
                teacher = Teacher(typed=everything.message.text)
                teacher.generate_valid(await SCHEDULE_API.teachers())
                identifier_match = pattern.TEACHER.match(teacher.valid) if teacher.valid else None
                if identifier_match is not None:
                    temp_mode = Mode.TEACHER
                    ctx.schedule.temp_mode = temp_mode
            else:
                identifier_match = group_match
                temp_mode = Mode.GROUP
                ctx.schedule.temp_mode = temp_mode

            if identifier_match is None:
                return
        
            identifier_match = identifier_match.group()

            if temp_mode == Mode.GROUP:
                identifier_object = Group(typed=identifier_match)
                identifier_object.generate_valid()
            elif temp_mode == Mode.TEACHER:
                identifier_object = teacher
            
            if identifier_object.valid != identifier:
                if temp_mode == Mode.GROUP:
                    ctx.schedule.temp_group = identifier_object.valid
                    temp_identifier = ctx.schedule.temp_group
                elif temp_mode == Mode.TEACHER:
                    ctx.schedule.temp_teacher = identifier_object.valid
                    temp_identifier = ctx.schedule.temp_teacher

    schedule_text = "None"

    if SCHEDULE_API.is_online:
        if ctx.schedule.message.is_weekly:
            if temp_mode == Mode.GROUP:
                weekly_page = await SCHEDULE_API.weekly(temp_identifier if temp_identifier else identifier)
                users_identifier_data = weekly_page.get_group(temp_identifier if temp_identifier else identifier) if weekly_page is not None else None
            elif temp_mode == Mode.TEACHER:
                weekly_page = await SCHEDULE_API.tchr_weekly(temp_identifier if temp_identifier else identifier)
                users_identifier_data = weekly_page.get_teacher(temp_identifier if temp_identifier else identifier) if weekly_page is not None else None
        
        elif ctx.schedule.message.is_daily:
            if temp_mode == Mode.GROUP:
                daily_page = await SCHEDULE_API.groups(temp_identifier if temp_identifier else identifier)
                users_identifier_data = daily_page.get_name(temp_identifier if temp_identifier else identifier) if daily_page is not None else None
            elif temp_mode == Mode.TEACHER:
                daily_page = await SCHEDULE_API.tchr_daily(temp_identifier if temp_identifier else identifier)
                users_identifier_data = daily_page.get_teacher(temp_identifier if temp_identifier else identifier) if daily_page is not None else None

        zoom_entries = None
        if temp_mode == Mode.GROUP:
            zoom_entries = ctx.settings.zoom.entries.list
        elif temp_mode == Mode.TEACHER:
            zoom_entries = ctx.settings.tchr_zoom.entries.list
        
        schedule_text = await sc_format.identifier(
            users_identifier_data,
            zoom_entries,
            temp_mode,
            everything.is_from_tg_generally,
            override_time=ctx.settings.time_mode == TimeMode.OVERRIDE
        )
    else:
        schedule_text = messages.format_cant_connect_to_schedule_server()

    answer_text = (
        messages.Builder()
            .add(schedule_text)
    )
    if temp_identifier:
        answer_keyboard = kb.Keyboard.temp_identifier_hub(
            ctx.schedule.message.type,
            temp_mode
        )
    else:
        answer_keyboard = kb.Keyboard.hub_default(
            ctx.schedule.message.type,
            ctx.settings.mode
        )

    if (
        everything.is_from_event and (
            (allow_send and not allow_edit)
            or everything.event.payload == kb.Payload.RESEND
        )
    ):
        await everything.event.show_notification(
            text = messages.format_sent_as_new_message()
        )

        return await everything.event.send_message(
            text     = answer_text.make(),
            keyboard = answer_keyboard
        )

    if everything.is_from_event and allow_edit:
        return await everything.event.edit_message(
            text     = answer_text.make(),
            keyboard = answer_keyboard
        )

    if everything.is_from_message and allow_send:
        return await everything.message.answer(
            text     = answer_text.make(),
            keyboard = answer_keyboard
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
        everything,
        allow_edit = allow_edit,
        allow_send = allow_send
    )


STATE_MAP = {
    HUB.I_MAIN: hub,
}
