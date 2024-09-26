from __future__ import annotations
from loguru import logger
import time
import asyncio
import json
import datetime
from copy import deepcopy
from json.encoder import JSONEncoder
from typing import Literal, Optional, Callable, Any, TypeVar, TYPE_CHECKING
from copy import deepcopy
from dataclasses import dataclass, field
from pydantic import BaseModel
from vkbottle import ShowSnackbarEvent, VKAPIError
from vkbottle_types.responses.messages import MessagesSendUserIdsResponseItem
from vkbottle_types.codegen.objects import MessagesMessageActionStatus
from aiogram.types import Message as TgMessage, CallbackQuery, ChatMemberUpdated
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest
from redis.commands.json.path import Path
from src import defs, RedisName, text
from src.api.schedule import Notify
from src.data import RepredBaseModel, HiddenVars, week
from src.data.schedule import Schedule, format as sc_format, Page, Formation
from src.data.schedule.raw import Kind, KIND_LITERAL
from src.data.schedule.compare import PageCompare
from src.data.settings import Settings, Mode
from src.data.range import Range
from src.svc import vk, telegram as tg
from src.svc.vk.types_ import MessageV2 as VkMessage, RawEvent
from src.svc.common.states import formatter as states_fmt, Values
from src.svc.common.states.tree import HUB
from src.svc.common.navigator import Navigator, DbNavigator
from src.svc.common import pagination, messages
from src.svc.common import keyboard as kb, error
from src.svc.common.states.tree import Space


if TYPE_CHECKING:
    from src.data.settings import MODE_LITERAL


class Source:
    """
    ## Different sources of messengers, events
    """
    VK = "vk"
    """ ## Message/event came from VK """
    TG = "tg"
    """ ## Message/event came from Telegram """
    TG_MY_CHAT_MEMBER = "tg_my_chat_member"
    """
    ## Someone was invited/kicked from the group chat
    This event is only used for logging
    """
    TG_EDITED_MESSAGE = "tg_edited_message"
    """
    ## Message was edited on Telegram
    This event is only used for logging
    """
    TG_CHANNEL_POST = "tg_channel_post"
    """
    ## Post was made in a Telegram channel
    This event is only used for logging
    """
    TG_EDITED_CHANNEL_POST = "tg_edited_channel_post"
    """
    ## Post was edited in a Telegram channel
    This event is only used for logging
    """

    MESSAGE = "message"
    """ ## Event came from an incoming message """
    EVENT = "event"
    """ ## Event came from pressing bot's keyboard buttons """

MESSENGER_OR_EVT_SOURCE = Literal[
    "vk",
    "tg",
    "tg_my_chat_member",
    "tg_edited_message",
    "tg_channel_post",
    "tg_edited_channel_post"
]
MESSENGER_SOURCE = Literal["vk", "tg"]
MESSENGER_SOURCE_T = TypeVar("MESSENGER_SOURCE_T")
EVENT_SOURCE = Literal["message", "event"]

DB_BASE_CTX_REBUILDED = False


@dataclass
class BroadcastFormation:
    mode: str
    formation: str
    header: str

    def add_header_to(self, fmt_schedule: str) -> str:
        return f"{self.header}\n\n{fmt_schedule}"

    @staticmethod
    def filter_for_formation(
        form: str,
        mappings: list[BroadcastFormation]
    ) -> list[BroadcastFormation]:
        relatives = []

        """ # Search for relative mapping """
        for mapping in mappings:
            if mapping.formation == form:
                relatives.append(mapping)

        return relatives

class DbBaseCtx(BaseModel):
    chat_id: int
    is_registered: bool
    is_admin: Optional[bool]
    is_switching_modes: Optional[bool]

    navigator: DbNavigator
    settings: Settings
    schedule: Schedule

    pages: pagination.Container

    last_call: float = 0.0
    last_everything: Optional[CommonEverything]
    last_bot_message: Optional[CommonBotMessage]
    last_groups_schedule: Optional[CommonBotMessage]
    last_teachers_schedule: Optional[CommonBotMessage]

    @classmethod
    def ensure_rebuild(cls):
        global DB_BASE_CTX_REBUILDED

        if not DB_BASE_CTX_REBUILDED:
            cls.model_rebuild()
            DB_BASE_CTX_REBUILDED = True

    @classmethod
    def from_runtime(cls: type[DbBaseCtx], ctx: BaseCtx) -> DbBaseCtx:
        DbBaseCtx.ensure_rebuild()

        return cls(
            chat_id=ctx.chat_id,
            is_registered=ctx.is_registered,
            is_admin=ctx.is_admin,
            is_switching_modes=ctx.is_switching_modes,
            navigator=ctx.navigator.to_db(),
            settings=ctx.settings,
            schedule=ctx.schedule,
            pages=ctx.pages,
            last_call=ctx.last_call,
            last_everything=ctx.last_everything,
            last_bot_message=ctx.last_bot_message,
            last_groups_schedule=ctx.last_groups_schedule,
            last_teachers_schedule=ctx.last_teachers_schedule
        )

    def to_runtime(self) -> BaseCtx:
        return BaseCtx.from_db(self)


@dataclass
class BaseCtx:
    chat_id: int
    is_registered: bool = field(default_factory=lambda: False)
    is_admin: bool = field(default_factory=lambda: False)
    is_switching_modes: bool = field(default_factory=lambda: False)

    navigator: Navigator = field(default_factory=Navigator)
    """ # `Back`, `next` buttons tracer """
    settings: Settings = field(default_factory=Settings)
    """ # Storage for settings and zoom data """
    schedule: Schedule = field(default_factory=Schedule)
    """ # Schedule data """
    
    pages: pagination.Container = field(default_factory=pagination.Container)
    """
    # Page storage for big data
    Used to store generated pages
    for massive data that can't
    fit in one message (like zoom entries).
    """

    last_call: float = field(default_factory=lambda: .0)
    """
    # Last UNIX time when user interacted with bot
    Used to throttle users who
    click buttons too fast.
    """
    last_everything: Optional[CommonEverything] = None
    """
    # Last received event
    Used for `navigator`, that passes `everything`
    to `on_enter`, `on_exit` methods of states.
    """
    last_bot_message: Optional[CommonBotMessage] = None
    """
    # Last message sent by the bot
    Used to resend it when for some reason
    user interacts with OLD messages.
    """
    last_groups_schedule: Optional[CommonBotMessage] = None
    """
    # Last groups schedule message sent by the bot
    Used to reply to it when sending an updated one.
    """
    last_teachers_schedule: Optional[CommonBotMessage] = None
    """
    # Last teachers schedule message sent by the bot
    Used to reply to it when sending an updated one.
    """

    @property
    def db_key(self) -> str:
        return f"{self.last_everything.src.upper()}_{self.chat_id}"

    @classmethod
    def from_db(cls: type[BaseCtx], db: DbBaseCtx) -> BaseCtx:
        self = cls(
            chat_id=db.chat_id,
            is_admin=db.is_admin if db.is_admin is not None else False,
            is_registered=db.is_registered,
            is_switching_modes=db.is_switching_modes,
            navigator=db.navigator.to_runtime(db.last_everything),
            settings=db.settings,
            schedule=db.schedule,
            pages=db.pages,
            last_call=db.last_call,
            last_everything=db.last_everything,
            last_bot_message=db.last_bot_message,
            last_groups_schedule=db.last_groups_schedule,
            last_teachers_schedule=db.last_teachers_schedule
        )

        self.settings.zoom.check_all()

        return self

    def to_db(self) -> DbBaseCtx:
        return DbBaseCtx.from_runtime(self)

    async def set_last_bot_message(self, message: CommonBotMessage):
        self.last_bot_message = message

    async def save(self):
        # backup hidden vars and delete them from last_everything
        hidden_vars = self.last_everything.take_hidden_vars()

        self_db = await defs.loop.run_in_executor(None, self.to_db)

        # this is so retarded,
        # i couldn't just do `self_db.dict()`,
        # because vkbottle's `Message` BaseModel
        # contains a bunch of shitty enums
        # that are only properly serialized
        # when calling `self_db.json()`, but not `self_db.dict()`
        self_db_json = self_db.model_dump_json()
        self_db_dict = json.loads(self_db_json)

        self.last_everything.set_hidden_vars(hidden_vars)

        await defs.redis.json(
            encoder=JSONEncoder(default=str)
        ).set(
            self.db_key,
            Path.root_path(),
            self_db_dict,
            decode_keys=True
        )
        
    @property
    def is_temp_mode(self) -> bool:
        return not not self.schedule.temp_mode

    @property
    def mode(self) -> "MODE_LITERAL":
        if self.is_temp_mode: return self.schedule.temp_mode
        else: return self.settings.mode

    @property
    def identifier(self) -> str:
        from src.data.settings import Mode
        if self.schedule.temp_mode == Mode.GROUP:
            return self.schedule.temp_group
        if self.schedule.temp_mode == Mode.TEACHER:
            return self.schedule.temp_teacher
        if self.settings.mode == Mode.GROUP:
            return self.settings.group.confirmed
        if self.settings.mode == Mode.TEACHER:
            return self.settings.teacher.confirmed

    def register(self) -> None:
        self.is_registered = True

    async def throttle(self) -> None:
        """ ## Stop executing for a short period to avoid rate limit """
        current_time = time.time()

        # allowed to call again after 1 second
        next_allowed_time = self.last_call + 1

        if next_allowed_time > current_time:
            # then throttle
            sleep_secs_until_allowed: float = next_allowed_time - current_time
            await asyncio.sleep(sleep_secs_until_allowed)

        self.last_call = current_time

    def set_everything(self, everything: CommonEverything) -> None:
        self.last_everything = everything
        self.navigator.set_everything(everything)

    def get_schedule_as_group(self) -> Optional[Formation]:
        try:
            page = defs.schedule.get_groups()
            return page.get_by_name(self.identifier)
        except AttributeError:
            return None

    def get_schedule_as_teacher(self) -> Optional[Formation]:
        try:
            page = defs.schedule.get_teachers()
            return page.get_by_name(self.identifier)
        except AttributeError:
            return None

    def get_schedule(self) -> Optional[Formation]:
        if self.mode == Mode.GROUP:
            return self.get_schedule_as_group()
        if self.mode == Mode.TEACHER:
            return self.get_schedule_as_teacher()
        
    def fmt_schedule_as_group(self) -> Optional[str]:
        try:
            form = self.get_schedule_as_group()
            return sc_format.formation(
                form=form,
                week_pos=self.schedule.get_week_or_current(),
                entries=self.settings.zoom.entries.list,
                mode=self.settings.mode,
                do_tg_markup=self.last_everything.is_from_tg_generally
            )
        except AttributeError:
            return None

    def fmt_schedule_as_teacher(self) -> Optional[str]:
        try:
            form = self.get_schedule_as_teacher()
            return sc_format.formation(
                form=form,
                week_pos=self.schedule.get_week_or_current(),
                entries=self.settings.tchr_zoom.entries.list,
                mode=self.settings.mode,
                do_tg_markup=self.last_everything.is_from_tg_generally
            )
        except AttributeError:
            return None
    
    def fmt_schedule(self) -> Optional[str]:
        if self.mode == Mode.GROUP:
            return self.fmt_schedule_as_group()
        if self.mode == Mode.TEACHER:
            return self.fmt_schedule_as_teacher()
    
    def is_backward_week_shift_allowed(self) -> bool:
        """ # Is it allowed to view the previous week """
        try:
            form = self.get_schedule()
            return form.first_week().week < self.schedule.get_week_or_current()
        except (AttributeError, IndexError, TypeError): return False
        
    def is_forward_week_shift_allowed(self) -> bool:
        """ # Is it allowed to view the next week """
        try:
            form = self.get_schedule()
            return self.schedule.get_week_or_current() < form.last_week().week
        except (AttributeError, IndexError, TypeError): return False
    
    def shift_week_backward(self) -> bool:
        try:
            form = self.get_schedule()
            target = form.prev_week_self(self.schedule.get_week_or_current())
            if week.current_active() == target.week:
                self.schedule.reset_temp_week()
            else:
                self.schedule.temp_week = target.week
            return True
        except:
            return False
        
    def shift_week_forward(self) -> bool:
        try:
            form = self.get_schedule()
            target = form.next_week_self(self.schedule.get_week_or_current())
            if week.current_active() == target.week:
                self.schedule.reset_temp_week()
            else:
                self.schedule.temp_week = target.week
            return True
        except AttributeError:
            return False
        
    def jump_week_backward(self) -> bool:
        try:
            form = self.get_schedule()
            if self.schedule.get_week_or_current() > week.current_active():
                # jump to the current week
                self.schedule.reset_temp_week()
            else:
                # jump to the beginning
                dww = form.first_week()
                self.schedule.temp_week = dww.week
            return True
        except AttributeError:
            return False
    
    def jump_week_forward(self) -> bool:
        try:
            form = self.get_schedule()
            if self.schedule.get_week_or_current() < week.current_active():
                # jump to the current week
                self.schedule.reset_temp_week()
            else:
                # jump to the end
                dww = form.last_week()
                self.schedule.temp_week = dww.week
            return True
        except AttributeError:
            return False

    async def send_custom_broadcast(self, message: CommonBotMessage):
        from src.data.settings import Mode

        new_message = await message.send()

        if new_message.id is not None:
            # we do these after sending and not before 
            # 'cause of the sending delay
            self.navigator.jump_back_to_or_append(HUB.I_MAIN)
            self.week_shift = 0

            if self.settings.mode == Mode.GROUP:
                self.last_groups_schedule = new_message
            elif self.settings.mode == Mode.TEACHER:
                self.last_teachers_schedule = new_message
            
            self.last_bot_message = new_message

            await self.save()

            if self.settings.should_pin:
                await new_message.safe_pin()
        else:
            raise error.BroadcastSendFail("sent message id is None")

    async def retry_send_custom_broadcast(
        self,
        message: CommonBotMessage,
        max_tries: int = 3,
        interval: int = 10 # in secs
    ):
        from src.data.settings import Mode
        
        tries = 0
        errors = []
        successful = False

        while tries < max_tries:
            try:
                await self.send_custom_broadcast(message)
                successful = True
                break
            except Exception as e:
                tries += 1
                errors.append(f"{type(e).__name__}({e})")
                await asyncio.sleep(interval)

        if successful:
            logger.opt(colors=True).success(
                f"<G><k><d>BROADCASTING TO {self.db_key} {self.identifier}</></></> "
                f"succeeded after {tries} times"
            )
        else:
            logger.opt(colors=True).error(
                f"<R><k><d>BROADCASTING TO {self.db_key} {self.identifier}</></></> "
                f"failed all {max_tries} times with errors: {' | '.join(errors)}"
            )

    async def send_broadcast(self, mappings: list[BroadcastFormation]):
        from src.data.settings import Mode

        last_schedule = None

        if self.settings.mode == Mode.GROUP:
            last_schedule = self.last_groups_schedule
        elif self.settings.mode == Mode.TEACHER:
            last_schedule = self.last_teachers_schedule

        for mapping in mappings:
            reply_to = None

            fmt_schedule = None
            if self.settings.mode == Mode.GROUP:
                fmt_schedule = self.fmt_schedule_as_group()
            elif self.settings.mode == Mode.TEACHER:
                fmt_schedule = self.fmt_schedule_as_teacher()
            
            bcast_text = None
            raw_bcast_text = mapping.add_header_to(fmt_schedule)
            
            if last_schedule:
                reply_to = last_schedule.id
                bcast_text = (
                f"{messages.format_replied_to_schedule_message()}\n\n"
                f"{raw_bcast_text}"
            )
            else:
                bcast_text = raw_bcast_text
            
            bcast_message = CommonBotMessage(
                text=bcast_text,
                keyboard=kb.Keyboard.hub_broadcast_default(
                    is_previous_dead_end=(
                        not self.is_backward_week_shift_allowed()
                    ),
                    is_previous_jump_dead_end=(
                        not self.is_backward_week_shift_allowed()
                    ),
                    is_next_dead_end=(
                        not self.is_forward_week_shift_allowed()
                    ),
                    is_next_jump_dead_end=(
                        not self.is_forward_week_shift_allowed()
                    )
                ),
                can_edit=False,
                src=self.last_everything.src,
                chat_id=self.chat_id,
                reply_to=reply_to,
            )

            async def try_without_reply(
                e: Exception,
                bcast_message: CommonBotMessage,
                mapping: BroadcastFormation
            ):
                logger.opt(colors=True).warning(
                    f"<Y><k><d>BROADCASTING TO {self.db_key} {self.identifier}</></></> "
                    f"failed with {type(e).__name__}({e}), trying without replying"
                )

                bcast_message.reply_to = None

                try:
                    logger.opt(colors=True).info(
                        f"<W><k><d>BROADCASTING TO {self.db_key} {self.identifier}</></></> "
                        f"{mapping.header}"
                    )
                    await self.send_custom_broadcast(
                        message=bcast_message
                    )
                except Exception as e:
                    logger.opt(colors=True).warning(
                        f"<Y><k><d>BROADCASTING TO {self.db_key} {self.identifier}</></></> "
                        f"unknown exception: {type(e).__name__}({e})"
                    )
                except error.BroadcastSendFail:
                    ...

            try:
                logger.opt(colors=True).info(
                    f"<W><k><d>BROADCASTING TO {self.db_key} {self.identifier}</></></> "
                    f"{mapping.header}"
                )
                await self.send_custom_broadcast(
                    message=bcast_message
                )
            except VKAPIError[913] as e:
                await try_without_reply(e, bcast_message, mapping)
            except VKAPIError[100] as e:
                if "cannot reply this message" in e.description:
                    await try_without_reply(e, bcast_message, mapping)
            except TelegramBadRequest as e:
                logger.opt(colors=True).warning(
                    f"<Y><k><d>BROADCASTING TO {self.db_key} {self.identifier}</></></> "
                    f"{type(e).__name__}({e})"
                )

                if "chat not found" in e.message:
                    ...
                
                if "repl" in e.message:
                    await try_without_reply(e, bcast_message, mapping)

            except TelegramForbiddenError:
                logger.opt(colors=True).warning(
                    f"<Y><k><d>BROADCASTING TO {self.db_key} {self.identifier}</></></> "
                    f"user had blocked the bot"
                )
            except error.BroadcastSendFail as e:
                logger.opt(colors=True).warning(
                    f"<Y><k><d>BROADCASTING TO {self.db_key} {self.identifier}</></></> "
                    f"sending the broadcast message had failed: {type(e).__name__}({e})"
                )
            except Exception as e:
                logger.opt(colors=True).warning(
                    f"<Y><k><d>BROADCASTING TO {self.db_key} {self.identifier}</></></> "
                    f"unknown exception: {type(e).__name__}({e})"
                )

@dataclass
class Ctx:
    async def is_added(self, everything: CommonEverything) -> bool:
        src = None
        if everything.src.startswith("tg"):
            src = "tg"
        elif everything.src.startswith("vk"):
            src = "vk"
        return bool(await defs.redis.exists(f"{src.upper()}_{everything.chat_id}"))

    async def add_from_everything(self, everything: CommonEverything) -> BaseCtx:
        if everything.is_from_vk:
            ctx = await self.add_vk(everything)
        elif everything.is_from_tg:
            ctx = await self.add_tg(everything)

        return ctx

    async def add(
        self,
        everything: Optional[CommonEverything] = None
    ) -> BaseCtx:
        ctx = BaseCtx(
            chat_id=everything.chat_id,
            last_call=time.time(),
        )
        ctx.set_everything(everything)

        return ctx

    async def add_vk(self, everything: Optional[CommonEverything] = None) -> BaseCtx:
        ctx = await self.add(everything)
        logger.opt(colors=True).info(
            "<G><k><d>+</></></> created ctx for vk {}", everything.chat_id
        )

        return ctx

    async def add_tg(self, everything: Optional[CommonEverything] = None) -> BaseCtx:
        ctx = await self.add(everything)
        logger.opt(colors=True).info(
            "<G><k><d>+</></></> created ctx for tg {}", everything.chat_id
        )

        return ctx

    async def delete(self, key: str):
        await defs.redis.json().delete(key)

    async def get_who_needs_broadcast(
        self,
        groups: list[str]
    ) -> Optional[list]:
        from src.data.settings import Mode

        if not groups:
            return None

        affected_groups_query = "|".join(groups)
        query = (
            f"@{RedisName.IS_REGISTERED}:""{true} "
            f"@{RedisName.MODE}:{Mode.GROUP} "
            f"@{RedisName.BROADCAST}:""{true} "
            f"@{RedisName.GROUP}:({affected_groups_query})"
        )
        response: list = await defs.redis.execute_command(
            f"FT.SEARCH",
            f"{RedisName.BROADCAST}",
            f"{query}",
            f"LIMIT",
            f"0",
            f"10000" # fuck it
        )

        return response

    async def get_who_needs_tchr_broadcast(
        self,
        teachers: list[str]
    ) -> Optional[list]:
        from src.data.settings import Mode

        if not teachers:
            return None

        affected_teachers_query = "|".join(teachers)
        query = (
            f"@{RedisName.IS_REGISTERED}:""{true} "
            f"@{RedisName.MODE}:{Mode.TEACHER} "
            f"@{RedisName.BROADCAST}:""{true} "
            f"@{RedisName.TEACHER}:({affected_teachers_query})"
        )
        response: list = await defs.redis.execute_command(
            f"FT.SEARCH",
            f"{RedisName.TCHR_BROADCAST}",
            f"{query}",
            f"LIMIT",
            f"0",
            f"10000"
        )

        return response

    async def get_everyone(self) -> Optional[list]:
        all_keys = await defs.redis.keys()
        all_raw_ctxs = await defs.redis.json().mget(all_keys, "$")
        
        return all_raw_ctxs

    async def parse_redis_result(self, result: list) -> list[BaseCtx]:
        ctxs: list[BaseCtx] = []

        for i, key_or_value in enumerate(result[1:]):
            even = i % 2
            is_key = even == 0
            is_value = even == 1

            if is_key:
                continue

            value = key_or_value[1]

            # convert ["string json" -> DbBaseCtx]
            # in executor
            db_ctx = await defs.loop.run_in_executor(
                None,
                DbBaseCtx.model_validate_json,
                value
            )
            # convert [DbBaseCtx -> BaseCtx]
            # in executor
            ctx = await defs.loop.run_in_executor(
                None,
                db_ctx.to_runtime
            )

            ctxs.append(ctx)

        return ctxs

    async def get_who_needs_broadcast_parsed(self, groups: list[str]) -> list[BaseCtx]:
        raw_result = await self.get_who_needs_broadcast(groups)

        if raw_result is None:
            return []

        return await self.parse_redis_result(raw_result)

    async def get_who_needs_tchr_broadcast_parsed(self, teachers: list[str]) -> list[BaseCtx]:
        raw_result = await self.get_who_needs_tchr_broadcast(teachers)

        if raw_result is None:
            return []

        return await self.parse_redis_result(raw_result)
    
    async def get_everyone_parsed(self) -> list[BaseCtx]:
        parsed = []
        raw_result = await self.get_everyone()

        if raw_result is None:
            return []

        for raw_ctx in raw_result:
            # convert [dict -> DbBaseCtx]
            # in executor
            db_ctx = await defs.loop.run_in_executor(
                None,
                DbBaseCtx.model_validate,
                raw_ctx[0]
            )
            # convert [DbBaseCtx -> BaseCtx]
            # in executor
            ctx = await defs.loop.run_in_executor(
                None,
                db_ctx.to_runtime
            )

            parsed.append(ctx)

        return parsed

    async def broadcast_mappings(
        self,
        mappings: list[BroadcastFormation]
    ):
        from src.data.settings import Mode

        affected_groups = [
            mapping.formation for mapping in mappings if mapping.mode == Mode.GROUP
        ]
        affected_teachers = [
            mapping.formation for mapping in mappings if mapping.mode == Mode.TEACHER
        ]

        chats_that_need_group_broadcast = (
            await self.get_who_needs_broadcast_parsed(affected_groups)
        )
        chats_that_need_tchr_broadcast = (
            await self.get_who_needs_tchr_broadcast_parsed(affected_teachers)
        )

        for chat in chats_that_need_group_broadcast:
            chat.schedule.reset_temps()
            chat_teacher = chat.settings.group.confirmed
            chat_relative_mappings = (
                BroadcastFormation.filter_for_formation(chat_teacher, mappings)
            )

            await chat.send_broadcast(chat_relative_mappings)

        for chat in chats_that_need_tchr_broadcast:
            chat.schedule.reset_temps()
            chat_teacher = chat.settings.teacher.confirmed
            chat_relative_mappings = (
                BroadcastFormation.filter_for_formation(chat_teacher, mappings)
            )

            await chat.send_broadcast(chat_relative_mappings)

    async def broadcast(self, notify: Notify):
        from src.data.schedule.compare import ChangeType
        from src.data.settings import Mode

        mappings: list[BroadcastFormation] = []

        for (mode, page_cmp) in [
            (Mode.GROUP, notify.groups),
            (Mode.TEACHER, notify.teachers)
        ]:
            do_detailed_compare = (
                page_cmp.date.is_same() if page_cmp is not None else False
            )
            
            change_types = {
                ChangeType.APPEARED: page_cmp.formations.appeared if page_cmp else None,
                ChangeType.CHANGED: page_cmp.formations.changed if page_cmp else None
            }
            
            for (change, formations) in change_types.items():
                formations: list[RepredBaseModel]
                if formations is None: continue
                
                for formation in formations:
                    name = formation.repr_name
                    header = None
                    if mode == Mode.GROUP:
                        header = messages.format_group_changed_in_schedule(
                            change=change
                        )
                    elif mode == Mode.TEACHER:
                        header = messages.format_teacher_changed_in_schedule(
                            change=change
                        )
                    
                    if change == ChangeType.APPEARED:
                        fmt_changes = sc_format.CompareFormatted(
                            text=None,
                            has_detailed=False
                        )
                    elif change == ChangeType.CHANGED:
                        fmt_changes = sc_format.cmp(
                            model=formation,
                            do_detailed=do_detailed_compare
                        )
            
                    if fmt_changes.text is not None:
                        header += "\n\n"

                        if fmt_changes.has_detailed and not do_detailed_compare:
                            header += messages.format_detailed_compare_not_shown()
                            header += "\n"

                        header += fmt_changes.text

                    bcast_formation = BroadcastFormation(
                        mode=mode,
                        formation=name,
                        header=header
                    )
                    
                    mappings.append(bcast_formation)
            
        await self.broadcast_mappings(mappings)


class BaseCommonEvent(HiddenVars):
    src: Optional[MESSENGER_OR_EVT_SOURCE] = None
    chat_id: Optional[int] = None

    @property
    def ctx(self) -> Optional[BaseCtx]:
        try:
            return self.__hidden_vars__["ctx"]
        except KeyError:
            return None

    def set_ctx(self, ctx: BaseCtx):
        self.__hidden_vars__["ctx"] = ctx

    def del_ctx(self):
        del self.__hidden_vars__["ctx"]

    @property
    def was_processed(self) -> bool:
        return self.__hidden_vars__["was_processed"]

    def set_was_processed(self, value: bool):
        self.__hidden_vars__["was_processed"] = value

    @property
    def is_from_vk(self):
        return self.src == Source.VK

    @property
    def is_from_tg(self):
        return self.src == Source.TG

    @property
    def is_from_tg_generally(self):
        return self.src in [
            Source.TG,
            Source.TG_MY_CHAT_MEMBER,
            Source.TG_EDITED_MESSAGE,
            Source.TG_CHANNEL_POST,
            Source.TG_EDITED_CHANNEL_POST
        ]

    @property
    def is_from_tg_my_chat_member(self):
        return self.src == Source.TG_MY_CHAT_MEMBER

    @property
    def is_from_tg_edited_message(self):
        return self.src == Source.TG_EDITED_MESSAGE

    @property
    def is_from_tg_channel_post(self):
        return self.src == Source.TG_CHANNEL_POST

    @property
    def is_from_tg_edited_channel_post(self):
        return self.src == Source.TG_EDITED_CHANNEL_POST

    async def load_ctx(self) -> BaseCtx:
        DbBaseCtx.ensure_rebuild()

        src = None
        if self.src.startswith("tg"):
            src = "tg"
        elif self.src.startswith("vk"):
            src = "vk"
        
        db_ctx = await defs.redis.json().get(f"{src.upper()}_{self.chat_id}")
        db_ctx_parsed = DbBaseCtx.parse_obj(db_ctx)

        self.set_ctx(db_ctx_parsed.to_runtime())

        logger.debug(f"ctx {self.ctx.db_key} loaded and set")

        return self.ctx

    @property
    def navigator(self) -> Navigator:
        return self.ctx.navigator

    def preprocess_text(
        self,
        text: str,
        add_tree: bool,
        everything: CommonEverything,
        base_lvl: int = 1,
        tree_values: Values = None
    ) -> str:
        """
        ## Add generic components to `text`
        - debug info
        - wise mystical tree of states
        """
        if add_tree:
            text = states_fmt.tree(
                navigator=self.ctx.navigator,
                everything=everything,
                values=tree_values,
                base_lvl=base_lvl
            ) + "\n\n" + text

        if messages.DEBUGGING:
            text = messages.format_debug(
                trace=self.ctx.navigator.trace,
                back_trace=self.ctx.navigator.back_trace,
                last_bot_message=self.ctx.last_bot_message,
                settings=self.ctx.settings
            ) + "\n\n" + text

        return text


class CommonMessage(BaseCommonEvent):
    """
    ## Container for only one source of received event
    - for example, if we received a message from VK,
    we'll pass it to `vk` field, leaving others as `None`
    """
    vk: Optional[VkMessage] = None
    """ ## Info about a received VK message """
    tg: Optional[TgMessage] = None
    """ ## Info about a received Telegram message """
    tg_edited_message: Optional[TgMessage] = None
    """ ## Info about an edited Telegram message """
    tg_channel_post: Optional[TgMessage] = None
    """ ## Info about a received Telegram channel post """
    tg_edited_channel_post: Optional[TgMessage] = None
    """ ## Info about an edited Telegram channel post """

    @classmethod
    def from_vk(cls, message: VkMessage):
        self = cls(
            src=Source.VK,
            chat_id=message.peer_id,
            vk=message,
        )

        return self

    @classmethod
    def from_tg(cls, message: TgMessage):
        self = cls(
            src=Source.TG,
            chat_id=message.chat.id,
            tg=message,
        )

        return self

    @classmethod
    def from_tg_edited_message(cls, message: TgMessage):
        self = cls(
            src=Source.TG_EDITED_MESSAGE,
            chat_id=message.chat.id,
            tg_edited_message=message,
        )

        return self

    @classmethod
    def from_tg_channel_post(cls, message: TgMessage):
        self = cls(
            src=Source.TG_CHANNEL_POST,
            chat_id=message.chat.id,
            tg_channel_post=message,
        )

        return self

    @classmethod
    def from_tg_edited_channel_post(cls, message: TgMessage):
        self = cls(
            src=Source.TG_EDITED_CHANNEL_POST,
            chat_id=message.chat.id,
            tg_edited_channel_post=message,
        )

        return self

    @property
    def tg_chat_type(self) -> str:
        if self.is_from_tg:
            return self.tg.chat.type
        elif self.is_from_tg_edited_message:
            return self.tg_edited_message.chat.type
        elif self.is_from_tg_channel_post:
            return self.tg_channel_post.chat.type
        elif self.is_from_tg_edited_channel_post:
            return self.tg_edited_channel_post.chat.type

    @property
    def is_tg_supergroup(self) -> bool:
        if not self.is_from_tg:
            return False

        return self.tg_chat_type == tg.ChatType.SUPERGROUP

    @property
    def is_tg_group(self) -> bool:
        if not self.is_from_tg:
            return False

        return self.tg_chat_type == tg.ChatType.GROUP

    @property
    def is_vk_group(self) -> bool:
        if not self.is_from_vk:
            return False

        return self.is_group_chat and self.is_from_vk

    @property
    def is_group_chat(self) -> bool:
        if self.is_from_vk:
            return vk.is_group_chat(self.vk.peer_id, self.vk.from_id)
        if self.is_from_tg_generally:
            return tg.is_group_chat(self.tg_chat_type)

    @property
    def message_id(self)-> Optional[int]:
        if self.is_from_vk:
            return self.vk.message_id
        if self.is_from_tg:
            return self.tg.message_id
        if self.is_from_tg_edited_message:
            return self.tg_edited_message.message_id
        if self.is_from_tg_channel_post:
            return self.tg_channel_post.message_id
        if self.is_from_tg_edited_channel_post:
            return self.tg_edited_channel_post.message_id

    @property
    def text(self) -> Optional[str]:
        if self.is_from_vk:
            return self.vk.text
        if self.is_from_tg:
            return self.tg.text
        if self.is_from_tg_edited_message:
            return self.tg_edited_message.text
        if self.is_from_tg_channel_post:
            return self.tg_channel_post.text
        if self.is_from_tg_edited_channel_post:
            return self.tg_edited_channel_post.text

    @property
    def forwards_text(self) -> Optional[str]:
        if self.is_from_vk:
            if self.vk.fwd_messages is None:
                return None

            return vk.text_from_forwards(self.vk.fwd_messages)

        return None

    @property
    def corresponding(self) -> Any:
        if self.is_from_vk:
            return self.vk
        if self.is_from_tg:
            return self.tg
        if self.is_from_tg_edited_message:
            return self.tg_edited_message
        if self.is_from_tg_channel_post:
            return self.tg_channel_post
        if self.is_from_tg_edited_channel_post:
            return self.tg_edited_channel_post
    
    @property
    def dt(self) -> datetime.datetime:
        if self.is_from_vk:
            return datetime.datetime.fromtimestamp(self.vk.date)
        if self.is_from_tg:
            return self.tg.date
        if self.is_from_tg_edited_message:
            return self.tg_edited_message.date
        if self.is_from_tg_channel_post:
            return self.tg_channel_post.date
        if self.is_from_tg_edited_channel_post:
            return self.tg_edited_channel_post.date

    def tg_is_invite(self) -> bool:
        if not self.is_from_tg:
            return False

        if self.tg.content_type != "new_chat_members":
            return False

        for new in self.tg.new_chat_members:
            if new.id == defs.tg_bot_info.id:
                return True

        return False

    def tg_did_user_used_bot_command(self) -> bool:
        if not self.is_from_tg:
            return False

        if self.tg.text is None:
            return False

        if self.tg.text == "/":
            return False
        elif any(cmd in self.tg.text for cmd in defs.tg_bot_commands):
            return True

        return False

    def tg_did_user_mentioned_bot(self) -> bool:
        if self.tg.entities is None:
            return False

        mentions = tg.extract_mentions(self.tg.entities, self.tg.text)

        # if our bot not in mentions
        if defs.tg_bot_mention not in mentions:
            return False

        return True

    def tg_did_user_replied_to_bot_message(self) -> bool:
        if self.tg.reply_to_message is None:
            return False

        return self.tg.reply_to_message.from_user.id == defs.tg_bot_info.id

    def tg_is_for_bot(self) -> bool:
        if not self.is_from_tg:
            return False

        event = self.tg
        is_group_chat = tg.is_group_chat(event.chat.type)

        if not self.tg_is_invite() and (is_group_chat and not (
            self.tg_did_user_used_bot_command() or
            self.tg_did_user_mentioned_bot() or
            self.tg_did_user_replied_to_bot_message()
        )):
            return False

        return True

    def vk_is_invite(self) -> bool:
        if not self.is_from_vk:
            return False

        if self.vk.action is None:
            return False

        return (
            self.vk.action.member_id == -defs.vk_bot_info.id
            and self.vk.action.type.value == MessagesMessageActionStatus.CHAT_INVITE_USER.value
        )

    def vk_did_user_mention_bot(self) -> bool:
        """
        ## @<bot id> <message>
        ### `@<bot id>` is a mention
        """
        if not self.is_from_vk:
            return False

        return self.vk.is_mentioned

    def vk_is_for_bot(self) -> bool:
        if not self.is_from_vk:
            return False

        event = self.vk
        is_group_chat = event.peer_id != event.from_id
        bot_id = defs.vk_bot_info.id

        if not self.vk_is_invite() and (is_group_chat and not (
            self.vk_did_user_mention_bot()
        )):
            return False

        return True

    def is_for_bot(self) -> bool:
        if self.is_from_vk:
            return self.vk_is_for_bot()
        if self.is_from_tg:
            return self.tg_is_for_bot()

        return False

    def did_user_mentioned_bot(self) -> bool:
        if self.is_from_vk:
            return self.vk_did_user_mention_bot()
        if self.is_from_tg:
            return self.tg_did_user_mentioned_bot() or self.tg_did_user_used_bot_command()

    async def sender_name(self) -> tuple[Optional[str], Optional[str], str]:
        if self.is_from_vk:
            return await vk.name_from_message(self.vk)
        if self.is_from_tg:
            return tg.name_from_message(self.tg)
        if self.is_from_tg_edited_message:
            return tg.name_from_message(self.tg_edited_message)
        if self.is_from_tg_channel_post:
            return tg.name_from_message(self.tg_channel_post)
        if self.is_from_tg_edited_channel_post:
            return tg.name_from_message(self.tg_edited_channel_post)

    async def vk_has_admin_rights(self) -> bool:
        if not self.is_from_vk:
            return False

        return await vk.has_admin_rights(self.vk.peer_id)

    async def can_pin(self) -> bool:
        if not self.is_group_chat:
            return False

        if self.is_from_vk:
            return await self.vk_has_admin_rights()
        if self.is_from_tg:
            bot = await defs.tg_bot.get_chat_member(
                chat_id = self.chat_id,
                user_id = defs.tg_bot_info.id
            )

            return bot.can_pin_messages

    async def answer(
        self,
        text: str,
        keyboard: Optional[kb.Keyboard] = None,
        add_tree: bool = False,
        tree_values: Optional[Values] = None,
        set_as_last: bool = True
    ):
        base_lvl = 1

        if Space.INIT in self.ctx.navigator.spaces:
            base_lvl = 2

        text = self.preprocess_text(
            text=text,
            add_tree=add_tree,
            tree_values=tree_values,
            base_lvl=base_lvl,
            everything=CommonEverything.from_message(self)
        )

        if self.is_from_vk:
            vk_message = self.vk

            result = await vk.chunked_send(
                peer_id=vk_message.peer_id,
                message=text,
                keyboard=keyboard.to_vk().get_json() if keyboard else None,
                dont_parse_links=True,
            )

            chat_id = result[-1].peer_id
            id = result[-1].conversation_message_id
            was_split = len(result) > 1

        elif self.is_from_tg:
            tg_message = self.tg

            result = await tg.chunked_send(
                chat_id=tg_message.chat.id,
                text=text,
                reply_markup=keyboard.to_tg() if keyboard else None,
            )

            chat_id = result[-1].chat.id
            id = result[-1].message_id
            was_split = len(result) > 1

        bot_message = CommonBotMessage(
            src=self.src,
            chat_id=chat_id,
            id=id,
            was_split=was_split,
            text=text,
            keyboard=keyboard,
            add_tree=add_tree,
            tree_values=tree_values
        )

        if set_as_last:
            await self.ctx.set_last_bot_message(bot_message)

class CommonBotMessage(BaseModel):
    """
    ## Already sent message
    - unlike `CommonBotTemplate`, this message
    WAS sent, so we know its `id` and `chat_id`
    - used to determine if user clicked
    a button in an old message and, if so,
    resend THIS instance
    """

    text: str
    keyboard: Optional[kb.Keyboard] = None

    can_edit: bool = True

    add_tree: bool = False
    """ ## If we should add tree of states on top of text """
    tree_values: Optional[Values] = None
    """ ## Optional values to write at the right of each state """

    src: Optional[MESSENGER_OR_EVT_SOURCE] = None
    """ ## For which messenger this message is """
    chat_id: Optional[int] = None
    """ ## For which chat this message is """
    id: Optional[int] = None
    """ ## ID of this exact message """
    reply_to: Optional[int] = None
    was_split: Optional[bool] = None
    timestamp: Optional[float] = None

    @property
    def is_from_vk(self):
        return self.src == Source.VK

    @property
    def is_from_tg(self):
        return self.src == Source.TG

    async def send(self) -> CommonBotMessage:
        if self.is_from_vk:
            results = await vk.chunked_send(
                peer_id=self.chat_id,
                message=self.text,
                keyboard=self.keyboard.to_vk().get_json(),
                reply_to=self.reply_to,
                dont_parse_links=True,
            )

            sent_message: MessagesSendUserIdsResponseItem = results[-1]

            chat_id = sent_message.peer_id
            id = sent_message.conversation_message_id

        elif self.is_from_tg:
            result = await tg.chunked_send(
                chat_id=self.chat_id,
                text=self.text,
                reply_markup=self.keyboard.to_tg(),
                reply_to_message_id=self.reply_to,
                disable_web_page_preview=True,
            )

            last_message = result[-1]

            chat_id = last_message.chat.id
            id = last_message.message_id

        # copy this instance
        bot_message = deepcopy(self)

        # change a few fields in this copy
        bot_message.chat_id = chat_id
        bot_message.id = id
        bot_message.timestamp = time.time()

        return bot_message

    async def pin(self):
        if self.is_from_vk:
            await defs.vk_bot.api.messages.pin(
                peer_id=self.chat_id,
                conversation_message_id=self.id
            )

        elif self.is_from_tg:
            await defs.tg_bot.pin_chat_message(
                chat_id=self.chat_id,
                message_id=self.id
            )

    async def safe_pin(self):
        try:
            await self.pin()
        except Exception as e:
            logger.warning(
                f"unable to pin {self.src} message {self.id} "
                f"for {self.chat_id}: {e}"
            )

    def __str__(self) -> str:
        # all fields of this class as string
        attrs: list[str] = []

        for (name, value) in self.__dict__.items():

            repr_name = name
            repr_value = value

            # if this attribute is "text"
            if name == "text":
                # don't display its value,
                # 'cause otherwise it leads
                # to recursion and each time
                # the message gets bigger
                repr_value = "..."

            # format attribute name and its value, append it
            attrs.append(f"{repr_name}={repr_value}")

        attrs_str = ""
        # join all attributes to one text
        attrs_str = "\n".join(attrs)

        return attrs_str

class CommonEvent(BaseCommonEvent):
    vk: Optional[RawEvent] = None
    """ ## Info about received VK callback button click """
    tg: Optional[CallbackQuery] = None
    """ ## Info about received Telegram callback button click """
    tg_my_chat_member: Optional[ChatMemberUpdated] = None
    """ ## Info about a chat member whose rights were updated """

    force_send: Optional[bool] = None
    """ ## Even if we can edit the message, we may want to send a new one instead """
    dt: Optional[datetime.datetime] = None
    """ ## When the event was received """


    @classmethod
    def from_vk(cls: type[CommonEvent], event: RawEvent, dt: datetime.datetime):
        event_object = event["object"]
        peer_id = event_object["peer_id"]

        self = cls(
            src=Source.VK,
            chat_id=peer_id,
            vk=event,
            force_send=False,
            dt=dt
        )

        return self

    @classmethod
    def from_tg(cls: type[CommonEvent], callback_query: CallbackQuery, dt: datetime.datetime):
        self = cls(
            src=Source.TG,
            chat_id=callback_query.message.chat.id,
            tg=callback_query,
            force_send=False,
            dt=dt
        )

        return self

    @classmethod
    def from_tg_my_chat_member(cls, upd: ChatMemberUpdated, dt: datetime.datetime):
        self = cls(
            src=Source.TG_MY_CHAT_MEMBER,
            chat_id=upd.chat.id,
            tg_my_chat_member=upd,
            dt=dt
        )

        return self

    @property
    def from_message_id(self):
        if self.is_from_vk:
            return self.vk["object"]["conversation_message_id"]
        if self.is_from_tg:
            return self.tg.message.message_id

    @property
    def is_from_last_message(self) -> bool:
        return self.ctx.last_bot_message.id == self.from_message_id

    def is_for_bot(self) -> bool:
        return self.src != Source.TG_MY_CHAT_MEMBER

    @property
    def payload(self) -> str:
        if self.is_from_tg:
            return self.tg.data
        if self.is_from_vk:
            payload_dict = self.vk["object"]["payload"]

            for (key, value) in payload_dict.items():
                return value

    @property
    def is_group_chat(self):
        if self.is_from_vk:
            peer_id = self.vk["object"]["peer_id"]
            from_id = self.vk["object"]["user_id"]
            return vk.is_group_chat(peer_id, from_id)
        if self.is_from_tg:
            return tg.is_group_chat(self.tg.message.chat.type)

    @property
    def is_tg_supergroup(self):
        if not self.is_from_tg:
            return False

        return self.tg.message.chat.type == tg.ChatType.SUPERGROUP

    @property
    def is_tg_group(self):
        if not self.is_from_tg:
            return False

        return self.tg.message.chat.type == tg.ChatType.GROUP

    @property
    def is_vk_group(self):
        if not self.is_from_vk:
            return False

        return self.is_group_chat and self.is_from_vk

    @property
    def needs_mention(self) -> bool:
        return self.is_group_chat and self.is_from_vk

    @property
    def needs_reply(self) -> bool:
        return self.is_group_chat and self.is_from_tg

    @property
    def message_id(self):
        if self.is_from_vk:
            return self.vk["object"]["conversation_message_id"]
        if self.is_from_tg:
            return self.tg.message.message_id

    @property
    def corresponding(self) -> Any:
        if self.is_from_vk:
            return self.vk
        if self.is_from_tg:
            return self.tg

    async def sender_name(self) -> tuple[Optional[str], Optional[str], str]:
        if self.is_from_vk:
            return await vk.name_from_raw(self.vk)
        if self.is_from_tg:
            return tg.name_from_callback(self.tg)

    async def vk_has_admin_rights(self) -> bool:
        if not self.is_from_vk:
            return False

        return await vk.has_admin_rights(self.vk["object"]["peer_id"])

    async def can_pin(self) -> bool:
        if not self.is_group_chat:
            return False

        if self.is_from_vk:
            return await self.vk_has_admin_rights()

        if self.is_from_tg:
            bot = await defs.tg_bot.get_chat_member(
                chat_id=self.chat_id,
                user_id=defs.tg_bot_info.id
            )

            return bot.can_pin_messages

    async def show_notification(
        self,
        text: str
    ):
        try:
            if self.is_from_vk:
                await defs.vk_bot.api.messages.send_message_event_answer(
                    event_id=self.vk["object"]["event_id"],
                    user_id=self.vk["object"]["user_id"],
                    peer_id=self.vk["object"]["peer_id"],
                    event_data=ShowSnackbarEvent(text=text)
                )
            elif self.is_from_tg:
                await self.tg.answer(
                    text=text,
                    show_alert=True
                )
        except:
            ...

    async def pong(self):
        if self.is_from_vk:
            await defs.vk_bot.api.messages.send_message_event_answer(
                event_id=self.vk["object"]["event_id"],
                user_id=self.vk["object"]["user_id"],
                peer_id=self.vk["object"]["peer_id"]
            )
        if self.is_from_tg:
            await self.tg.answer()

    async def edit_message(
        self,
        text: str,
        keyboard: Optional[kb.Keyboard] = None,
        add_tree: bool = False,
        tree_values: Optional[Values] = None
    ):
        """
        ## Edit message by id inside event
        """

        base_lvl = 1

        if Space.INIT in self.ctx.navigator.spaces:
            base_lvl = 2

        text = self.preprocess_text(
            text=text,
            add_tree=add_tree,
            tree_values=tree_values,
            base_lvl=base_lvl,
            everything=CommonEverything.from_event(self)
        )

        was_split = False
        was_sent_instead = False

        if self.is_from_vk:
            chat_id = self.vk["object"]["peer_id"]
            message_id = self.vk["object"]["conversation_message_id"]

            async def send():
                nonlocal was_sent_instead
                nonlocal message_id
                nonlocal was_split

                was_sent_instead = True

                result = await vk.chunked_send(
                    peer_id=chat_id,
                    message=text,
                    keyboard=keyboard.to_vk().get_json() if keyboard else None,
                    dont_parse_links=True,
                )

                message_id = result[-1].conversation_message_id
                was_split = len(result) > 1

            if (
                self.force_send
                or (self.is_from_last_message and self.ctx.last_bot_message.was_split)
            ):
                await send()
            else:
                try:
                    result = await vk.chunked_edit(
                        peer_id=chat_id,
                        conversation_message_id=message_id,
                        message=text,
                        keyboard=keyboard.to_vk().get_json() if keyboard else None,
                        dont_parse_links=True,
                    )

                    if len(result[1]) > 0:
                        message_id = result[1][-1].conversation_message_id
                        was_split = True

                except VKAPIError[909]:
                    await send()

        elif self.is_from_tg:
            chat_id = self.tg.message.chat.id
            message_id = self.tg.message.message_id

            if self.force_send or (
                self.is_from_last_message
                and self.ctx.last_bot_message.was_split
            ):
                was_sent_instead = True

                result = await tg.chunked_send(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard.to_tg() if keyboard else None
                )

                message_id = result[-1].message_id
                was_split = len(result) > 1
            else:
                try:
                    result = await tg.chunked_edit(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=text,
                        reply_markup=keyboard.to_tg() if keyboard else None,
                    )
                    
                    if len(result[1]) > 0:
                        message_id = result[1][-1].message_id
                        was_split = True
                except TelegramBadRequest as e:
                    if "exactly the same" in e.message:
                        await self.tg.answer()
                    else: raise e

        if was_sent_instead:
            await self.show_notification(
                messages.format_sent_as_new_message()
            )

        bot_message = CommonBotMessage(
            src=self.src,
            chat_id=chat_id,
            id=message_id,
            was_split=was_split,
            text=text,
            keyboard=keyboard,
            add_tree=add_tree,
            tree_values=tree_values
        )

        await self.ctx.set_last_bot_message(bot_message)

    async def send_message(
        self,
        text: str,
        keyboard: Optional[kb.Keyboard] = None,
        add_tree: bool = False,
        tree_values: Optional[Values] = None,
        set_as_last: bool = True
    ):
        """
        ## Send message by id inside event
        """

        base_lvl = 1

        if Space.INIT in self.ctx.navigator.spaces:
            base_lvl = 2

        text = self.preprocess_text(
            text=text,
            add_tree=add_tree,
            tree_values=tree_values,
            base_lvl=base_lvl,
            everything=CommonEverything.from_event(self)
        )

        was_split = False

        if self.is_from_vk:
            chat_id = self.vk["object"]["peer_id"]
            message_id = self.vk["object"]["conversation_message_id"]

            result = await vk.chunked_send(
                peer_id=chat_id,
                message=text,
                keyboard=keyboard.to_vk().get_json() if keyboard else None,
                dont_parse_links=True,
            )

            message_id = result[-1].conversation_message_id
            was_split = len(result) > 1

        elif self.is_from_tg:
            chat_id = self.tg.message.chat.id
            message_id = self.tg.message.message_id

            result = await tg.chunked_send(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard.to_tg() if keyboard else None
            )

            message_id = result[-1].message_id
            was_split = len(result) > 1

        bot_message = CommonBotMessage(
            src=self.src,
            chat_id=chat_id,
            id=message_id,
            was_split=was_split,
            text=text,
            keyboard=keyboard,
            add_tree=add_tree,
            tree_values=tree_values
        )

        if set_as_last:
            await self.ctx.set_last_bot_message(bot_message)

class CommonEverything(BaseCommonEvent):
    """
    ## Stores only one type of event inside
    - in example, if we received a new incoming
    message, we'll pass it to `message` field,
    leaving others as `None`
    """
    event_src: Optional[EVENT_SOURCE] = None
    """ ## Point what to look for: `message` or `event` """

    message: Optional[CommonMessage] = None
    """ ## Info about received message """
    event: Optional[CommonEvent] = None
    """ ## Info about received callback button press """

    force_send: Optional[bool] = None
    """ ## Even if we can edit the message, we may want to send a new one instead """

    @classmethod
    def from_message(cls: type[CommonEverything], message: CommonMessage):
        self = cls(
            src=message.src,
            chat_id=message.chat_id,
            event_src=Source.MESSAGE,
            message=message,
            hidden_vars=False
        )

        return self

    @classmethod
    def from_event(cls: type[CommonEverything], event: CommonEvent):
        self = cls(
            src=event.src,
            chat_id=event.chat_id,
            event_src=Source.EVENT,
            event=event,
            hidden_vars=False
        )

        return self

    @property
    def __hidden_vars__(self) -> dict[str, Any]:
        if self.is_from_event:
            return self.event.__hidden_vars__
        if self.is_from_message:
            return self.message.__hidden_vars__

    def set_hidden_vars(self, value: dict[str, Any]):
        if self.is_from_event:
            self.event.set_hidden_vars(value)
        elif self.is_from_message:
            self.message.set_hidden_vars(value)

    @property
    def is_from_message(self) -> bool:
        return self.event_src == Source.MESSAGE

    @property
    def is_from_event(self) -> bool:
        return self.event_src == Source.EVENT

    @property
    def is_group_chat(self) -> bool:
        if self.is_from_event:
            return self.event.is_group_chat
        if self.is_from_message:
            return self.message.is_group_chat

    @property
    def is_tg_supergroup(self) -> bool:
        if self.is_from_event:
            return self.event.is_tg_supergroup
        if self.is_from_message:
            return self.message.is_tg_supergroup

    @property
    def is_tg_group(self) -> bool:
        if self.is_from_event:
            return self.event.is_tg_group
        if self.is_from_message:
            return self.message.is_tg_group

    @property
    def is_vk_group(self) -> bool:
        if self.is_from_event:
            return self.event.is_vk_group
        if self.is_from_message:
            return self.message.is_tg_group

    @property
    def navigator(self) -> Navigator:
        if self.is_from_message:
            return self.message.navigator
        if self.is_from_event:
            return self.event.navigator

    @property
    def ctx(self) -> BaseCtx:
        if self.is_from_event:
            return self.event.ctx
        if self.is_from_message:
            return self.message.ctx

    def set_ctx(self, value: Any):
        if self.is_from_event:
            self.event.set_ctx(value)
        elif self.is_from_message:
            self.message.set_ctx(value)

    def del_ctx(self):
        if self.is_from_event:
            self.event.del_ctx()
        elif self.is_from_message:
            self.message.del_ctx()

    def del_hidden_vars(self):
        if self.is_from_event:
            self.event.del_hidden_vars()
        elif self.is_from_message:
            self.message.del_hidden_vars()

    def take_hidden_vars(self) -> dict[str, Any]:
        if self.is_from_event:
            return self.event.take_hidden_vars()
        if self.is_from_message:
            return self.message.take_hidden_vars()

    async def load_ctx(self) -> BaseCtx:
        if self.is_from_event:
            return await self.event.load_ctx()
        elif self.is_from_message:
            return await self.message.load_ctx()

    @property
    def was_processed(self) -> bool:
        if self.is_from_event:
            return self.event.was_processed
        if self.is_from_message:
            return self.message.was_processed

    def set_was_processed(self, value: bool):
        if self.is_from_event:
            self.event.set_was_processed(value)
        elif self.is_from_message:
            self.message.set_was_processed(value)

    @property
    def corresponding(self) -> Any:
        if self.is_from_event:
            return self.event.corresponding
        if self.is_from_message:
            return self.message.corresponding

    def is_for_bot(self) -> bool:
        if self.is_from_event:
            return self.event.is_for_bot()
        if self.is_from_message:
            return self.message.is_for_bot()

    def did_user_mentioned_bot(self) -> bool:
        if self.is_from_event:
            return True
        if self.is_from_message:
            return self.message.did_user_mentioned_bot()

    async def sender_name(self) -> tuple[Optional[str], Optional[str], str]:
        if self.is_from_event:
            return await self.event.sender_name()
        if self.is_from_message:
            return await self.message.sender_name()

    async def vk_has_admin_rights(self) -> bool:
        if self.is_from_event:
            return await self.event.vk_has_admin_rights()
        if self.is_from_message:
            return await self.message.vk_has_admin_rights()

    async def can_pin(self) -> bool:
        if self.is_from_event:
            return await self.event.can_pin()
        if self.is_from_message:
            return await self.message.can_pin()

    async def edit_or_answer(
        self,
        text: str,
        keyboard: Optional[kb.Keyboard] = None,
        add_tree: bool = False,
        tree_values: Optional[Values] = None
    ):
        """
        If we have received a `message`, we SEND our response (answer).
        
        If we have received an `event`, we EDIT the message with our response.
        """
        event = self.event
        if event is not None:
            event.force_send = self.force_send
        message = self.message

        edit = False
        send = False
        notify_about_resending = False

        if (
            self.is_from_event and
            self.ctx.last_bot_message and
            self.ctx.last_bot_message.can_edit
        ):
            edit = True
        elif (
            self.is_from_event and
            (not self.ctx.last_bot_message or not self.ctx.last_bot_message.can_edit)
        ):
            send = True
            notify_about_resending = True
        else:
            send = True

        if edit:
            return await event.edit_message(
                text=text,
                keyboard=keyboard,
                add_tree=add_tree,
                tree_values=tree_values
            )
        elif send:
            if notify_about_resending:
                await self.event.show_notification(
                    messages.format_sent_as_new_message()
                )

            if message is not None:
                return await message.answer(
                    text=text,
                    keyboard=keyboard,
                    add_tree=add_tree,
                    tree_values=tree_values
                )
            else:
                return await event.send_message(
                    text=text,
                    keyboard=keyboard,
                    add_tree=add_tree,
                    tree_values=tree_values
                )

    async def answer(
        self,
        text: str,
        keyboard: Optional[kb.Keyboard] = None,
        add_tree: bool = False,
        tree_values: Optional[Values] = None,
        set_as_last: bool = True
    ):
        if self.is_from_event:
            event = self.event

            return await event.send_message(
                text=text,
                keyboard=keyboard,
                add_tree=add_tree,
                tree_values=tree_values,
                set_as_last=set_as_last
            )

        if self.is_from_message:
            message = self.message

            return await message.answer(
                text=text,
                keyboard=keyboard,
                add_tree=add_tree,
                tree_values=tree_values,
                set_as_last=set_as_last
            )

    async def send_message(
        self,
        text: str,
        keyboard: Optional[kb.Keyboard] = None,
        chunker: Callable[[str, Optional[int]], list[str]] = text.chunks
    ):
        if self.is_from_vk:
            result = await vk.chunked_send(
                peer_id=self.chat_id,
                message=text,
                keyboard=keyboard.to_vk().get_json() if keyboard else None,
                chunker=chunker
            )
        
            chat_id = result[-1].peer_id
            id = result[-1].conversation_message_id
            was_split = len(result) > 1
        if self.is_from_tg:
            result = await tg.chunked_send(
                chat_id=self.chat_id,
                text=text,
                reply_markup=keyboard.to_tg() if keyboard else None,
                chunker=chunker
            )

            chat_id = result[-1].chat.id
            id = result[-1].message_id
            was_split = len(result) > 1

        bot_message = CommonBotMessage(
            src=self.src,
            chat_id=chat_id,
            id=id,
            was_split=was_split,
            text=text,
            keyboard=keyboard,
            add_tree=False,
            tree_values=None
        )
        
        return bot_message

def run_forever():
    """
    ## Run all services
    """
    from src import defs

    loop = defs.loop

    vk = defs.vk_bot
    tg = defs.tg_dispatch
    tg_bot = defs.tg_bot

    async def tg_start_polling():
        while True:
            try:
                await tg.start_polling(tg_bot)
            except TelegramRetryAfter as e:
                logger.warning(f"CAUGHT TELEGRAM RETRY AFTER {e.retry_after}")
                await asyncio.sleep(e.retry_after)
            except Exception as e:
                logger.warning(f"CAUGHT TELEGRAM POLLING ERROR {e}")
                await asyncio.sleep(1)

            logger.info("starting tg polling again")

    async def vk_run_polling():
        while True:
            try:
                await vk.run_polling()
            except Exception as e:
                logger.warning(f"CAUGHT VK POLLING ERROR: {e}")
                await asyncio.sleep(1)

            logger.info("starting vk polling again")
    
    if defs.vk_bot:
        defs.create_task(vk_run_polling())
    if defs.tg_dispatch:
        defs.create_task(tg_start_polling())

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("shutdown, closing log file")
        defs.log_file.close()
