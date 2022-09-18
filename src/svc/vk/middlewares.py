from vkbottle import BaseMiddleware, BotPolling
from vkbottle.bot import Message

from src import defs
from src.svc.common import ctx, CommonMessage, CommonEvent, CommonEverything
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

        if ctx.vk.get(peer_id) is None:
            ctx.add_vk(peer_id)

class CtxCheckMessage(BaseMiddleware[Message]):
    """
    ## Checks if user is in context and initializes it, if not
    ### It's a `message_new` middleware
    """
    async def pre(self):
        peer_id = self.event.peer_id

        if ctx.vk.get(peer_id) is None:
            ctx.add_vk(peer_id)

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