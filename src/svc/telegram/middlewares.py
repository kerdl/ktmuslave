from loguru import logger
from aiogram.types import Update, Message, CallbackQuery
from typing import Callable, Any, Awaitable

from src.svc.common import ctx, CommonMessage, CommonEvent, CommonEverything


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
        logger.info("CtxCheck")

        if event.event_type == "message":
            chat = event.message.chat
        elif event.event_type == "callback_query":
            chat = event.callback_query.message.chat

        if ctx.tg.get(chat.id) is None:
            ctx.add_tg(chat)

        return await handler(event, data)

class CommonMessageMaker:
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any]
    ) -> Any:
        """
        ## Makes `CommonMessage` from vk message and sends it to a handler
        """
        logger.info("CommonMessageMaker")

        common_message = CommonMessage.from_tg(event)
        common_everything = CommonEverything.from_message(common_message)

        data["common_message"] = common_message
        data["common_everything"] = common_everything

        return await handler(event, data)

class CommonEventMaker:
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any]
    ) -> Any:
        logger.info("CommonEventMaker")

        common_event = CommonEvent.from_tg_callback_query(event)
        common_everything = CommonEverything.from_event(common_event)

        data["common_event"] = common_event
        data["common_everything"] = common_everything

        return await handler(event, data)

        