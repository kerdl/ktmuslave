from loguru import logger
from aiogram.types import Chat as TgChat
from dataclasses import dataclass

from .navigator import Navigator
from .states.tree import Init, Hub


@dataclass
class VkCtx:
    peer_id: int
    navigator = Navigator(init_trace=[Init.I_MAIN], hub_trace=[Hub.I_MAIN])

@dataclass
class TgCtx:
    chat: TgChat
    navigator = Navigator(init_trace=[Init.I_MAIN], hub_trace=[Hub.I_MAIN])

@dataclass
class Ctx:
    vk: dict[int, VkCtx]
    tg: dict[int, TgCtx]

    def add_vk(self, peer_id: int):
        self.vk[peer_id] = VkCtx(peer_id)
        logger.info("created ctx for vk {}", peer_id)
        logger.info(self)

    def add_tg(self, chat: TgChat):
        self.tg[chat.id] = TgCtx(chat)
        logger.info("created ctx for tg {}", chat.id)
        logger.info(self)
