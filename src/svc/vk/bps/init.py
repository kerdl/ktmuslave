from vkbottle.bot import Blueprint, Message

from svc.common.states.tree import Init
from svc.common import CommonMessage
from svc.common.bps import init
from svc.vk import rule

bp = Blueprint(name="init")

@bp.on.message(rule.StateRule(Init.I_MAIN))
async def main(message: Message, common_message: CommonMessage):
    return await init.main(common_message)