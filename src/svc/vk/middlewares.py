from loguru import logger
from vkbottle import BaseMiddleware, ShowSnackbarEvent
from vkbottle.bot import Message

from src import defs
from src.svc import vk
from src.svc.common import CommonMessage, CommonEvent, CommonEverything, messages
from src.svc.common import keyboard as kb
from src.svc.common.states.tree import INIT, SETTINGS, HUB
from .types import RawEvent
from . import keyboard as vk_kb


class LogRaw(BaseMiddleware[RawEvent]):
    async def pre(self):
        try:
            user = await defs.vk_bot.api.users.get(
                [self.event["object"]["user_id"]]
            )

            first_name = user[0].first_name
            last_name = user[0].last_name
            peer_id = self.event["object"]["peer_id"]

            logger.opt(colors=True).info(
                f"<W><k><d>{first_name} {last_name} at {peer_id}</></></> "
                f"vk event: {self.event}"
            )
        except Exception as e:
            logger.warning(f"error while logging raw: {e}")
    
class LogMessage(BaseMiddleware[Message]):
    async def pre(self):
        try:
            user = await self.event.get_user()

            first_name = user.first_name
            last_name = user.last_name
            peer_id = self.event.peer_id

            logger.opt(colors=True).info(
                f"<W><k><d>{first_name} {last_name} at {peer_id}</></></> "
                f"vk event: {self.event}"
            )
        except Exception as e:
            logger.warning(f"error while logging message: {e}")

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

        user_ctx = defs.ctx.vk.get(peer_id)

        if user_ctx is None:
            user_ctx = defs.ctx.add_vk(peer_id)

            if not vk.is_group_chat(peer_id, from_id):
                user_ctx.navigator.ignored.add(SETTINGS.III_SHOULD_PIN)

class CtxCheckMessage(BaseMiddleware[Message]):
    """
    ## Checks if user is in context and initializes it, if not
    ### It's a `message_new` middleware
    """
    async def pre(self):
        peer_id = self.event.peer_id
        from_id = self.event.from_id

        user_ctx = defs.ctx.vk.get(peer_id)

        if user_ctx is None:
            user_ctx = defs.ctx.add_vk(peer_id)

class ThrottleRaw(BaseMiddleware[RawEvent]):
    async def pre(self):
        chat_ctx = defs.ctx.vk.get(self.event["object"]["peer_id"])
        await chat_ctx.throttle()

class ThrottleMessage(BaseMiddleware[Message]):
    async def pre(self):
        chat_ctx = defs.ctx.vk.get(self.event.peer_id)
        await chat_ctx.throttle()

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
        
        if everything.ctx.last_everything is None:
            # this is first event for this ctx
            everything.ctx.set_everything(everything)
            everything.navigator.auto_ignored()
            everything.ctx.settings.defaults_from_everything(everything)
        else:
            everything.ctx.set_everything(everything)

        self.send({"common_event": event})
        self.send({"everything": everything})

class OldMessagesBlock(BaseMiddleware[RawEvent]):
    """
    ## Blocks usage of old messages and buttons
    ### It's a `raw_event` middleware
    """
    async def pre(self):
        user_ctx = defs.ctx.vk.get(self.event["object"]["peer_id"])

        this_message_id = self.event["object"]["conversation_message_id"]
    
        if user_ctx.last_bot_message is not None:
            last_message_id = user_ctx.last_bot_message.id
        else:
            self.stop("no last bot message")

        async def send_snackbar(text: str):
            await defs.vk_bot.api.messages.send_message_event_answer(
                event_id   = self.event["object"]["event_id"],
                user_id    = self.event["object"]["user_id"],
                peer_id    = self.event["object"]["peer_id"],
                event_data = ShowSnackbarEvent(text=text)
            )

        if this_message_id != last_message_id:
            payload = self.event["object"]["payload"]

            if vk_kb.payload_eq(payload, kb.Payload.UPDATE):
                return

            elif vk_kb.payload_eq(payload, kb.Payload.SETTINGS):
                user_ctx.navigator.jump_back_to_or_append(HUB.I_MAIN)
                user_ctx.last_bot_message.can_edit = False
                await send_snackbar(messages.format_sent_as_new_message())

                return

            await send_snackbar(messages.format_cant_press_old_buttons())

            # send last bot message again
            user_ctx.last_bot_message = await user_ctx.last_bot_message.send()

            self.stop()