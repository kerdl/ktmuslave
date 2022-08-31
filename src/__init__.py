import sys
from vkbottle.bot import Bot as VkBot
from aiogram.bot import Bot as TgBot
from loguru import logger
from dataclasses import dataclass

@dataclass
class Defs:
    """
    ## `Def`inition`s` of variables, constants, objects, etc.
    """
    vk_bot: VkBot = None
    tg_bot: TgBot = None

    def init_all(self) -> None:
        self.init_logger()
        self.init_vars()

    def init_vars(self) -> None:
        """
        ## Init variables/constants, by default they are all `None`
        """
        from src.svc import vk, telegram

        self.vk_bot = vk.load()
        self.tg_bot = telegram.load()

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
