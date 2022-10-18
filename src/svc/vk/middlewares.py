from vkbottle import BaseMiddleware, ShowSnackbarEvent
from vkbottle.bot import Message

from src import defs
from src.svc import vk
from src.svc.common import ctx, CommonMessage, CommonEvent, CommonEverything, messages
from src.svc.common.states.tree import Init, Settings
from .types import RawEvent


class BotMentionFilter(BaseMiddleware[Message]):
    """
    ## Filtering off messages that doesn't mention us

    - If we were granted with admin permissions
    in group chat, we can view every single message
    there

    - We don't want to answer to every single
    message there

    - We'll only answer to messages dedicated to us
    """
    async def pre(self):
        is_group_chat = self.event.peer_id != self.event.from_id
        bot_id = defs.vk_bot_info.id
        negative_bot_id = -bot_id
        
        def did_user_mentioned_bot() -> bool:
            """ 
            ## @<bot id> <message> 
            ### `@<bot id>` is a mention
            """
            return self.event.is_mentioned
        
        def did_user_replied_to_bot_message() -> bool:
            """ ## When you press on bot's message and then `Reply` button """
            reply_message = self.event.reply_message

            if reply_message is None:
                return False

            return reply_message.from_id == negative_bot_id

        if (
            is_group_chat and not (
                did_user_mentioned_bot() or
                did_user_replied_to_bot_message()
            )
        ):
            self.stop("message blocked, this message is not for the bot")

class CtxCheckRaw(BaseMiddleware[RawEvent]):
    """
    ## Checks if user is in context and initializes it, if not
    ### It's a `raw_event` middleware
    """
    async def pre(self):
        event_object = self.event["object"]
        peer_id = event_object["peer_id"]
        from_id = event_object["user_id"]

        user_ctx = ctx.vk.get(peer_id)

        if user_ctx is None:
            user_ctx = ctx.add_vk(peer_id)

        if not vk.is_group_chat(peer_id, from_id):
            user_ctx.navigator.ignored.add(Settings.II_SHOULD_PIN)

class CtxCheckMessage(BaseMiddleware[Message]):
    """
    ## Checks if user is in context and initializes it, if not
    ### It's a `message_new` middleware
    """
    async def pre(self):
        peer_id = self.event.peer_id
        from_id = self.event.from_id

        user_ctx = ctx.vk.get(peer_id)

        if user_ctx is None:
            user_ctx = ctx.add_vk(peer_id)
        
        user_ctx.navigator.ignored.add(Settings.I_MAIN)
        
        if not vk.is_group_chat(peer_id, from_id):
            user_ctx.navigator.ignored.add(Settings.II_SHOULD_PIN)

class CommonMessageMaker(BaseMiddleware[Message]):
    """
    ## Makes `CommonMessage` from vk message and sends it to a handler
    ### It's a `message_new` middleware
    """
    async def pre(self):
        message = CommonMessage.from_vk(self.event)
        everything = CommonEverything.from_message(message)
        
        self.send({"common_message": message})
        self.send({"everything": everything})

class CommonEventMaker(BaseMiddleware[RawEvent]):
    """
    ## Makes `CommonEvent` from vk event and sends it to a handler
    ### It's a `raw_event` middleware
    """
    async def pre(self):
        event = CommonEvent.from_vk(self.event)
        everything = CommonEverything.from_event(event)
        
        self.send({"common_event": event})
        self.send({"everything": everything})

class OldMessagesBlock(BaseMiddleware[RawEvent]):
    """
    ## Blocks usage of old messages and buttons
    ### It's a `raw_event` middleware
    """
    async def pre(self):
        user_ctx = ctx.vk.get(self.event["object"]["peer_id"])

        this_message_id = self.event["object"]["conversation_message_id"]
        last_message_id = user_ctx.last_bot_message.id

        if this_message_id != last_message_id:

            await defs.vk_bot.api.messages.send_message_event_answer(
                event_id   = self.event["object"]["event_id"],
                user_id    = self.event["object"]["user_id"],
                peer_id    = self.event["object"]["peer_id"],
                event_data = ShowSnackbarEvent(text=messages.format_cant_press_old_buttons())
            )

            # send last bot message again
            user_ctx.last_bot_message = await user_ctx.last_bot_message.send()

            self.stop()