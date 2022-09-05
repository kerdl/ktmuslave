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
    tg: dict[int, VkCtx]

