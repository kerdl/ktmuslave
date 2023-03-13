from loguru import logger

from src import defs
from src.svc.common import CommonEverything, messages
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
            added_ctx = await defs.ctx.add_from_everything(everything)
            everything.set_ctx(added_ctx)
        else:
            await everything.load_ctx()
            everything.ctx.last_everything = everything
            everything.ctx.navigator.set_everything(everything)

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
        if common_event.ctx.last_bot_message is None:
            last_message_id = None
        else:
            last_message_id = common_event.ctx.last_bot_message.id

        if this_message_id != last_message_id:
            if common_event.payload in [
                kb.Payload.WEEKLY,
                kb.Payload.DAILY,
                kb.Payload.UPDATE,
                kb.Payload.RESEND,
            ]:
                return

            if common_event.payload == kb.Payload.RESET and last_message_id is None:
                return

            elif common_event.payload == kb.Payload.SETTINGS:
                user_ctx.navigator.jump_back_to_or_append(HUB.I_MAIN)
                user_ctx.last_bot_message.can_edit = False

                return

            elif not user_ctx.last_bot_message.can_edit:
                await hub.to_hub(
                    user_ctx.last_everything,
                    allow_edit = False
                )
                
                self.stop_pre()

            await common_event.show_notification(
                messages.format_cant_press_old_buttons()
            )

            # send last bot message again
            msg = await user_ctx.last_bot_message.send()
            await user_ctx.set_last_bot_message(msg)

            self.stop_pre()

@r.middleware()
class ShowNotImplementedError(Middleware):
    async def post(self, everything: CommonEverything):
        try:
            if not everything.was_processed and everything.is_from_event:
                await everything.event.show_notification(
                    messages.format_not_implemented_error()
                )
        except Exception:
            ...

@r.middleware()
class SaveCtxToDb(Middleware):
    async def post(self, everything: CommonEverything):
        logger.success(f"saving {everything.ctx.db_key} ctx")
        await everything.ctx.save()
        logger.success(f"del {everything.ctx.db_key} ctx")
        everything.del_ctx()