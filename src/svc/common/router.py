"""
## Cross-platform decorators for handlers
"""

if __name__ == "__main__":
    import sys
    sys.path.append('.')

    from src.svc import common

from loguru import logger
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Union
from vkbottle import GroupEventType
from vkbottle.bot import MessageEvent

from src import defs
from src.svc.common import CommonEverything, CommonMessage
from src.svc.common import CommonEvent
from src.svc.common.filters import BaseFilter, MessageOnlyFilter, EventOnlyFilter


FUNC_TYPE = Callable[[Union[CommonMessage, CommonEvent, CommonEverything]], Awaitable[Any]]


@dataclass
class Handler:
    func: FUNC_TYPE
    filters: tuple[BaseFilter]
    is_blocking: bool

@dataclass
class Router:
    handlers: list[Handler]

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

    def assign(self):
        """
        ## Assign dummies to VK and Telegram decorators
        """

        """ Assign to VK """
        # on message
        vk_msg_decorator = defs.vk_bot.on.message()
        vk_msg_decorator(self.choose_handler)

        # on callback button press
        vk_callback_decorator = defs.vk_bot.on.raw_event(
            GroupEventType.MESSAGE_EVENT, 
            MessageEvent
        )
        vk_callback_decorator(self.choose_handler)


        """ Assign to Telegram """
        # on message handler
        tg_msg_decorator = defs.tg_router.message()
        tg_msg_decorator(self.choose_handler)

        # on callback button press
        tg_callback_decorator = defs.tg_router.callback_query()
        tg_callback_decorator(self.choose_handler)

    async def choose_handler(self, *args, everything: CommonEverything):
        everything.ctx.set_everything(everything)

        for handler in self.handlers:

            # if filter condition interrupted this
            # handler from execution
            filter_interrupt = True

            # if no filters, this handler
            # should always be executed
            if len(handler.filters) < 1:
                filter_interrupt = False

            else:
                # but if we do have filters,
                # check them
                filter_results: list[bool] = []

                for filter_ in handler.filters:
                    # call the filter
                    result = await filter_(everything)
                    filter_results.append(result)
                
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

                logger.info(f"calling {handler.func}")
                await handler.func(**kwargs)
                
                if handler.is_blocking:
                    break

r = Router([])


if __name__ == "__main__":

    @dataclass
    class UrMomFilter(BaseFilter):
        async def __call__(self, everything: CommonEverything):
            return everything.is_from_tg

    defs.init_all(init_handlers=False, init_middlewares=True)

    @r.on_everything()
    async def pizda(everything: CommonEverything):
        if everything.is_from_message:
            message = everything.message
            await message.answer("mne pohui")
        elif everything.is_from_event:
            event = everything.event
            await event.edit_message("mne VDVOINE POEBAT")

    @r.on_message()
    async def shit(message: CommonMessage):
        await message.answer("rabotaet ebat")
    
    @r.on_callback()
    async def cock(event: CommonEvent):
        await event.edit_message("niger")

    r.assign()

    common.run_forever()
