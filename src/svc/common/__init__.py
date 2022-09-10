from loguru import logger
from typing import Any, Literal, Optional
from dataclasses import dataclass
from vkbottle.bot import Message as VkMessage, MessageEvent as VkMessageEvent
from aiogram.types import Message as TgMessage

from svc.vk.types import RawEvent
from .context import Ctx, TgCtx, VkCtx


ctx = Ctx({}, {})

class Source:
    VK = "vk"
    TG = "tg"

SOURCE_LITERAL = Literal["vk", "tg"]

@dataclass
class CommonMessage:
    src: SOURCE_LITERAL

    vk: Optional[VkMessage] = None
    vk_ctx: Optional[VkCtx] = None

    tg: Optional[TgMessage] = None
    tg_ctx: Optional[TgCtx] = None

    is_group_chat: Optional[bool] = None

    @classmethod
    def from_vk(cls, message: VkMessage):
        self = cls(
            src=Source.VK,
            vk=message,
            vk_ctx=ctx.vk.get(message.peer_id),
            is_group_chat=message.peer_id != message.from_id
        )

        return self
    
    @classmethod
    def from_tg(cls, message: TgMessage):
        self = cls(
            src=Source.TG,
            tg=message,
            tg_ctx=ctx.tg.get(message.chat.id),
            is_group_chat=message.chat.type in ["group", "supergroup", "channel"]
        )

        return self

    @property
    def main_ctx(self):
        return ctx

@dataclass
class CommonEvent:
    src: SOURCE_LITERAL

    vk: Optional[RawEvent] = None
    vk_ctx: Optional[VkCtx] = None

    is_group_chat: Optional[bool] = None

    @classmethod
    def from_vk(cls, event: RawEvent):
        event_object = event["object"]
        peer_id = event_object["peer_id"]
        user_id = event_object["user_id"]

        self = cls(
            src=Source.VK,
            vk=event,
            vk_ctx=ctx.vk.get(peer_id),
            is_group_chat=peer_id != user_id
        )

        return self
    

def run_forever():
    """
    ## Run all services
    """
    from src import defs

    loop = defs.loop

    vk = defs.vk_bot
    tg = defs.tg_dispatch
    tg_bot = defs.tg_bot

    loop.create_task(tg.start_polling(tg_bot))
    loop.create_task(vk.run_polling())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("keyboard interrupt")
    