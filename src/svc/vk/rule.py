from vkbottle import ABCRule
from vkbottle.bot import Message

from svc.common import ctx, checker, error
from svc.common.states import State


class StateRule(ABCRule[Message]):
    def __init__(self, state: State):
        self.state = state
    
    async def check(self, message: Message) -> bool:
        # get chat id from message and find context for it
        id = message.peer_id
        user_ctx = ctx.vk.get(id)

        # contexts are created by middlewares,
        # before ANY handler, so no context
        # is definitely an error
        if user_ctx is None:
            raise error.NoContext(
                f"no context for vk {id=}, check middlewares that init context"
            )
        
        is_user_on_this_state = await checker.is_user_on_state(user_ctx.navigator, self.state)

        return is_user_on_this_state