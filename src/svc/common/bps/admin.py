from loguru import logger
import re
import traceback

from src import defs
from src.api.schedule import SCHEDULE_API
from src.parse import pattern
from src.svc.common import CommonEverything, messages
from src.svc.common.bps import zoom as zoom_bp, executor
from src.data import zoom as zoom_data
from src.svc.common.states import formatter as states_fmt, Space
from src.svc.common.states.tree import INIT, ZOOM, SETTINGS, RESET, HUB, ADMIN
from src.svc.common.router import r, AvoidPostMw
from src.svc.common.filters import PayloadFilter, StateFilter, UnionFilter
from src.svc.common.keyboard import Keyboard, Payload
from src.svc.common import keyboard as kb


""" ADMIN STATE """

@r.on_message(StateFilter(ADMIN.I_EXECUTE_CODE))
async def execute_code(everything: CommonEverything):
    if not everything.ctx.is_admin:
        answer_text = (
            messages.Builder()
                .add(messages.format_no_rights())
        )
        answer_keyboard = kb.Keyboard()

        return await everything.answer(
            text=answer_text.make(),
            keyboard=answer_keyboard
        )

    if everything.is_from_event:
        answer_text = (
            messages.Builder()
                .add(messages.format_execute_code_explain(
                    exposed_vars=["everything: CommonEverything", "defs: Defs"],
                    print_example="log(\"message\")"
                ))
        )
    elif everything.is_from_message:
        (logs, error) = await executor.execute(
            everything,
            everything.message.text
        )

        if not logs or len(logs.replace("\n", "")) < 1:
            logs = messages.format_logs_empty(do_escape=everything.is_from_tg_generally)

        answer_text = (
            messages.Builder()
                .add(logs)
                .add_if(
                    messages.format_execution_error(error),
                    error is not None
                )
        )

    answer_keyboard = Keyboard()

    await everything.edit_or_answer(
        text=answer_text.make(),
        keyboard=answer_keyboard
    )

@r.on_callback(
    StateFilter(SETTINGS.I_MAIN), 
    PayloadFilter(Payload.EXECUTE_CODE)
)
async def to_execute_code(everything: CommonEverything):
    if not everything.ctx.is_admin:
        if everything.is_from_event:
            answer_text = (
                messages.Builder()
                    .add(messages.format_no_rights())
            )
            
            return await everything.event.show_notification(
                answer_text.make()
            )

    everything.navigator.append(ADMIN.I_EXECUTE_CODE)
    return await execute_code(everything)
