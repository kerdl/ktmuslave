"""
## Cross-platform handlers
"""

from loguru import logger
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Union, Literal
from vkbottle import BaseMiddleware
from vkbottle.bot import Message as VkMessage
from aiogram.types import Update
import inspect

from src import defs
from src.svc.vk.types_ import RawEvent
from src.svc.common import CommonEverything, CommonMessage
from src.svc.common import CommonEvent
from src.svc.common.filters import BaseFilter, MessageOnlyFilter, EventOnlyFilter


FUNC_TYPE = Callable[[Union[CommonMessage, CommonEvent, CommonEverything]], Awaitable[Any]]

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
class StopPre(Exception): ...


class VkRawCatcher(BaseMiddleware[RawEvent]):
    async def pre(self) -> None:
        try:
            event = CommonEvent.from_vk(self.event)
            everything = CommonEverything.from_event(event)
            await r.choose_handler(everything)
        except Exception as e:
            logger.exception(f"{type(e).__name__}({e})")

class VkMessageCatcher(BaseMiddleware[VkMessage]):
    async def pre(self) -> None:
        try:
            # we're not using this
            # and it fails to serialize 🖕🖕🖕
            self.event.unprepared_ctx_api = None

            message = CommonMessage.from_vk(self.event)
            everything = CommonEverything.from_message(message)        
            await r.choose_handler(everything)
        except Exception as e:
            logger.exception(f"{type(e).__name__}({e})")

class TgUpdateCatcher:
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any]
    ) -> Any:
        if event.event_type == "message":
            message = CommonMessage.from_tg(event.message)
            everything = CommonEverything.from_message(message)
        elif event.event_type == "callback_query":
            event = CommonEvent.from_tg(event.callback_query)
            everything = CommonEverything.from_event(event)
        else:
            logger.warning(f"unsupported tg event type: {event.event_type}")
        
        await r.choose_handler(everything)


@dataclass
class Middleware:
    exec_filter: EXEC_FILTER_LITERAL = ExecFilter.ALWAYS

    async def pre(self, everything: CommonEverything): ...
    async def post(self, everything: CommonEverything): ...
    def stop(self): raise Stop
    def stop_pre(self): raise StopPre


@dataclass
class MessageMiddleware(Middleware):
    exec_filter: EXEC_FILTER_LITERAL = ExecFilter.MESSAGE


@dataclass
class EventMiddleware(Middleware):
    exec_filter: EXEC_FILTER_LITERAL = ExecFilter.RAW_EVENT


@dataclass
class Handler:
    func: FUNC_TYPE
    filters: tuple[BaseFilter]
    is_blocking: bool

@dataclass
class Router:
    handlers: list[Handler] = field(default_factory=list)
    middlewares: list[Middleware] = field(default_factory=list)

    def on_message(
        self, 
        *filters: BaseFilter, 
        is_blocking: bool = True,
    ):
        def decorator(func: FUNC_TYPE):
            handler = Handler(func, (MessageOnlyFilter(),) + filters, is_blocking)
            self.handlers.append(handler)

            return func

        return decorator
    
    def on_callback(
        self, 
        *filters: BaseFilter, 
        is_blocking: bool = True,
    ):
        def decorator(func: FUNC_TYPE):
            handler = Handler(func, (EventOnlyFilter(),) + filters, is_blocking)
            self.handlers.append(handler)

            return func

        return decorator
    
    def on_everything(
        self, 
        *filters: BaseFilter, 
        is_blocking: bool = True
    ):
        def decorator(func: FUNC_TYPE):
            handler = Handler(func, filters, is_blocking)
            self.handlers.append(handler)

            return func

        return decorator

    def add_middleware(self, mw: Middleware):
        self.middlewares.append(mw)
    
    def middleware(self):
        def decorator(mw: type[Middleware]) -> Middleware:
            self.add_middleware(mw())
            return mw
        
        return decorator

    def assign(self):
        """
        ## Assign middleware dummies to VK and Telegram
        """

        """ Assign to VK """
        defs.vk_bot.labeler.message_view.register_middleware(VkMessageCatcher)
        defs.vk_bot.labeler.raw_event_view.register_middleware(VkRawCatcher)

        """ Assign to Telegram """
        defs.tg_dispatch.update.outer_middleware(TgUpdateCatcher())

    async def call_pre_middlewares(self, everything: CommonEverything):
        if everything.is_from_event:
            event_type = ExecFilter.RAW_EVENT
        elif everything.is_from_message:
            event_type = ExecFilter.MESSAGE

        for mw in self.middlewares:
            if mw.exec_filter == ExecFilter.ALWAYS or mw.exec_filter == event_type:
                await mw.pre(everything)
    
    async def call_post_middlewares(self, everything: CommonEverything):
        if everything.is_from_event:
            event_type = ExecFilter.RAW_EVENT
        elif everything.is_from_message:
            event_type = ExecFilter.MESSAGE

        for mw in self.middlewares:
            if mw.exec_filter == ExecFilter.ALWAYS or mw.exec_filter == event_type:
                await mw.post(everything)

    async def choose_handler(self, everything: CommonEverything):
        do_handler_choose = True
        handler_was_called = False

        try:
            await self.call_pre_middlewares(everything)
        except Stop:
            return
        except StopPre:
            do_handler_choose = False
        except Exception as e:
            logger.exception(e)
            raise e

        if do_handler_choose:
            for handler in self.handlers:

                # if filter condition interrupted this
                # handler from execution
                filter_interrupt = True
                filter_check_interrupt = False

                # if no filters, this handler
                # should always be executed
                if len(handler.filters) < 1:
                    filter_interrupt = False

                else:
                    # but if we do have filters,
                    # check them
                    filter_results: list[bool] = []

                    for filter_ in handler.filters:
                        try:
                            call_fn = filter_.__call__
                        except AttributeError:
                            call_fn = filter_

                        # call the filter
                        if inspect.iscoroutinefunction(call_fn):
                            result = await call_fn(everything)
                        else:
                            result = call_fn(everything)

                        if result is False:
                            filter_check_interrupt = True
                            break

                        filter_results.append(result)
                    
                    if filter_check_interrupt:
                        continue

                    # if all filters were passed
                    if all(filter_results):
                        filter_interrupt = False
                
                if filter_interrupt:
                    # continue to look for other
                    # handlers
                    continue
                else:
                    kwargs = {}

                    # look for function arguments and their type hints
                    for (argument, annotation) in handler.func.__annotations__.items():
                        if annotation == CommonEverything:
                            kwargs[argument] = everything
                        elif annotation == CommonMessage:
                            kwargs[argument] = everything.message
                        elif annotation == CommonEvent:
                            kwargs[argument] = everything.event

                    await handler.func(**kwargs)
                    handler_was_called = True
                    
                    if handler.is_blocking:
                        break

        everything.set_was_processed(handler_was_called)

        await self.call_post_middlewares(everything)

r = Router()
