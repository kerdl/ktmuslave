from aiogram.types import Chat as TgChat


class VkCtx:
    peer_id: int

class TgCtx:
    chat: TgChat

class Ctx:
    vk: dict[int, VkCtx]
    tg: dict[int, VkCtx]

