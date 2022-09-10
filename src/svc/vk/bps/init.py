from loguru import logger
from vkbottle import GroupEventType
from vkbottle.bot import Blueprint, Message, MessageEvent
from vkbottle.dispatch.rules.base import PayloadRule

from svc.common.context import VkCtx
from svc.common.states.tree import Init
from svc.common import CommonMessage, CommonEvent
from svc.common.bps import init
from svc.vk import rule

bp = Blueprint(name="init")


@bp.on.message(rule.StateRule(Init.I_MAIN))
async def main(message: Message, common_message: CommonMessage):
    return await init.main(common_message)

@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadRule({"cmd": "begin"}))
async def begin(event: MessageEvent, common_event: CommonEvent):
    return await init.begin(common_event)

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