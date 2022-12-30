from loguru import logger
from dataclasses import dataclass, field
from vkbottle import BaseMiddleware
from vkbottle.bot import Message as VkMessage
from aiogram.types import Update, Message as TgMessage, CallbackQuery, Chat
from typing import Callable, Any, Awaitable, Optional
from typing import Literal

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
            return await r.vk_raw(self, Order.PRE, ExecFilter.MESSAGE)
        except Stop:
            self.stop()
        except Exception as e:
            logger.exception(e)
            raise
    
    async def post(self):
        try:
            return await r.vk_raw(self, Order.POST, ExecFilter.MESSAGE)
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
            await r
            return await handler(event, data)
        except Stop:
            ...

class TgMessageMiddleware:
    async def __call__(
        self,
        handler: Callable[[TgMessage, dict[str, Any]], Awaitable[Any]],
        event: TgMessage,
        data: dict[str, Any]
    ) -> Any:
        try:
            await r
            return await handler(event, data)
        except Stop:
            ...

class TgEventMiddleware:
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any]
    ) -> Any:
        try:
            await r
            return await handler(event, data)
        except Stop:
            ...


@dataclass
class Middleware:
    exec_filter: EXEC_FILTER_LITERAL = ExecFilter.ALWAYS

    async def pre(self, everything: CommonEverything): ...
    async def post(self, everything: CommonEverything): ...


@dataclass
class MessageMiddleware(Middleware):
    exec_filter: EXEC_FILTER_LITERAL = ExecFilter.MESSAGE


@dataclass
class EventMiddleware(Middleware):
    exec_filter: EXEC_FILTER_LITERAL = ExecFilter.RAW_EVENT


@dataclass
class Router:
    middlewares: list[Middleware] = field(default_factory=list)


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
            return await self.tg_message(event, order)
        if event.event_type == "callback_query":
            return await self.tg_event(event, order)
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
        everything = CommonEverything.from_message(message)

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
