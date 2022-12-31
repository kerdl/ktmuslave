from loguru import logger
from dataclasses import dataclass, field
from vkbottle import BaseMiddleware
from vkbottle.bot import Message as VkMessage
from aiogram import Dispatcher
from aiogram.types import Update, Message as TgMessage, CallbackQuery, Chat
from typing import Callable, Any, Awaitable, Optional
from typing import Literal

from src import defs
from src.svc.common import CommonEverything, CommonEvent, CommonMessage
from src.svc.vk.types_ import RawEvent


class Order:
    PRE = "pre"
    POST = "post"

ORDER_LITERAL = Literal["pre", "post"]


class ExecFilter:
    ALWAYS = "always"
    RAW_EVENT = "raw_event"
    MESSAGE = "message"

EXEC_FILTER_LITERAL = Literal["always", "raw_event", "message"]


class Stop(Exception): ...


class VkRawMiddleware(BaseMiddleware[RawEvent]):
    async def pre(self):
        try:
            return await r.vk_raw(self, Order.PRE, ExecFilter.RAW_EVENT)
        except Stop:
            self.stop()
        except Exception as e:
            logger.exception(e)
            raise
    
    async def post(self):
        try:
            return await r.vk_raw(self, Order.POST, ExecFilter.RAW_EVENT)
        except Stop:
            self.stop()
        except Exception as e:
            logger.exception(e)
            raise

class VkMessageMiddleware(BaseMiddleware[VkMessage]):
    async def pre(self):
        try:
            return await r.vk_message(self, Order.PRE, ExecFilter.MESSAGE)
        except Stop:
            self.stop()
        except Exception as e:
            logger.exception(e)
            raise
    
    async def post(self):
        try:
            return await r.vk_message(self, Order.POST, ExecFilter.MESSAGE)
        except Stop:
            self.stop()
        except Exception as e:
            logger.exception(e)
            raise

class TgUpdateMiddleware:
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any]
    ) -> Any:
        try:
            await r.tg_update(event, Order.PRE)
            await handler(event, data)
            await r.tg_update(event, Order.POST)
        except Stop:
            ...


@dataclass
class Middleware:
    exec_filter: EXEC_FILTER_LITERAL = ExecFilter.ALWAYS

    async def pre(self, everything: CommonEverything): ...
    async def post(self, everything: CommonEverything): ...
    def stop(self): raise Stop


@dataclass
class MessageMiddleware(Middleware):
    exec_filter: EXEC_FILTER_LITERAL = ExecFilter.MESSAGE


@dataclass
class EventMiddleware(Middleware):
    exec_filter: EXEC_FILTER_LITERAL = ExecFilter.RAW_EVENT


@dataclass
class Router:
    middlewares: list[Middleware] = field(default_factory=list)

    def add(self, mw: Middleware):
        self.middlewares.append(mw)
    
    def middleware(self):
        def decorator(mw: type[Middleware]) -> Middleware:
            self.add(mw())
            return mw
        
        return decorator

    def assign(self, tg_dp: Dispatcher):
        defs.vk_bot.labeler.message_view.register_middleware(VkMessageMiddleware)
        defs.vk_bot.labeler.raw_event_view.register_middleware(VkRawMiddleware)

        tg_dp.update.outer_middleware(TgUpdateMiddleware())

    async def vk_raw(
        self,
        mw: BaseMiddleware[RawEvent],
        order: ORDER_LITERAL,
        exec_filter: EXEC_FILTER_LITERAL
    ):
        event = CommonEvent.from_vk(mw.event)
        everything = CommonEverything.from_event(event)

        return await self.exec_from_order(everything, order, exec_filter)
    
    async def vk_message(
        self,
        mw: BaseMiddleware[VkMessage],
        order: ORDER_LITERAL,
        exec_filter: EXEC_FILTER_LITERAL
    ):
        message = CommonMessage.from_vk(mw.event)
        everything = CommonEverything.from_message(message)

        return await self.exec_from_order(everything, order, exec_filter)

    async def tg_update(
        self,
        event: Update,
        order: ORDER_LITERAL,
    ):
        if event.event_type == "message":
            return await self.tg_message(event.message, order)
        if event.event_type == "callback_query":
            return await self.tg_event(event.callback_query, order)
        else:
            logger.warning(f"uncaught tg event type while processing middlewares: {event}")
    
    async def tg_message(
        self,
        event: TgMessage,
        order: ORDER_LITERAL,
    ):
        message = CommonMessage.from_tg(event)
        everything = CommonEverything.from_message(message)

        return await self.exec_from_order(everything, order, ExecFilter.MESSAGE)
    
    async def tg_event(
        self,
        event: CallbackQuery,
        order: ORDER_LITERAL,
    ):
        message = CommonEvent.from_tg(event)
        everything = CommonEverything.from_event(message)

        return await self.exec_from_order(everything, order, ExecFilter.RAW_EVENT)

    async def exec_from_order(
        self,
        everything: CommonEverything,
        order: ORDER_LITERAL,
        exec_filter: EXEC_FILTER_LITERAL
    ):
        if order == Order.PRE:
            return await self.exec_pre(everything, exec_filter)
        if order == Order.POST:
            return await self.exec_post(everything, exec_filter)

    async def exec_pre(self, everything: CommonEverything, exec_filter: EXEC_FILTER_LITERAL):
        for mw in self.middlewares:
            if mw.exec_filter == ExecFilter.ALWAYS or mw.exec_filter == exec_filter:
                await mw.pre(everything)
    
    async def exec_post(self, everything: CommonEverything, exec_filter: EXEC_FILTER_LITERAL):
        for mw in self.middlewares:
            if mw.exec_filter == ExecFilter.ALWAYS or mw.exec_filter == exec_filter:
                await mw.post(everything)


r = Router()


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
        if not defs.ctx.is_added(everything):
            defs.ctx.add_from_everything(everything)

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
