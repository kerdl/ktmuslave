from loguru import logger
from typing import Optional
from dataclasses import dataclass
from aiogram.types import Chat as TgChat
from vkbottle_types.responses.messages import MessagesSendUserIdsResponseItem

from .navigator import Navigator
from .states.tree import Init, Hub


@dataclass
class VkCtx:
    peer_id: int
    navigator: Navigator

@dataclass
class TgCtx:
    chat: TgChat
    navigator: Navigator

@dataclass
class Ctx:
    vk: dict[int, VkCtx]
    tg: dict[int, TgCtx]

    def add_vk(self, peer_id: int):
        self.vk[peer_id] = VkCtx(peer_id, Navigator([Init.I_MAIN]))
        logger.info("created ctx for vk {}", peer_id)
        logger.info(self)

    def add_tg(self, chat: TgChat):
        self.tg[chat.id] = TgCtx(chat, Navigator([Init.I_MAIN]))
        logger.info("created ctx for tg {}", chat.id)
        logger.info(self)
