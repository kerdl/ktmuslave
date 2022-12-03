from loguru import logger
from aiogram.types import Update, Message, CallbackQuery, Chat
from typing import Callable, Any, Awaitable, Optional

from src import defs
from src.svc import telegram as tg
from src.svc.common import CommonMessage, CommonEvent, CommonEverything, messages, keyboard as kb
from src.svc.common.states.tree import INIT, SETTINGS, HUB


def get_chat(event: Update) -> Optional[Chat]:
    if event.event_type == tg.EventType.MESSAGE:
        return event.message.chat
    if event.event_type == tg.EventType.CALLBACK_QUERY:
        return event.callback_query.message.chat

class Log:
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any]
    ) -> Any:
        try:
            def fmt(username: str, first_name: str, last_name: str):
                event_str = str(event).replace("<", "\<")

                logger.opt(colors=True).info(
                    f"<W><k><d>{first_name} {last_name} ({username})</></></> tg event: {event_str}"
                )

            if event.callback_query is not None:
                username = event.callback_query.from_user.username
                first_name = event.callback_query.from_user.first_name
                last_name = event.callback_query.from_user.last_name

                fmt(username, first_name, last_name)

            elif event.message is not None:
                username = event.message.from_user.username
                first_name = event.message.from_user.first_name
                last_name = event.message.from_user.last_name

                fmt(username, first_name, last_name)
            else:
                logger.opt(colors=True).info(f"tg event: {event}")

        except Exception as e:
            logger.warning(f"error logging tg: {e}")

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

        def is_invite() -> bool:
            if event.content_type != "new_chat_members":
                return False
            
            for new in event.new_chat_members:
                if new.id == defs.tg_bot_info.id:
                    return True
            
            return False

        def did_user_used_bot_command() -> bool:
            if event.text is None:
                return False
            
            if event.text == "/":
                return False
            elif any(cmd in event.text for cmd in defs.tg_bot_commands):
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

        if not is_invite() and (is_group_chat and not (
            did_user_used_bot_command() or
            did_user_mentioned_bot() or
            did_user_replied_to_bot_message()
        )):
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

        chat = get_chat(event)

        if chat is None:
            return

        user_ctx = defs.ctx.tg.get(chat.id)

        if user_ctx is None:
            user_ctx = defs.ctx.add_tg(chat)

        return await handler(event, data)

class Throttling:
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any]
    ):
        chat = get_chat(event)

        chat_ctx = defs.ctx.tg.get(chat.id)
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
        ## Makes `CommonMessage` from tg message and sends it to a handler
        """

        common_message = CommonMessage.from_tg(event)
        common_everything = CommonEverything.from_message(common_message)

        if common_everything.ctx.last_everything is None:
            # this is first event for this ctx
            common_everything.ctx.set_everything(common_everything)
            common_everything.navigator.auto_ignored()
            common_everything.ctx.settings.defaults_from_everything(common_everything)
        else:
            common_everything.ctx.set_everything(common_everything)

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

        common_event = CommonEvent.from_tg(event)
        common_everything = CommonEverything.from_event(common_event)
    
        if common_everything.ctx.last_everything is None:
            # this is first event for this ctx
            common_everything.ctx.set_everything(common_everything)
            common_everything.navigator.auto_ignored()
            common_everything.ctx.settings.defaults_from_everything(common_everything)
        else:
            common_everything.ctx.set_everything(common_everything)


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
        from src.svc.common.bps import hub

        common_event: CommonEvent = data["common_event"]
        user_ctx = common_event.ctx

        this_message_id = common_event.message_id
        last_message_id = common_event.ctx.last_bot_message.id

        if this_message_id != last_message_id:
            
            if common_event.payload in [
                kb.Payload.WEEKLY,
                kb.Payload.DAILY,
                kb.Payload.UPDATE,
                kb.Payload.RESEND
            ]:
                return await handler(event, data)

            elif common_event.payload == kb.Payload.SETTINGS:
                user_ctx.navigator.jump_back_to_or_append(HUB.I_MAIN)
                user_ctx.last_bot_message.can_edit = False

                await common_event.show_notification(
                    messages.format_sent_as_new_message()
                )

                return await handler(event, data)

            elif not user_ctx.last_bot_message.can_edit:
                await hub.to_hub(
                    user_ctx.last_everything,
                    allow_edit = False
                )
                
                return

            await common_event.show_notification(
                messages.format_cant_press_old_buttons()
            )

            # send last bot message again
            user_ctx.last_bot_message = await user_ctx.last_bot_message.send()

            return
        
        return await handler(event, data)
