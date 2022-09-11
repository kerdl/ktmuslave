from loguru import logger
from aiogram.types import Update, Message
from typing import Callable, Any, Awaitable

from svc.common import ctx, CommonMessage


class CtxCheck:
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any]
    ):
        """
        ## Checks if user is in context and initializes it, if not
        """
        logger.info("ctx_check")

        match event.event_type:
            case "message":
                chat = event.message.chat
            case "callback_query":
                chat = event.callback_query.message.chat

        if ctx.tg.get(chat.id) is None:
            ctx.add_tg(chat)

        return await handler(event, data)

class CommonMessageMaker:
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any]
    ) -> Any:
        """
        ## Makes `CommonMessage` from vk message and sends it to a handler
        """
        logger.info("common_message_maker")

        data["common_message"] = CommonMessage.from_tg(event)
        return await handler(event, data)

