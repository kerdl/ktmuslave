from aiogram.types import Message

from src import defs
from src.svc.common import CommonMessage
from src.svc.common.bps import settings

dp = defs.tg_dispatch

@dp.message_handler()
async def test(message: Message):
    print("oi tg message")
    m = await CommonMessage.from_tg(message)
    return await settings.test(m)
    