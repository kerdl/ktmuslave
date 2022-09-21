from loguru import logger
from aiogram.types import Update, Message, CallbackQuery, MessageEntity
from typing import Callable, Any, Awaitable

from src import defs
from src.svc import telegram as tg
from src.svc.common import ctx, CommonMessage, CommonEvent, CommonEverything


class BotMentionFilter:
    """
    ## Filtering off messages that doesn't mention us

    - If we were granted with admin permissions
    in group chat, we can view every single message
    there

    - We don't want to answer to every single
    message there

    - We'll only answer to messages dedicated to us
    """
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any]
    ) -> Any:
        BOT_MENTION = f"@{defs.tg_bot_info.username}"

        is_group_chat = tg.is_group_chat(event.chat.type)

        def did_user_used_bot_command() -> bool:
            if event.text == "/":
                return False
            elif "/" in event.text:
                return True
            
            return False
    
            if event.entities is None:
                return False
            
            commands = tg.extract_commands(event.entities, event.text)

            for command in commands:
                if BOT_MENTION in command:
                    return True
            
            return False

        def did_user_mentioned_bot() -> bool:
            if event.entities is None:
                return False

            mentions = tg.extract_mentions(event.entities, event.text)

            # if our bot not in mentions
            if BOT_MENTION not in mentions:
                return False

            return True

        def did_user_replied_to_bot_message() -> bool:
            if event.reply_to_message is None:
                return False

            return event.reply_to_message.from_user.id == defs.tg_bot_info.id

        if (
            is_group_chat and not (
                did_user_used_bot_command() or
                did_user_mentioned_bot() or
                did_user_replied_to_bot_message()
            )
        ):
            return

        return await handler(event, data)

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
        data["everything"] = common_everything

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
        data["everything"] = common_everything

        return await handler(event, data)

        