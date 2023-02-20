import asyncio
import datetime
import re
import aiofiles
from redis.asyncio import Redis
from redis import exceptions as rexeptions
from aiofiles.threadpool.text import AsyncTextIOWrapper
from aiofiles import ospath
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


if TYPE_CHECKING:
    from src.svc.common import Ctx

ENV_PATH = ".env"
COLOR_ESCAPE_REGEX = re.compile(r"\x1b[[]\d{1,}m")


def sink(message: Message):
    is_error = False
    record = message.record

    if record["exception"] or record["level"].name == "ERROR":
        is_error = True

    async def write_out():
        try:
            await defs.log_file.write(no_escapes)
            await defs.log_file.flush()

            if (await ospath.getsize(defs.log_path)) > 1_048_576: # 1mb
                now = datetime.datetime.now()
                now_str = str(now)
                now_str = now_str.replace(":", "_").replace("/", "_")

                await defs.log_file.close()

                defs.log_path.rename(defs.log_dir.joinpath(f"log_{now_str}.txt"))

                defs.log_file = await aiofiles.open(
                    defs.log_path, mode="a", encoding="utf8", newline="\n"
                )
        except Exception:
            ...

    print(message, end="")

    no_escapes = COLOR_ESCAPE_REGEX.sub("", message)

    if is_error:
        from src.svc import vk
        
        async def send_error():
            admin_id = get_key(ENV_PATH, "VK_ADMIN")

            try:
                await vk.chunked_send(
                    peer_id = admin_id,
                    message = str(no_escapes),
                )
            except Exception:
                ...

        defs.create_task(send_error())

    defs.create_task(write_out())


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
    tg_bot_commands: Optional[list[str]] = None
    tg_router: Optional[Router] = None
    tg_dispatch: Optional[Dispatcher] = None

    http: Optional[ClientSession] = None
    ctx: Optional["Ctx"] = None
    redis: Optional[Redis] = None

    data_dir: Optional[Path] = None
    log_dir: Optional[Path] = None
    log_path: Optional[Path] = None
    log_file: Optional[AsyncTextIOWrapper] = None

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

        await SCHEDULE_API.ping()
        await SCHEDULE_API.update_period()
        await SCHEDULE_API.ft_daily_friendly_url()
        await SCHEDULE_API.ft_weekly_friendly_url()
        await SCHEDULE_API.r_weekly_friendly_url()

        SCHEDULE_API.ft_daily_url_button()
        SCHEDULE_API.ft_weekly_url_button()
        SCHEDULE_API.r_weekly_url_button()

        self.create_task(SCHEDULE_API.updates())

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
        self.tg_bot_commands = ["/nigga"]

    async def wait_for_redis(self):
        retry = 5
        logged = False

        host = self.redis.connection_pool.connection_kwargs["host"]
        port = self.redis.connection_pool.connection_kwargs["port"]

        while True:
            try:
                await self.redis.ping()
                logger.info(f"redis connected on {host}:{port}")
                break
            except rexeptions.ConnectionError:
                if not logged:
                    logger.opt(colors=True).error(f"run redis instance on {host}:{port} first, will keep trying reconnecting every {retry} secs")
                    logged = True
                
                await asyncio.sleep(retry)

    def init_redis(self):
        no_addr_error = ValueError("put redis connection details to the .env file like this: REDIS = \"127.0.0.1:6379\"")
        invalid_addr_error = ValueError("invalid addr for redis, make sure there is a \":\" in it like this: 127.0.0.1:6379")

        redis_uri = get_key(ENV_PATH, "REDIS")
        if redis_uri is None:
            raise no_addr_error
        
        host_port = redis_uri.split(":")
        if not host_port or len(host_port) < 2:
            raise invalid_addr_error

        host, port = host_port

        self.redis = Redis(host=host, port=port)
        self.loop.run_until_complete(self.wait_for_redis())

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
        self.tg_dispatch = telegram.load_dispatch(self.tg_router)

        self.loop.run_until_complete(self.init_http())

        self.loop.run_until_complete(self.get_vk_bot_info())
        self.loop.run_until_complete(self.get_tg_bot_info())

        if init_middlewares:
            from src.svc.common import middlewares
            middlewares.r.assign()
        
        if init_handlers:
            from src.svc.common.bps import settings, init, zoom, hub
        
        from src.svc.common import Ctx

        self.ctx = Ctx()
        self.init_redis()

        self.loop.run_until_complete(self.init_schedule_api())

    def init_fs(self) -> None:
        self.data_dir = Path(".", "data")
        self.data_dir.mkdir(exist_ok=True)

        self.log_dir = self.data_dir.joinpath("log")
        self.log_dir.mkdir(exist_ok=True)

        self.log_path = self.log_dir.joinpath("log.txt")

        self.log_file = self.loop.run_until_complete(
            aiofiles.open(self.log_path, mode="a", encoding="utf8", newline="\n")
        )

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
    
    def create_task(self, coro, *, name=None):
        task = self.loop.create_task(coro, name=name)

        task.add_done_callback(self._handle_task)

    def _handle_task(self, task: asyncio.Task):
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            try:
                fn = task.get_coro().cr_code.co_name
            except AttributeError:
                fn = "unknown"

            logger.exception(f"task function <{fn}> raised {type(e).__name__}: {e}")

defs = Defs()
