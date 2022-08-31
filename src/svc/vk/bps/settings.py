from vkbottle.bot import Blueprint, Message

from src.svc.common import CommonMessage
from src.svc.common.bps import settings

bp = Blueprint(name="settings")

@bp.on.message()
async def test(message: Message):
    print("oi vk message")
    m = await CommonMessage.from_vk(message)
    return await settings.test(m)