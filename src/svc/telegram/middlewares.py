from loguru import logger
from aiogram.types import Update, Message, CallbackQuery, Chat
from typing import Callable, Any, Awaitable, Optional

from src import defs
from src.svc import telegram as tg
from src.svc.common import ctx, CommonMessage, CommonEvent, CommonEverything, messages
from src.svc.common.states.tree import Init


def get_chat(event: Update) -> Optional[Chat]:
    if event.event_type == tg.EventType.MESSAGE:
        return event.message.chat
    if event.event_type == tg.EventType.CALLBACK_QUERY:
        return event.callback_query.message.chat

class Log:
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any]
    ) -> Any:
        logger.info(f"tg message: {event}")
        return await handler(event, data)

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

        is_group_chat = tg.is_group_chat(event.chat.type)

        def did_user_used_bot_command() -> bool:
            if event.text is None:
                return False
            
            if event.text == "/":
                return False
            elif "/" in event.text:
                return True
            
            return False
    
            if event.entities is None:
                return False
            
            commands = tg.extract_commands(event.entities, event.text)

            for command in commands:
                if defs.tg_bot_mention in command:
                    return True
            
            return False

        def did_user_mentioned_bot() -> bool:
            if event.entities is None:
                return False

            mentions = tg.extract_mentions(event.entities, event.text)

            # if our bot not in mentions
            if defs.tg_bot_mention not in mentions:
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

        chat = get_chat(event)
        user_ctx = ctx.tg.get(chat.id)

        if user_ctx is None:
            user_ctx = ctx.add_tg(chat)

        if not tg.is_group_chat(chat.type):
            user_ctx.navigator.ignored.add(Init.II_SHOULD_PIN)

        return await handler(event, data)

class Throttling:
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any]
    ):
        return await handler(event, data)

        chat = get_chat(event)

        chat_ctx = ctx.tg.get(chat.id)
        await chat_ctx.throttle()

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

        common_event = CommonEvent.from_tg(event)
        common_everything = CommonEverything.from_event(common_event)

        data["common_event"] = common_event
        data["everything"] = common_everything

        return await handler(event, data)

class OldMessagesBlock:
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any]
    ):
        common_event: CommonEvent = data["common_event"]

        this_message_id = common_event.message_id
        last_message_id = common_event.ctx.last_bot_message_id

        if this_message_id != last_message_id:
            await common_event.show_notification(
                messages.format_cant_press_old_buttons()
            )
            return
        
        return await handler(event, data)