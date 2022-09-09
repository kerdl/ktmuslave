from aiogram.types import Message

from src import defs
from svc.common.states.tree import Init
from svc.common import CommonMessage
from svc.common.bps import init

dp = defs.tg_dispatch

@dp.message_handler()
async def main(message: Message, common_message: CommonMessage):
    return await init.main(common_message)