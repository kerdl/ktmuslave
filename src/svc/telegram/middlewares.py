from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message

from src.svc.common import ctx
from src.svc.common.context import TgCtx


class CtxCheck(BaseMiddleware):
    """
    ## Checks if user is in context and initializes it, if not
    """
    async def on_process_message(self, message: Message, data: dict):
        id = message.chat.id

        if not ctx.tg.get(id):
            ctx.tg[id] = TgCtx(message.chat)

        print(ctx)
