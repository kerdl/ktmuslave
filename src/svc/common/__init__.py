from vkbottle.bot import Message as VkMessage
from aiogram.types import Message as TgMessage
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

    @classmethod
    async def from_vk(cls, message: VkMessage):
        self = cls(
            src=MessageSource.VK,
            vk=message
        )

        return self
    
    @classmethod
    async def from_tg(cls, message: VkMessage):
        self = cls(
            src=MessageSource.TG,
            tg=message
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

    loop.create_task(tg.start_polling())
    loop.create_task(vk.run_polling())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("keyboard interrupt")
    