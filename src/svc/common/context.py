from aiogram.types import Chat as TgChat
from dataclasses import dataclass

from .navigator import Navigator
from .states import Init, Hub


@dataclass
class VkCtx:
    peer_id: int
    navigator = Navigator(init_trace=[Init.MAIN], hub_trace=[Hub.MAIN])

@dataclass
class TgCtx:
    chat: TgChat
    navigator = Navigator(init_trace=[Init.MAIN], hub_trace=[Hub.MAIN])

@dataclass
class Ctx:
    vk: dict[int, VkCtx]
    tg: dict[int, VkCtx]

