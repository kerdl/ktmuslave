from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message

from svc.common import ctx, CommonMessage


class CommonMessageMaker(BaseMiddleware):
    """
    ## Makes `CommonMessage` from vk message and sends it to a handler
    """
    async def on_process_message(self, message: Message, data: dict):
        message = await CommonMessage.from_tg(message)
        data["common_message"] = message

class CtxCheck(BaseMiddleware):
    """
    ## Checks if user is in context and initializes it, if not
    """
    async def on_process_message(self, message: Message, data: dict):
        chat = message.chat

        if ctx.tg.get(chat.id) is None:
            ctx.add_tg(chat)
