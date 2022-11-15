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
from src.svc.common.states.tree import INIT, ZOOM, HUB
from src.svc.common.router import r
from src.svc.common.filters import PayloadFilter, StateFilter, UnionFilter
from src.svc.common import keyboard as kb


@r.on_callback(StateFilter(HUB.I_MAIN), PayloadFilter(kb.Payload.UPDATE))
async def update(everything: CommonEverything):
    ctx = everything.ctx

    if ctx.schedule.can_update:
        notify = await ctx.schedule.update()

        if notify.has_updates_for_group(ctx.settings.group.confirmed):
            message = messages.format_updates_sent()
            await everything.event.show_notification(message)
        else:
            message = messages.format_no_updates()
            await everything.event.show_notification(message)

            allow_edit = (
                everything.event.message_id == ctx.last_bot_message.id
                and everything.event.message_id not in [
                    ctx.last_weekly_message.id,
                    ctx.last_daily_message.id
                ]
            )

            return await hub(
                everything,
                allow_edit = allow_edit
            )

        await defs.ctx.broadcast(notify, invoker = ctx)
    else:
        await everything.event.show_notification(
            messages.format_too_fast_retry_after(
                int(ctx.schedule.until_allowed)
            )
        )

@r.on_callback(StateFilter(HUB.I_MAIN), PayloadFilter(kb.Payload.WEEKLY))
async def switch_to_weekly(everything: CommonEverything):
    ctx = everything.ctx
    ctx.schedule.message.switch_to_weekly()

    return await hub(everything)

@r.on_callback(StateFilter(HUB.I_MAIN), PayloadFilter(kb.Payload.DAILY))
async def switch_to_daily(everything: CommonEverything):
    ctx = everything.ctx
    ctx.schedule.message.switch_to_daily()

    return await hub(everything)

@r.on_everything(StateFilter(HUB.I_MAIN))
async def hub(
    everything: CommonEverything,
    allow_edit: bool = True,
    allow_send: bool = True
):
    ctx = everything.ctx

    is_daily = ctx.schedule.message.is_daily
    is_weekly = ctx.schedule.message.is_weekly
    is_folded = ctx.schedule.message.is_folded
    is_unfolded = not is_folded

    schedule_text = "ЫЫ ЧО ЗА ХУЙНЯ???"

    if ctx.schedule.message.is_weekly:
        weekly_page = await SCHEDULE_API.cached_weekly()
        users_group = weekly_page.get_group(ctx.settings.group.confirmed)

    elif ctx.schedule.message.is_daily:
        daily_page = await SCHEDULE_API.cached_daily()
        users_group = daily_page.get_group(ctx.settings.group.confirmed)

    schedule_text = await sc_format.group(
        users_group,
        ctx.settings.zoom.entries.set
    )

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
        [kb.RESEND_BUTTON],
        [kb.SETTINGS_BUTTON],
        [
            SCHEDULE_API.ft_daily_url_button(),
            SCHEDULE_API.ft_weekly_url_button()
        ],
        [SCHEDULE_API.r_weekly_url_button()],
    ], add_back = False)

    if (
        everything.is_from_event 
        and everything.event.payload == kb.Payload.RESEND
        and allow_send
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


async def to_hub(everything: CommonEverything):
    everything.navigator.clear()
    everything.navigator.append(HUB.I_MAIN)

    everything.navigator.auto_ignored()

    return await hub(everything)


STATE_MAP = {
    HUB.I_MAIN: hub,
}