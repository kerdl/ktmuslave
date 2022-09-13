from aiogram.types import CallbackQuery

from src import defs
from src.svc.common import bps
from src.svc.common import CommonEverything
from src.svc.common.keyboard import Payload
from src.svc.telegram.filter import CallbackFilter


r = defs.tg_router


@r.callback_query(CallbackFilter(data=Payload.BACK))
async def back(callback_query: CallbackQuery, common_everything: CommonEverything):
    return await bps.back(common_everything)