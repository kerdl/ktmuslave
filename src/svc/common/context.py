from loguru import logger
from dataclasses import dataclass
from aiogram.types import Chat as TgChat
from typing import Optional
import time
import asyncio

from src.svc.common.states import State
from src.data import Settings, Group
from .navigator import Navigator
from .states.tree import Init, Hub


@dataclass
class BaseCtx:
    navigator: Navigator
    settings: Settings
    last_call: float
    """ ## Last UNIX time when user interacted with bot """
    last_bot_message_id: Optional[int]

    async def throttle(self) -> None:
        """ ## Stop executing for a short period to avoid rate limit """

        current_time = time.time()

        # allowed to call again after 2 seconds
        next_allowed_time = self.last_call + 2

        if next_allowed_time > current_time:
            # then throttle
            logger.warning("TROLLING")
            sleep_secs_until_allowed: float = next_allowed_time - current_time

            await asyncio.sleep(sleep_secs_until_allowed)

        self.last_call = current_time

@dataclass
class VkCtx(BaseCtx):
    peer_id: int

@dataclass
class TgCtx(BaseCtx):
    chat: TgChat

@dataclass
class Ctx:
    vk: dict[int, VkCtx]
    tg: dict[int, TgCtx]


    def add_vk(self, peer_id: int) -> None:
        navigator = Navigator([Init.I_MAIN], [], set())
        settings = Settings(Group())

        self.vk[peer_id] = VkCtx(
            navigator           = navigator, 
            settings            = settings, 
            last_call           = time.time(), 
            last_bot_message_id = None,
            peer_id             = peer_id
        )

        logger.info("created ctx for vk {}", peer_id)

        return self.vk[peer_id]

    def add_tg(self, chat: TgChat) -> None:
        navigator = Navigator([Init.I_MAIN], [], set())
        settings = Settings(Group())

        self.tg[chat.id] = TgCtx(
            navigator           = navigator, 
            settings            = settings, 
            last_call           = time.time(), 
            last_bot_message_id = None,
            chat                = chat
        )

        logger.info("created ctx for tg {}", chat.id)

        return self.tg[chat.id]
