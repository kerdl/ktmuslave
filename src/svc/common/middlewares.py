from loguru import logger

from src import defs
from src.svc.common import CommonEverything, messages, keyboard as kb
from src.svc.common.router import router, Middleware, MessageMiddleware, EventMiddleware


@router.middleware()
class Log(Middleware):
    async def pre(self, everything: CommonEverything):
        async def log():
            src = everything.src.upper()
            event_src = everything.event_src.upper()
            name = await everything.sender_name()
            if name:
                first_name, last_name, nickname = name
            else:
                first_name, last_name, nickname = (None, None, None)
            chat_id = everything.chat_id

            event_str = str(everything.corresponding).replace("<", "\<")

            logger.opt(colors=True).info(
                f"<W><k><d>{src} {event_src} from {first_name} {last_name} ({nickname}) at {chat_id}</></></>: {event_str}"
            )

            await defs.logger.log_everything(everything)
        
        defs.create_task(log())

@router.middleware()
class BotMentionFilter(Middleware):
    async def pre(self, everything: CommonEverything):
        if not everything.is_for_bot():
            self.stop()

@router.middleware()
class CtxCheck(Middleware):
    async def pre(self, everything: CommonEverything):
        if not await defs.is_redis_online():
            logger.error("redis instance is offline, aborting...")
            self.stop()
            
        if not await defs.ctx.is_added(everything):
            added_ctx = await defs.ctx.add_from_everything(everything)
            everything.set_ctx(added_ctx)
        else:
            await everything.load_ctx()
            everything.ctx.last_everything = everything
            everything.ctx.navigator.set_everything(everything)

@router.middleware()
class Throttling(Middleware):
    async def pre(self, everything: CommonEverything):
        await everything.ctx.throttle()

@router.middleware()
class ManualUpdateBlock(EventMiddleware):
    async def pre(self, everything: CommonEverything):
        if everything.event.payload != kb.Payload.UPDATE:
            return
        
        await everything.event.show_notification(
            messages.format_manual_updates_are_disabled()
        )
        await self.stop_pre()

@router.middleware()
class OldMessagesBlock(EventMiddleware):
    async def pre(self, everything: CommonEverything):
        from src.svc.common.bps import hub, init
        from src.svc.common.states.tree import HUB, INIT

        async def resend_last_bot_message():
            await common_event.show_notification(
                messages.format_cant_press_old_buttons()
            )

            if user_ctx.last_bot_message is not None:
                # send last bot message again
                msg = await user_ctx.last_bot_message.send()
                await user_ctx.set_last_bot_message(msg)
            else:
                await init.main(everything, force_send=True)
        
        common_event = everything.event
        user_ctx = common_event.ctx

        this_message_id = common_event.message_id
        if common_event.ctx.last_bot_message is None:
            last_message_id = None
            last_message_can_edit = False
        else:
            last_message_id = common_event.ctx.last_bot_message.id
            last_message_can_edit = common_event.ctx.last_bot_message.can_edit

        if this_message_id != last_message_id:
            if everything.ctx.is_registered:
                if common_event.payload in [
                    kb.Payload.UPDATE,
                    kb.Payload.RESEND,
                ]:
                    return

                elif common_event.payload == kb.Payload.SETTINGS:
                    user_ctx.navigator.jump_back_to_or_append(HUB.I_MAIN)
                    user_ctx.last_bot_message.can_edit = False

                    return
                elif not last_message_can_edit:
                    user_ctx.navigator.jump_back_to_or_append(HUB.I_MAIN)
                    await hub.hub(everything, allow_edit=False)
                    self.stop_pre()
                else:
                    await resend_last_bot_message()
                    self.stop_pre()
            else:
                if common_event.payload == kb.Payload.RESET and last_message_id is None:
                    return
                
                await resend_last_bot_message()
                self.stop_pre()


@router.middleware()
class ShowNotImplementedError(Middleware):
    async def post(self, everything: CommonEverything):
        try:
            if not everything.was_processed and everything.is_from_event:
                await everything.event.show_notification(
                    messages.format_not_implemented_error()
                )
        except Exception:
            ...

@router.middleware()
class SaveCtxToDb(Middleware):
    async def post(self, everything: CommonEverything):
        logger.debug(f"saving {everything.ctx.db_key} ctx")
        await everything.ctx.save()
        logger.debug(f"del {everything.ctx.db_key} ctx")
        everything.del_ctx()