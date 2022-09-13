"""
## Cross-platform decorators for handlers
"""

if __name__ == "__main__":
    import sys
    sys.path.append('.')

    from src.svc import common

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Union
from vkbottle import GroupEventType
from vkbottle.bot import MessageEvent

from src import defs
from src.svc.common import CommonEverything, CommonMessage
from src.svc.common import CommonEvent
from src.svc.common.filter import BaseFilter


@dataclass
class Handler:
    func: Callable[[Union[CommonMessage, CommonEvent]], Awaitable[Any]]
    filters: tuple[BaseFilter]

@dataclass
class Router:
    message_handlers: list[Handler]
    callback_handlers: list[Handler]

    def on_message(self, *filters: BaseFilter):
        def decorator(func: Callable[[CommonMessage], Awaitable[Any]]):
            self.message_handlers.append(Handler(func, filters))

            return func

        return decorator
    
    def on_callback(self, *filters: BaseFilter):
        def decorator(func: Callable[[CommonEvent], Awaitable[Any]]):
            self.callback_handlers.append(Handler(func, filters))

            return func

        return decorator

    def assign(self):
        """
        ## Assign dummies to VK and Telegram decorators
        """

        # on message handler
        vk_msg_decorator = defs.vk_bot.on.message()
        vk_msg_decorator(self.vk_message)

        # on callback button press
        vk_callback_decorator = defs.vk_bot.on.raw_event(
            GroupEventType.MESSAGE_EVENT, 
            MessageEvent
        )
        vk_callback_decorator(self.vk_callback)

        """"""""""""""""""""""""""""""""""""""""""""

        # on message handler
        tg_msg_decorator = defs.tg_router.message()
        tg_msg_decorator(self.tg_message)

        # on callback button press
        tg_callback_decorator = defs.tg_router.callback_query()
        tg_callback_decorator(self.tg_callback)

    @staticmethod
    async def filter_handlers(handler_list: list[Handler], everything: CommonEverything):
        for handler in handler_list:

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
                for filter_ in handler.filters:
                    # call the filter
                    result = await filter_(everything)

                    # if this filter returned True
                    if result is True:
                        filter_interrupt = False
                        break
            
            if filter_interrupt:
                # continue to look for other
                # handlers
                continue
            else:
                if everything.is_from_message:
                    # call this handler with CommonMessage
                    await handler.func(everything.message)
                elif everything.is_from_event:
                    # call this handler with CommonEvent
                    await handler.func(everything.event)
                
                break

    async def find_callback_handler(self, event: CommonEvent):
        await self.filter_handlers(
            self.callback_handlers, 
            CommonEverything.from_event(event)
        )

    async def find_message_handler(self, message: CommonMessage):
        await self.filter_handlers(
            self.message_handlers,
            CommonEverything.from_message(message)
        )
    
    async def vk_message(self, *args, common_message: CommonMessage):
        await self.find_message_handler(common_message)
    
    async def vk_callback(self, *args, common_event: CommonEvent):
        await self.find_callback_handler(common_event)

    async def tg_message(self, *args, common_message: CommonMessage):
        await self.find_message_handler(common_message)

    async def tg_callback(self, *args, common_event: CommonEvent):
        await self.find_callback_handler(common_event)

r = Router([], [])


if __name__ == "__main__":

    from aiogram.types import ReplyKeyboardRemove

    @dataclass
    class UrMomFilter(BaseFilter):
        async def __call__(self, everything: CommonEverything):
            return everything.is_from_tg

    defs.init_all(init_handlers=False, init_middlewares=True)

    @r.on_message()
    async def shit(message: CommonMessage):
        await message.answer("rabotaet ebat")
    
    @r.on_callback()
    async def cock(event: CommonEvent):
        await event.edit_message("niger")

    r.assign()

    common.run_forever()