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
async def begin(callback_query: CallbackQuery):
    return await init.begin()

async def group(message: Message, common_message: CommonMessage):
    return await init.group(common_message)

async def unknown_group(message: Message, common_message: CommonMessage):
    return await init.unknown_group(common_message)

async def schedule_broadcast(message: Message, common_message: CommonMessage):
    return await init.schedule_broadcast(common_message)

async def should_pin(message: Message, common_message: CommonMessage):
    return await init.should_pin(common_message)

async def finish(message: Message, common_message: CommonMessage):
    return await init.finish(common_message)