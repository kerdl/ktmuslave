from loguru import logger
from vkbottle import GroupEventType
from vkbottle.bot import Blueprint, Message, MessageEvent
from vkbottle.dispatch.rules.base import PayloadRule

from src.svc.common.states.tree import Init
from src.svc.common.keyboard import Payload
from src.svc.common import CommonEverything
from src.svc.common.bps import init
from src.svc.vk import rule
from src.svc.vk.keyboard import CMD


bp = Blueprint(name="init")


@bp.on.message(rule.StateRule(Init.I_MAIN))
async def main(message: Message, common_everything: CommonEverything):
    return await init.main(common_everything)

@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadRule({CMD: Payload.BEGIN}))
async def begin(event: MessageEvent, common_everything: CommonEverything):
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