from vkbottle.bot import Message as VkMessage
from aiogram.types import Message as TgMessage
from aiogram.types.chat import ChatType
from dataclasses import dataclass
from typing import Optional
from loguru import logger

from .context import Ctx


ctx = Ctx({}, {})

class MessageSource:
    VK = "vk"
    TG = "tg"

@dataclass
class CommonMessage:
    src: str
    vk: Optional[VkMessage] = None
    tg: Optional[TgMessage] = None
    is_group_chat: Optional[bool] = None

    @classmethod
    async def from_vk(cls, message: VkMessage):
        self = cls(
            src=MessageSource.VK,
            vk=message,
            is_group_chat=message.peer_id != message.from_id
        )

        return self
    
    @classmethod
    async def from_tg(cls, message: TgMessage):
        self = cls(
            src=MessageSource.TG,
            tg=message,
            is_group_chat=message.chat.type in [ChatType.GROUP, ChatType.CHANNEL]
        )

        return self

    @property
    def ctx(self):
        return ctx

def run_forever():
    """
    ## Run all services
    """
    from src import defs

    loop = defs.loop

    vk = defs.vk_bot
    tg = defs.tg_dispatch

    loop.create_task(tg.start_polling())
    loop.create_task(vk.run_polling())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("keyboard interrupt")
    