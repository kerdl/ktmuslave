from vkbottle import BaseMiddleware
from vkbottle.bot import Message

from svc.common import ctx, CommonMessage


class CommonMessageMaker(BaseMiddleware[Message]):
    """
    ## Makes `CommonMessage` from vk message and sends it to a handler
    """
    async def pre(self):
        message = await CommonMessage.from_vk(self.event)
        self.send({"common_message": message})

class CtxCheck(BaseMiddleware[Message]):
    """
    ## Checks if user is in context and initializes it, if not
    """
    async def pre(self):
        peer_id = self.event.peer_id

        if ctx.vk.get(peer_id) is None:
            ctx.add_vk(peer_id)
