from vkbottle.bot import Message as VkMessage
from aiogram.types import Message as TgMessage
from dataclasses import dataclass
from typing import Optional
from loguru import logger

from .context import Ctx, TgCtx, VkCtx


ctx = Ctx({}, {})

class MessageSource:
    VK = "vk"
    TG = "tg"

@dataclass
class CommonMessage:
    src: str

    vk: Optional[VkMessage] = None
    vk_ctx: Optional[VkCtx] = None

    tg: Optional[TgMessage] = None
    tg_ctx: Optional[TgCtx] = None

    is_group_chat: Optional[bool] = None

    @classmethod
    async def from_vk(cls, message: VkMessage):
        self = cls(
            src=MessageSource.VK,
            vk=message,
            vk_ctx=ctx.vk.get(message.peer_id),
            is_group_chat=message.peer_id != message.from_id
        )

        return self
    
    @classmethod
    async def from_tg(cls, message: TgMessage):
        self = cls(
            src=MessageSource.TG,
            tg=message,
            tg_ctx=ctx.tg.get(message.chat.id),
            is_group_chat=message.chat.type in ["group", "supergroup", "channel"]
        )

        return self

    @property
    def main_ctx(self):
        return ctx

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
    