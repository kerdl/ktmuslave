from vkbottle import BaseMiddleware
from vkbottle.bot import Message

from svc.common import ctx, CommonMessage, CommonEvent
from .types import RawEvent


class GroupMentionFilter(BaseMiddleware[Message]):
    """
    ## Filtering off messages that doesn't mention us

    - If we were granted with admin permissions
    in group chat, we can view every single message
    there

    - We don't want to answer to every single
    message there

    - We'll only answer to those where we are
    mentioned
    """
    async def pre(self):
        is_group_chat = self.event.peer_id != self.event.from_id
        
        if is_group_chat and not self.event.is_mentioned:
            self.stop("message blocked, this is a group chat and we're not mentioned")

class CtxCheckRaw(BaseMiddleware[RawEvent]):
    """
    ## Checks if user is in context and initializes it, if not
    ### It's a `raw_event` middleware
    """
    async def pre(self):
        event_object = self.event["object"]
        peer_id: int = event_object["peer_id"]

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
    ## Makes `CommonEvenr` from vk event and sends it to a handler
    ### It's a `raw_event` middleware
    """
    async def pre(self):
        event = CommonEvent.from_vk(self.event)
        self.send({"common_event": event})

class CommonMessageMaker(BaseMiddleware[Message]):
    """
    ## Makes `CommonMessage` from vk message and sends it to a handler
    ### It's a `message_new` middleware
    """
    async def pre(self):
        message = CommonMessage.from_vk(self.event)
        self.send({"common_message": message})