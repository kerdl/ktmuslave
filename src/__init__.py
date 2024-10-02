import asyncio
import datetime
import re
import aiofiles
import warnings
import asyncio
from redis.asyncio import Redis
from redis import exceptions as rexeptions
from aiofiles.threadpool.text import AsyncTextIOWrapper
from aiofiles import ospath
from typing import Optional, Never, TYPE_CHECKING
from vkbottle import Bot as VkBot
from vkbottle_types.responses.groups import GroupsGroupFull
from aiogram import Bot as TgBot, Dispatcher, Router
from aiogram.types import User
from aiohttp import ClientSession, client_exceptions as aiohttp_exc
from loguru import logger
from loguru._handler import Message
from dataclasses import dataclass
from pathlib import Path
from src.settings import Settings
from src.weekcast import WeekCast
from src.api.schedule import ScheduleApi, LastNotify
from src.data import week
from src.data.range import Range
from src.data.weekday import WEEKDAY_LITERAL


if TYPE_CHECKING:
    from src.svc.common import Ctx
    from src.svc.common.logsvc import Logger


COLOR_ESCAPE_REGEX = re.compile(r"\x1b[[]\d{1,}m")


class RedisName:
    BROADCAST = "broadcast"
    TCHR_BROADCAST = "tchr_broadcast"
    GENERIC_BROADCAST = "generic_broadcast"
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
        if not defs.log_path:
            return

        try:
            await defs.log_file.write(no_escapes)
            await defs.log_file.flush()

            if (await ospath.getsize(defs.log_path)) > 1_048_576: # 1mb
                now = datetime.datetime.now()
                now_str = str(now)
                now_str = now_str.replace(":", "_").replace("/", "_")

                await defs.log_file.close()

                defs.log_path.rename(
                    defs.settings.logging.dir.joinpath(f"log_{now_str}.txt")
                )
                defs.log_file = await aiofiles.open(
                    defs.log_path, mode="a", encoding="utf8", newline="\n"
                )
        except Exception:
            ...

    print(message, end="")

    no_escapes = COLOR_ESCAPE_REGEX.sub("", message)

    if is_error:
        from src.svc import vk, telegram
        from src.svc.common import Source
        
        async def send_error():
            for admin in defs.settings.logging.admins:
                try:
                    if admin.src == Source.VK:
                        await vk.chunked_send(
                            peer_id=admin.id,
                            message=str(no_escapes),
                        )
                    elif admin.src == Source.TG:
                        await telegram.chunked_send(
                            chat_id=admin.id,
                            text=str(no_escapes),
                        )
                except Exception as e:
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
    vk_bot_mention_regex: Optional[re.Pattern] = None

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

    settings: Optional[Settings] = None
    weekcast: Optional[WeekCast] = None
    schedule: Optional[ScheduleApi] = None

    data_dir: Optional[Path] = None
    log_path: Optional[Path] = None
    log_file: Optional[AsyncTextIOWrapper] = None

    time_mapping: Optional[dict["WEEKDAY_LITERAL", Range[datetime.time]]] = None

    def init_all(
        self, 
        init_handlers: bool = True,
        init_middlewares: bool = True,
    ) -> None:
        self.init_loop()
        self.init_logger()
        self.init_fs()
        self.init_vars(init_handlers, init_middlewares)
        self.init_periods()

    def init_loop(self) -> None:
        self.loop = asyncio.get_event_loop()

    async def init_http(self) -> None:
        self.http = ClientSession(loop=self.loop)
    
    async def init_schedule_api(self) -> None:
        #await self.schedule.await_server()
        self.create_task(self.schedule.updates())

    async def get_vk_bot_info(self) -> None:
        groups_resp = await self.vk_bot.api.groups.get_by_id()
        group_data = groups_resp.groups[0]
        self.vk_bot_info = group_data
        self.vk_bot_mention = "@" + group_data.screen_name
        regex = f"[[].+[|]{self.vk_bot_mention}[]]"
        self.vk_bot_mention_regex = re.compile(regex)

    async def get_tg_bot_info(self) -> None:
        me = await self.tg_bot.get_me()
        self.tg_bot_info = me
        self.tg_bot_mention = "/nigga"
        self.tg_bot_commands = ["/nigga"]

    async def wait_for_redis(self) -> None:
        retry = 5
        logged = False

        host = self.redis.connection_pool.connection_kwargs["host"]
        port = self.redis.connection_pool.connection_kwargs["port"]

        while True:
            if not await self.is_redis_online():
                if not logged:
                    logger.opt(colors=True).error(
                        f"unable to rech redis instance "
                        f"at {host}:{port}, awaiting..."
                    )
                    logged = True
                
                await asyncio.sleep(retry)
            else:
                logger.info(f"redis connected on {host}:{port}")
                break

    async def is_redis_online(self) -> bool:
        try:
            await self.redis.ping()
            return True
        except rexeptions.ConnectionError:
            return False

    async def create_redisearch_group_broadcast_index(self) -> None:
        await self.redis.execute_command(
            "FT.CREATE",
            RedisName.BROADCAST,
            "ON",
            "JSON",
            "SCHEMA",
            "$.is_registered", "AS", RedisName.IS_REGISTERED, "TAG",
            "$.settings.broadcast", "AS", RedisName.BROADCAST, "TAG",
            "$.settings.mode", "AS", RedisName.MODE, "TEXT",
            "$.settings.group.confirmed", "AS", RedisName.GROUP, "TEXT"
        )
    
    async def create_redisearch_tchr_broadcast_index(self) -> None:
        await self.redis.execute_command(
            "FT.CREATE",
            RedisName.TCHR_BROADCAST,
            "ON",
            "JSON",
            "SCHEMA",
            "$.is_registered", "AS", RedisName.IS_REGISTERED, "TAG",
            "$.settings.broadcast", "AS", RedisName.BROADCAST, "TAG",
            "$.settings.mode", "AS", RedisName.MODE, "TEXT",
            "$.settings.teacher.confirmed", "AS", RedisName.TEACHER, "TEXT"
        )

    async def create_redisearch_generic_broadcast_index(self) -> None:
        await self.redis.execute_command(
            "FT.CREATE",
            RedisName.GENERIC_BROADCAST,
            "ON",
            "JSON",
            "SCHEMA",
            "$.is_registered", "AS", RedisName.IS_REGISTERED, "TAG",
            "$.settings.broadcast", "AS", RedisName.BROADCAST, "TAG"
        )

    async def check_redisearch_index(self) -> None:
        try:
            await self.redis.ft(RedisName.BROADCAST).info()
        except rexeptions.ResponseError:
            await self.create_redisearch_group_broadcast_index()
            logger.info(f"created redis \"{RedisName.BROADCAST}\" index")

        try:
            await self.redis.ft(RedisName.TCHR_BROADCAST).info()
        except rexeptions.ResponseError:
            await self.create_redisearch_tchr_broadcast_index()
            logger.info(f"created redis \"{RedisName.TCHR_BROADCAST}\" index")
            
        try:
            await self.redis.ft(RedisName.GENERIC_BROADCAST).info()
        except rexeptions.ResponseError:
            await self.create_redisearch_generic_broadcast_index()
            logger.info(f"created redis \"{RedisName.GENERIC_BROADCAST}\" index")

    def init_redis(self) -> None:
        invalid_addr_error = ValueError(
            "invalid database address, "
            "make sure it follows this format: 127.0.0.1:6379"
        )
        
        host_port = self.settings.database.addr.split(":")
        if not host_port or len(host_port) < 2:
            raise invalid_addr_error

        host, port = host_port
        password = self.settings.database.password

        self.redis = Redis(host=host, port=port, password=password)
        self.loop.run_until_complete(self.wait_for_redis())
        self.loop.run_until_complete(self.check_redisearch_index())
        
        from src.svc.common import DbBaseCtx
        from src.data.zoom import Container
        from src.data.settings import MODE_LITERAL
        DbBaseCtx.model_rebuild()
        Container.model_rebuild()
        
    async def weekcast_loop(self) -> Never:
        from src.svc.common import messages
        
        await self.schedule.ready_channel.get()
        
        while True:
            today = datetime.date.today()
            covered = self.weekcast.covered
            next_broadcast = covered.end
            
            if today not in covered:
                next_broadcast = week.ensure_next_after_current(covered).end
                self.weekcast.covered = week.cover_today(covered.start.weekday())
                self.weekcast.poll_save()
                
                logger.info("weekcast starts broadcasting")
                
                await self.ctx.broadcast_schedule_to_subscribes(
                    header=messages.format_next_week()
                )
            
            now = datetime.datetime.now()
            next_broadcast_time = datetime.datetime.combine(
                date=next_broadcast,
                time=datetime.time()
            )
            
            delta = next_broadcast_time - now
            delta_s = delta.total_seconds()
            
            logger.info(f"weekcast sleeps {delta_s} s...")
            await asyncio.sleep(delta_s)
            
    async def init_logger_svc(self) -> None:
        """
        Abandoned logging service
        """
        from src.svc.common.logsvc import Logger

        logger_addr = "127.0.0.1:7215"
        if not logger_addr.startswith("http://"):
            logger_addr = "http://" + logger_addr

        try:
            await self.http.get(logger_addr)
        except aiohttp_exc.ClientConnectorError:
            ...

        self.logger = Logger(addr=logger_addr)

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
        
        def fuckwarning(*args, **kwargs):
            # WHO ASKED????????
            # WHO FUCKING ASKED ABOUT YOUR FUCKING DEPRECATIONS????
            #
            # vkbottle's like "ugh we gettin' rid of blueprints"
            # YES BITCH YOU ARE! AND I'M NOT EVEN USING THEM!!!
            # IT'S YOUR FUCKING SHITTY IMPORT SOMEWHERE AND YOU
            # STILL WARN **ME**, WHEN IT'S NOT EVEN MY FAULT!!!!
            #
            # pydantic's like "oi mate u using parse_raw... use model_shittify_json instead"
            # OH YEAH? ARE YOU SURE THIS IS ME?
            # NOT THE FUCKING AIOGRAM OR VKBOTTLE? I HAVE NO "parse_raw"
            # OCCURRENCES IN MY CODE WHATSOEVER!
            #
            # FUCK YOU, NEXT TIME I'M NOT USING THESE
            # AND WRITING MY OWN IMPLEMENTATIONS FROM SCRATCH
            # SIT ON YOUR vkBOTTLES FUCKING AioTISTIC BITCHES
            ...
        
        warnings.showwarning = fuckwarning

    def init_fs(self) -> None:
        self.data_dir = Path(".", "data")
        self.data_dir.mkdir(exist_ok=True)

        settings_path = self.data_dir.joinpath("settings.json")
        last_notify_path = self.data_dir.joinpath("last_notify.json")
        weekcast_path = self.data_dir.joinpath("weekcast.json")
        
        self.settings = Settings.load_or_init(path=settings_path)
        self.weekcast = WeekCast.load_or_init(path=weekcast_path)
        self.schedule = ScheduleApi(
            addr=self.settings.server.addr,
            last_notify=LastNotify.load_or_init(path=last_notify_path),
            ready_channel=asyncio.Queue()
        )

        if self.settings.logging and self.settings.logging.dir:
            self.log_path = self.settings.logging.dir.joinpath("log.txt")
            self.log_file = self.loop.run_until_complete(
                aiofiles.open(
                    self.log_path,
                    mode="a",
                    encoding="utf8",
                    newline="\n"
                )
            )

    def init_vars(
        self, 
        init_handlers: bool = True,
        init_middlewares: bool = True,
    ) -> None:
        """
        ## Init variables/constants, by default they are all `None`
        """
        from src.svc import vk, telegram

        self.loop.run_until_complete(self.init_http())

        if self.settings.tokens.vk:
            self.vk_bot = vk.load(token=self.settings.tokens.vk, loop=self.loop)
            self.loop.run_until_complete(self.get_vk_bot_info())
        if self.settings.tokens.tg:
            self.tg_bot = telegram.load_bot(token=self.settings.tokens.tg)
            self.tg_router = telegram.load_router()
            self.tg_dispatch = telegram.load_dispatch(self.tg_router)
            self.loop.run_until_complete(self.get_tg_bot_info())

        if init_middlewares:
            from src.svc.common import middlewares
            middlewares.router.assign()
        
        if init_handlers:
            from src.svc.common.bps import admin, reset, settings, init, zoom, hub
        
        from src.svc.common import Ctx

        self.ctx = Ctx()
        self.init_redis()

        self.loop.run_until_complete(self.init_logger_svc())
        self.loop.run_until_complete(self.init_schedule_api())

    def init_periods(self) -> None:
        self.create_task(self.weekcast_loop())
            
    def create_task(self, coro, *, name=None) -> None:
        task = self.loop.create_task(coro, name=name)
        task.add_done_callback(self._handle_task)

    def _handle_task(self, task: asyncio.Task) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            try:
                fn = task.get_coro().cr_code.co_name
            except AttributeError:
                fn = "unknown"

            logger.exception(
                f"task function <{fn}> raised {type(e).__name__}: {e}"
            )


defs = Defs()
