from loguru import logger
from aiogram.types import Message, CallbackQuery

from src import defs
from svc.common import CommonMessage
from svc.common.bps import init
from svc.common.context import TgCtx
from svc.common.states.tree import Init
from svc.telegram.filter import StateFilter, CallbackFilter

r = defs.tg_router

@r.message(StateFilter(state=Init.I_MAIN))
async def main(message: Message, common_message: CommonMessage):
    return await init.main(common_message)

@r.callback_query(CallbackFilter(data="begin"))
async def begin_click(callback_query: CallbackQuery, ctx: TgCtx):
    logger.info(f"begin click {ctx}")

async def group(message: Message, common_message: CommonMessage):
    ...

async def unknown_group(message: Message, common_message: CommonMessage):
    ...

async def schedule_broadcast(message: Message, common_message: CommonMessage):
    ...

async def should_pin(message: Message, common_message: CommonMessage):
    ...

async def finish(message: Message, common_message: CommonMessage):
    ...