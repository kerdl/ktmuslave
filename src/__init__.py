import asyncio
import datetime
import re
import aiofiles
from redis.asyncio import Redis
from redis.commands.search.field import TextField, TagField
from redis import exceptions as rexeptions
from aiofiles.threadpool.text import AsyncTextIOWrapper
from aiofiles import ospath
from typing import Optional, TYPE_CHECKING
from vkbottle import Bot as VkBot
from vkbottle_types.responses.groups import GroupsGroupFull
from aiogram import Bot as TgBot, Dispatcher, Router
from aiogram.types import User
from aiohttp import ClientSession, client_exceptions as aiohttp_exc
from loguru import logger
from loguru._handler import Message
from dataclasses import dataclass
from pathlib import Path
from dotenv import get_key


if TYPE_CHECKING:
    from src.svc.common import Ctx, BaseCtx
    from src.svc.common.logsvc import Logger

ENV_PATH = ".env"
COLOR_ESCAPE_REGEX = re.compile(r"\x1b[[]\d{1,}m")


class RedisName:
    BROADCAST = "broadcast"
    TCHR_BROADCAST = "tchr_broadcast"
    IS_REGISTERED = "is_registered"
    MODE = "mode"
    GROUP = "group"
    TEACHER = "teacher"


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
class UpdateWaiter:
    waiter: "BaseCtx"

    def __enter__(self): 
        defs.add_update_waiter(self.waiter)

    def __exit__(self, type, value, traceback):
        defs.del_update_waiter(self.waiter.db_key)

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
    logger: Optional["Logger"] = None

    data_dir: Optional[Path] = None
    log_dir: Optional[Path] = None
    log_path: Optional[Path] = None
    log_file: Optional[AsyncTextIOWrapper] = None

    update_waiters: Optional[list["BaseCtx"]] = None

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

        await SCHEDULE_API.wait_for_schedule_server()
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

    async def create_redisearch_index(self):
        # i couldn't figure out how to generate
        # this exact command with redis-py built-in
        # instruments
        await self.redis.execute_command(
            "FT.CREATE",
            RedisName.BROADCAST,
            "ON",
            "JSON",
            "SCHEMA",
            "$.settings.mode", "AS", RedisName.MODE, "TEXT",
            "$.settings.group.confirmed", "AS", RedisName.GROUP, "TEXT",
            "$.settings.broadcast", "AS", RedisName.BROADCAST, "TAG",
            "$.is_registered", "AS", RedisName.IS_REGISTERED, "TAG",
        )
    
    async def create_redisearch_tchr_index(self):
        await self.redis.execute_command(
            "FT.CREATE",
            RedisName.TCHR_BROADCAST,
            "ON",
            "JSON",
            "SCHEMA",
            "$.settings.mode", "AS", RedisName.MODE, "TEXT",
            "$.settings.teacher.confirmed", "AS", RedisName.TEACHER, "TEXT",
            "$.settings.broadcast", "AS", RedisName.BROADCAST, "TAG",
            "$.is_registered", "AS", RedisName.IS_REGISTERED, "TAG",
        )

    async def check_redisearch_index(self):
        try:
            # try getting info about broadcast index
            await self.redis.ft(RedisName.BROADCAST).info()
        except rexeptions.ResponseError:
            # Unknown Index name
            # it doesn't exist, create this index
            await self.create_redisearch_index()
            logger.info(f"created redis \"{RedisName.BROADCAST}\" index")

        try:
            # try getting info about broadcast index
            await self.redis.ft(RedisName.TCHR_BROADCAST).info()
        except rexeptions.ResponseError:
            # Unknown Index name
            # it doesn't exist, create this index
            await self.create_redisearch_tchr_index()
            logger.info(f"created redis \"{RedisName.TCHR_BROADCAST}\" index")

    def init_redis(self):
        no_addr_error = ValueError("put redis connection details to the .env file like this: REDIS_ADDR = \"127.0.0.1:6379\"")
        invalid_addr_error = ValueError("invalid addr for redis, make sure there is a \":\" in it like this: 127.0.0.1:6379")

        redis_uri = get_key(ENV_PATH, "REDIS_ADDR")
        if redis_uri is None:
            raise no_addr_error
        
        host_port = redis_uri.split(":")
        if not host_port or len(host_port) < 2:
            raise invalid_addr_error

        host, port = host_port
        password = get_key(ENV_PATH, "REDIS_PASSWORD") or None

        self.redis = Redis(host=host, port=port, password=password)
        self.loop.run_until_complete(self.wait_for_redis())
        self.loop.run_until_complete(self.check_redisearch_index())
        
        from src.svc.common import DbBaseCtx
        from src.data.zoom import Container
        from src.data.settings import MODE_LITERAL
        DbBaseCtx.ensure_update_forward_refs()
        Container.update_forward_refs(**locals())

    async def init_logger_svc(self) -> None:
        from src.svc.common.logsvc import Logger

        logger_addr = get_key(ENV_PATH, "LOGGER_ADDR") or "127.0.0.1:7215"
        if not logger_addr.startswith("https://"):
            logger_addr = "https://" + logger_addr

        try:
            await self.http.get(logger_addr)
        except aiohttp_exc.ClientConnectorError:
            logger.warning(
                f"logging service at {logger_addr} is not running, logging may be inconsistent"
            )

        self.logger = Logger(addr=logger_addr)

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
            from src.svc.common.bps import admin, reset, settings, init, zoom, hub
        
        from src.svc.common import Ctx

        self.ctx = Ctx()
        self.init_redis()

        self.loop.run_until_complete(self.init_logger_svc())
        self.loop.run_until_complete(self.init_schedule_api())

        self.update_waiters = []

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

    def add_update_waiter(self, waiter: "BaseCtx"):
        self.update_waiters.append(waiter)
        logger.info(f"update waiter {waiter.db_key} has been added")
    
    def del_update_waiter(self, db_key: str):
        for index, waiter in enumerate(self.update_waiters):
            waiter: "BaseCtx"

            if waiter.db_key == db_key:
                self.update_waiters.pop(index)
                logger.info(f"update waiter {db_key} has been deleted")
                logger.info(f"{self.update_waiters_db_keys=}")
                break
    
    def clean_update_waiters(self):
        self.update_waiters = []
    
    @property
    def update_waiters_db_keys(self) -> list[str]:
        waiters_db_keys: list[str] = []

        for waiter in self.update_waiters:
            waiters_db_keys.append(waiter.db_key)
        
        return waiters_db_keys

defs = Defs()
