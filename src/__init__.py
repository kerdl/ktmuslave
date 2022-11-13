import sys
import os
import asyncio
import datetime
import re
from typing import Optional, TYPE_CHECKING
from vkbottle import Bot as VkBot
from vkbottle_types.responses.groups import GroupsGroupFull
from aiogram import Bot as TgBot, Dispatcher, Router
from aiogram.types import User
from aiohttp import ClientSession
from loguru import logger
from loguru._handler import Message
from dataclasses import dataclass
from pathlib import Path
from dotenv import get_key
from io import TextIOWrapper


if TYPE_CHECKING:
    from src.svc.common import Ctx

COLOR_ESCAPE_REGEX = re.compile(r"\x1b[[]\d{1,}m")


def sink(message: Message):
    record = message.record

    if record["exception"]:
        from src.svc import vk

        exc = record["exception"]
        
        async def send_error():
            admin_id = get_key(".env", "VK_ADMIN")

            await vk.chunked_send(
                peer_id = admin_id,
                message = str(exc),
            )

        defs.loop.create_task(send_error())

    print(message, end="")

    no_escapes = COLOR_ESCAPE_REGEX.sub("", message)

    defs.log_file.write(no_escapes)
    defs.log_file.flush()


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

    http: Optional[ClientSession] = None
    ctx: Optional["Ctx"] = None

    data_dir: Optional[Path] = None
    log_dir: Optional[Path] = None
    log_path: Optional[Path] = None
    log_file: Optional[TextIOWrapper] = None

    def init_all(
        self, 
        init_handlers: bool = True,
        init_middlewares: bool = True,
    ) -> None:
        self.init_loop()
        self.init_logger()
        self.init_fs()
        self.init_vars(init_handlers, init_middlewares)

    def init_loop(self):
        self.loop = asyncio.get_event_loop()

    async def init_http(self):
        self.http = ClientSession(loop = self.loop)
    
    async def init_schedule_api(self):
        from src.api.schedule import SCHEDULE_API

        await SCHEDULE_API.last_update(force=True)
        await SCHEDULE_API.update_period()
        await SCHEDULE_API.ft_daily_friendly_url()
        await SCHEDULE_API.ft_weekly_friendly_url()
        await SCHEDULE_API.r_weekly_friendly_url()

        SCHEDULE_API.ft_daily_url_button()
        SCHEDULE_API.ft_weekly_url_button()
        SCHEDULE_API.r_weekly_url_button()

        await SCHEDULE_API.daily()
        await SCHEDULE_API.weekly()

        self.loop.create_task(SCHEDULE_API.updates())

    async def get_vk_bot_info(self):
        groups_data = await self.vk_bot.api.groups.get_by_id()
        group_data = groups_data[0]

        self.vk_bot_info = group_data
        self.vk_bot_mention = "@" + group_data.screen_name

    async def get_tg_bot_info(self):
        me = await self.tg_bot.get_me()
        
        self.tg_bot_info = me
        #self.tg_bot_mention = "@" + me.username
        self.tg_bot_mention = "/nigga"

    def init_vars(
        self, 
        init_handlers: bool = True,
        init_middlewares: bool = True,
    ) -> None:
        """
        ## Init variables/constants, by default they are all `None`
        """
        from src.svc import vk, telegram

        self.vk_bot = vk.load(self.loop)
        self.tg_bot = telegram.load_bot(self.loop)
        self.tg_router = telegram.load_router()
        self.tg_dispatch = telegram.load_dispatch(self.tg_router, init_middlewares)

        self.loop.run_until_complete(self.init_http())

        self.loop.run_until_complete(self.get_vk_bot_info())
        self.loop.run_until_complete(self.get_tg_bot_info())

        if init_middlewares:
            from src.svc.telegram import middlewares
        
        if init_handlers:
            from src.svc.common.bps import settings, init, zoom, hub
            from src.svc.common.router import r
            r.assign()
        
        from src.svc.common import Ctx

        self.ctx = Ctx.load_or_init()
        self.loop.create_task(self.ctx.save_forever())

        self.loop.run_until_complete(self.init_schedule_api())

    def init_fs(self) -> None:
        self.data_dir = Path(".", "data")
        self.data_dir.mkdir(exist_ok=True)

        self.log_dir = self.data_dir.joinpath("log")
        self.log_dir.mkdir(exist_ok=True)

        self.log_path = self.log_dir.joinpath("log.txt")

        if self.log_path.exists() and os.path.getsize(self.log_path) > 1_048_576: # 1mb
            now = datetime.datetime.now()
            now_str = str(now)

            now_str = now_str.replace(":", "_").replace("/", "_")

            self.log_path.rename(f"log_{now_str}.txt")

        self.log_file = open(self.log_path, mode="a", encoding="utf8", newline="\n")

    def init_logger(self) -> None:
        """
        ## Init `loguru` with custom sink and format
        """

        logger.remove()

        fmt = ("<g>{time:YYYY-MM-DD HH:mm:ss}</> "
        "| <level>{level: ^8}</> "
        "| <level>{message}</> "
        "(<c>{name}:{function}</>)")

        logger.add(
            sink,
            format=fmt, 
            backtrace=True, 
            diagnose=True, 
            enqueue=True,
            colorize=True,
            catch=True,
            level="INFO"
        )

        self.log_dir

defs = Defs()
