from loguru import logger

from src import defs
from src.svc.common import CommonEverything
from src.svc.common.router import r, Middleware, MessageMiddleware, EventMiddleware


@r.middleware()
class Log(Middleware):
    async def pre(self, everything: CommonEverything):
        async def log():
            src = everything.src.upper()
            event_src = everything.event_src.upper()
            first_name, last_name, nickname = await everything.sender_name()
            chat_id = everything.chat_id

            event_str = str(everything.corresponding).replace("<", "\<")

            logger.opt(colors=True).info(
                f"<W><k><d>{src} {event_src} from {first_name} {last_name} ({nickname}) at {chat_id}</></></>: {event_str}"
            )
        
        defs.create_task(log())

@r.middleware()
class BotMentionFilter(MessageMiddleware):
    async def pre(self, everything: CommonEverything):
        if not everything.is_for_bot():
            self.stop()

@r.middleware()
class CtxCheck(Middleware):
    async def pre(self, everything: CommonEverything):
        if not await defs.ctx.is_added(everything):
            everything.set_ctx(await defs.ctx.add_from_everything(everything))
        else:
            await everything.load_ctx()

@r.middleware()
class Throttling(Middleware):
    async def pre(self, everything: CommonEverything):
        await everything.ctx.throttle()

@r.middleware()
class OldMessagesBlock(EventMiddleware):
    async def pre(self, everything: CommonEverything):
        from src.svc.common.bps import hub
        from src.svc.common import messages, keyboard as kb
        from src.svc.common.states.tree import HUB

        common_event = everything.event
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
                return

            elif common_event.payload == kb.Payload.SETTINGS:
                user_ctx.navigator.jump_back_to_or_append(HUB.I_MAIN)
                user_ctx.last_bot_message.can_edit = False

                await common_event.show_notification(
                    messages.format_sent_as_new_message()
                )

                return

            elif not user_ctx.last_bot_message.can_edit:
                await hub.to_hub(
                    user_ctx.last_everything,
                    allow_edit = False
                )
                
                self.stop()

            await common_event.show_notification(
                messages.format_cant_press_old_buttons()
            )

            # send last bot message again
            user_ctx.last_bot_message = await user_ctx.last_bot_message.send()

            return
