import sys
import asyncio
from typing import Optional
from vkbottle import Bot as VkBot
from vkbottle_types.responses.groups import GroupsGroupFull
from aiogram import Bot as TgBot, Dispatcher, Router
from aiogram.types import User
from loguru import logger
from dataclasses import dataclass


@dataclass
class Defs:
    """
    ## `Def`inition`s` of variables, constants, objects, etc.
    """
    loop: Optional[asyncio.AbstractEventLoop] = None
    vk_bot: Optional[VkBot] = None
    vk_bot_info: Optional[GroupsGroupFull] = None
    vk_bot_mention: Optional[str] = None
    tg_bot: Optional[TgBot] = None
    tg_bot_info: Optional[User] = None
    tg_bot_mention: Optional[str] = None
    tg_router: Optional[Router] = None
    tg_dispatch: Optional[Dispatcher] = None

    def init_all(
        self, 
        init_handlers: bool = True,
        init_middlewares: bool = True,
    ) -> None:
        self.init_logger()
        self.init_vars(init_handlers, init_middlewares)

    def init_vars(
        self, 
        init_handlers: bool = True,
        init_middlewares: bool = True,
    ) -> None:
        """
        ## Init variables/constants, by default they are all `None`
        """
        from src.svc import vk, telegram

        self.loop = asyncio.get_event_loop()
        self.vk_bot = vk.load(self.loop)
        self.tg_bot = telegram.load_bot(self.loop)
        self.tg_router = telegram.load_router()
        self.tg_dispatch = telegram.load_dispatch(self.tg_router, init_middlewares)

        async def get_vk_bot_info():
            groups_data = await self.vk_bot.api.groups.get_by_id()
            group_data = groups_data[0]

            self.vk_bot_info = group_data
            self.vk_bot_mention = "@" + group_data.screen_name

        async def get_tg_bot_info():
            me = await self.tg_bot.get_me()
            
            self.tg_bot_info = me
            self.tg_bot_mention = "@" + me.username

        self.loop.create_task(get_vk_bot_info())
        self.loop.create_task(get_tg_bot_info())

        if init_middlewares:
            from src.svc.telegram import middlewares
        
        if init_handlers:
            from src.svc.common.bps import init, hub
            from src.svc.common.router import r
            r.assign()

    @staticmethod
    def init_logger() -> None:
        """
        ## Init `loguru` with custom sink and format
        """

        logger.remove()

        fmt = ("<g>{time:YYYY-MM-DD HH:mm:ss}</> "
        "| <level>{level: ^8}</> "
        "| <level>{message}</> "
        "(<c>{name}:{function}</>)")
        
        logger.add(
            sys.stdout,
            format=fmt, 
            backtrace=True, 
            diagnose=True, 
            enqueue=True,
            colorize=True,
            catch=True,
            level="DEBUG"
        )

defs = Defs()
