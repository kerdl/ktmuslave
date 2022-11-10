from time import time
from loguru import logger
import re

from src import defs
from src.api.schedule import SCHEDULE_API
from src.parse import pattern
from src.svc.common import CommonEverything, messages
from src.svc.common.bps import zoom as zoom_bp
from src.data import zoom as zoom_data
from src.data.schedule import format as sc_format
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import Init, Zoom, Hub
from src.svc.common.router import r
from src.svc.common.filters import PayloadFilter, StateFilter, UnionFilter
from src.svc.common import keyboard as kb


@r.on_callback(StateFilter(Hub.I_MAIN), PayloadFilter(kb.Payload.UPDATE))
async def update(everything: CommonEverything):
    ctx = everything.ctx

    if ctx.schedule.can_update:
        has_updates = await ctx.schedule.update()

        message = messages.format_no_updates()

        if has_updates:
            message = messages.format_updates_sent()

        await everything.event.show_notification(message)
    else:
        await everything.event.show_notification(
            messages.format_too_fast_retry_after(int(ctx.schedule.until_allowed))
        )

@r.on_callback(StateFilter(Hub.I_MAIN), PayloadFilter(kb.Payload.WEEKLY))
async def switch_to_weekly(everything: CommonEverything):
    ctx = everything.ctx
    ctx.schedule.message.switch_to_weekly()

    return await hub(everything)

@r.on_callback(StateFilter(Hub.I_MAIN), PayloadFilter(kb.Payload.DAILY))
async def switch_to_daily(everything: CommonEverything):
    ctx = everything.ctx
    ctx.schedule.message.switch_to_daily()

    return await hub(everything)

async def hub(everything: CommonEverything):
    ctx = everything.ctx

    is_daily = ctx.schedule.message.is_daily
    is_weekly = ctx.schedule.message.is_weekly
    is_folded = ctx.schedule.message.is_folded
    is_unfolded = not is_folded

    schedule_text = "ЫЫ ЧО ЗА ХУЙНЯ???"

    if ctx.schedule.message.is_weekly:
        weekly_page = await SCHEDULE_API.weekly()
        users_group = weekly_page.get_group(ctx.settings.group.confirmed)

        if users_group is not None:
            schedule_text = sc_format.group(
                users_group,
                ctx.settings.zoom.entries.set
            )
        else:
            schedule_text = "твоей группы нет в недельном расписании ёпта"
    elif ctx.schedule.message.is_daily:
        daily_page = await SCHEDULE_API.daily()
        users_group = daily_page.get_group(ctx.settings.group.confirmed)

        if users_group is not None:
            schedule_text = sc_format.group(
                users_group,
                ctx.settings.zoom.entries.set
            )
        else:
            schedule_text = "твоей группы нет в дневном расписании ёпта"

    answer_text = (
        messages.Builder()
                .add(schedule_text)
    )
    answer_keyboard = kb.Keyboard([
        [kb.WEEKLY_BUTTON.only_if(is_daily)],
        [kb.DAILY_BUTTON.only_if(is_weekly)],
        #[kb.FOLD_BUTTON.only_if(is_unfolded)],
        #[kb.UNFOLD_BUTTON.only_if(is_folded)],
        [kb.UPDATE_BUTTON],
        [kb.SETTINGS_BUTTON]
    ], add_back = False)

    return await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard
    )

async def to_hub(everything: CommonEverything):
    everything.navigator.clear()
    everything.navigator.append(Hub.I_MAIN)

    everything.navigator.auto_ignored()

    return await hub(everything)


STATE_MAP = {
    Hub.I_MAIN: hub,
}