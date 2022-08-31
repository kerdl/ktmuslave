import sys
import asyncio
from vkbottle import Bot as VkBot
from aiogram import Bot as TgBot, Dispatcher
from loguru import logger
from dataclasses import dataclass

@dataclass
class Defs:
    """
    ## `Def`inition`s` of variables, constants, objects, etc.
    """
    loop: asyncio.AbstractEventLoop = None
    vk_bot: VkBot = None
    tg_bot: TgBot = None
    tg_dispatch: Dispatcher = None

    def init_all(self) -> None:
        self.init_logger()
        self.init_vars()

    def init_vars(self) -> None:
        """
        ## Init variables/constants, by default they are all `None`
        """
        from src.svc import vk, telegram

        self.loop = asyncio.get_event_loop()
        self.vk_bot = vk.load(loop=self.loop)
        self.tg_bot = telegram.load_bot(loop=self.loop)
        self.tg_dispatch = telegram.load_dispatch(bot=self.tg_bot, loop=self.loop)

        from src.svc.telegram.bps import settings

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
