from vkbottle.dispatch.rules.base import PayloadRule
from vkbottle.bot import Blueprint, MessageEvent, Message
from vkbottle import GroupEventType

from src.svc.common.keyboard import Payload
from src.svc.common import bps, CommonEverything
from src.svc.vk.keyboard import CMD


bp = Blueprint("common")


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadRule({CMD: Payload.BACK}))
async def back(message: Message, common_everything: CommonEverything):
    return await bps.back(common_everything)

