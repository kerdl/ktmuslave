from loguru import logger
from aiogram.types import Message, CallbackQuery

from src import defs
from src.svc.common import CommonEverything
from src.svc.common.bps import init
from src.svc.common.states.tree import Init
from src.svc.telegram.filter import StateFilter, CallbackFilter

r = defs.tg_router

@r.message(StateFilter(state=Init.I_MAIN))
async def main(message: Message, common_everything: CommonEverything):
    return await init.main(common_everything)

@r.callback_query(CallbackFilter(data="begin"))
async def begin(callback_query: CallbackQuery, common_everything: CommonEverything):
    return await init.begin(common_everything)

async def group(message: Message, common_everything: CommonEverything):
    return await init.group(common_everything)

async def unknown_group(message: Message, common_everything: CommonEverything):
    return await init.unknown_group(common_everything)

async def schedule_broadcast(message: Message, common_everything: CommonEverything):
    return await init.schedule_broadcast(common_everything)

async def should_pin(message: Message, common_everything: CommonEverything):
    return await init.should_pin(common_everything)

async def finish(message: Message, common_everything: CommonEverything):
    return await init.finish(common_everything)