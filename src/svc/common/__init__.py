from __future__ import annotations
from loguru import logger
import time
import asyncio
from typing import Literal, Optional, Callable, Any, TypeVar, Generic
from copy import deepcopy
from dataclasses import dataclass, field
from pydantic import BaseModel
from vkbottle import ShowSnackbarEvent, VKAPIError
from vkbottle.bot import Message as VkMessage
from vkbottle_types.responses.messages import MessagesSendUserIdsResponseItem
from vkbottle_types.codegen.objects import MessagesMessageActionStatus
from aiogram.types import Chat as TgChat, Message as TgMessage, CallbackQuery
from aiogram.exceptions import TelegramRetryAfter
import pickle
import aiofiles

from src import defs
from src.svc import vk, telegram as tg
from src import text
from src.svc.common.states import formatter as states_fmt, Values
from src.svc.common.states.tree import HUB
from src.svc.common.navigator import Navigator, DbNavigator
from src.svc.common import pagination, messages
from src.svc.vk.types_ import RawEvent
from src.svc.common import keyboard as kb
from src.data import RepredBaseModel
from src.data.schedule import Schedule, format as sc_format, Type, TYPE_LITERAL
from src.data.settings import Settings
from src.api.schedule import Notify
from .states.tree import Space


class Source:
    """
    ## Different sources of messengers, events
    """
    VK = "vk"
    """ ## Message/event came from VK """
    TG = "tg"
    """ ## Message/event came from Telegram """
    MESSAGE = "message"
    """ ## Event came from incoming message """
    EVENT = "event"
    """ ## Event came from pressing keyboard buttons inside message """

MESSENGER_SOURCE = Literal["vk", "tg"]
MESSENGER_SOURCE_T = TypeVar("MESSENGER_SOURCE_T")
EVENT_SOURCE = Literal["message", "event"]


@dataclass
class BroadcastGroup:
    name: str
    header: str
    sc_type: TYPE_LITERAL

class DbBaseCtx(BaseModel):
    chat_id: int
    is_registered: bool

    navigator: DbNavigator
    settings: Settings
    schedule: Schedule

    pages: pagination.Container

    last_call: float = 0.0
    last_everything: Optional[CommonEverything]
    last_bot_message: Optional[CommonBotMessage]
    last_daily_message: Optional[CommonBotMessage]
    last_weekly_message: Optional[CommonBotMessage]

    @classmethod
    def from_runtime(cls: type[DbBaseCtx], ctx: BaseCtx) -> DbBaseCtx:
        return cls(
            chat_id=ctx.chat_id,
            is_registered=ctx.is_registered,
            navigator=ctx.navigator.to_db(),
            settings=ctx.settings,
            schedule=ctx.schedule,
            pages=ctx.pages,
            last_call=ctx.last_call,
            last_everything=ctx.last_everything,
            last_bot_message=ctx.last_bot_message,
            last_daily_message=ctx.last_daily_message,
            last_weekly_message=ctx.last_weekly_message
        )
    
    def to_runtime(self) -> BaseCtx:
        return BaseCtx.from_db(self)

@dataclass
class BaseCtx:
    chat_id: int
    is_registered: bool = False

    navigator: Navigator = field(default_factory=Navigator)
    """ # `Back`, `next` buttons tracer """
    settings: Settings = field(default_factory=Settings)
    """ # Storage for settings and zoom data """
    schedule: Schedule = field(default_factory=Schedule)
    """ # Schedule data """
    
    last_call: float = 0.0
    """
    # Last UNIX time when user interacted with bot

    ## Used
    - to throttle users who
    click buttons too fast
    """

    pages: pagination.Container = field(default_factory=pagination.Container)
    """
    # Page storage for big data

    ## Used
    - to store generated pages
    for massive data that can't
    fit in one message (like zoom entries)
    """
    last_everything: Optional[CommonEverything] = None
    """
    # Last received event

    ## Used
    - for `navigator`, that passes `everything`
    to `on_enter`, `on_exit` methods of states
    """
    last_bot_message: Optional[CommonBotMessage] = None
    """
    # Last message sent by the bot

    ## Used
    - to resend it when for some reason
    user interacts with OLD messages
    """
    last_daily_message: Optional[CommonBotMessage] = None
    last_weekly_message: Optional[CommonBotMessage] = None


    @classmethod
    def from_db(cls: type[BaseCtx], db: DbBaseCtx) -> BaseCtx:
        return cls(
            chat_id=db.chat_id,
            is_registered=db.is_registered,
            navigator=db.navigator.to_runtime(db.last_everything),
            settings=db.settings,
            schedule=db.schedule,
            last_call=db.last_call,
            pages=db.pages,
            last_everything=db.last_everything,
            last_bot_message=db.last_bot_message,
            last_daily_message=db.last_daily_message,
            last_weekly_message=db.last_weekly_message
        )
    
    def to_db(self) -> DbBaseCtx:
        return DbBaseCtx.from_runtime(self)

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

@dataclass
class DbIterator(Generic[MESSENGER_SOURCE_T]):
    ...


@dataclass
class Ctx:
    """ ## Global context storage"""
    vk: dict[int, BaseCtx]
    """
    ## VK chats
    - stored in a dict of `{peer_id: ctx}`
    """
    tg: dict[int, BaseCtx]
    """
    ## Telegram chats
    - stored in a dict of `{chat_id: ctx}`
    """

    def is_added(self, everything: CommonEverything) -> bool:
        if everything.is_from_vk:
            return everything.chat_id in self.vk.keys()
        if everything.is_from_tg:
            return everything.chat_id in self.tg.keys()
    
    def add_from_everything(self, everything: CommonEverything) -> BaseCtx:
        if everything.is_from_vk:
            ctx = self.add_vk(everything.chat_id)
        elif everything.is_from_tg:
            if everything.is_from_event:
                ctx = self.add_tg(everything.event.tg.message.chat.id)
            elif everything.is_from_message:
                ctx = self.add_tg(everything.message.tg.chat.id)
        
        ctx.set_everything(everything)

        return ctx

    def add_vk(self, peer_id: int) -> BaseCtx:
        self.vk[peer_id] = BaseCtx(
            chat_id=peer_id,
            last_call=time.time(),
        )

        logger.info("created ctx for vk {}", peer_id)

        return self.vk[peer_id]

    def add_tg(self, chat_id: int) -> BaseCtx:
        self.tg[chat_id] = BaseCtx(
            chat_id=chat_id,
            last_call=time.time(),
        )

        logger.info("created ctx for tg {}", chat_id)

        return self.tg[chat_id]

    async def broadcast_mappings(
        self,
        mappings: list[BroadcastGroup],
        invoker: Optional[BaseCtx] = None
    ):
        from src.api.schedule import SCHEDULE_API

        groups = [group.name for group in mappings]

        CTX_TYPES = {
            Source.VK: self.vk,
            Source.TG: self.tg
        }

        for (src, storage) in CTX_TYPES.items():
            storage: dict[int, BaseCtx]

            for (chat_id, ctx) in storage.items():
                if not ctx.is_registered:
                    continue

                user_group = ctx.settings.group.confirmed
                should_broadcast = (
                    ctx.settings.broadcast
                    if invoker is None or ctx.chat_id != invoker.chat_id else True
                )

                if not should_broadcast:
                    continue

                if user_group not in groups:
                    continue

                mappings_to_send = [
                    mapping for mapping in mappings if mapping.name == user_group
                ]
                
                for mapping in mappings_to_send:
                    opposite_type: TYPE_LITERAL
                    no_message_to_reply_to = False
                    reply_to = None

                    if mapping.sc_type == Type.DAILY:
                        opposite_type = Type.WEEKLY
                        page = await SCHEDULE_API.daily()

                        if ctx.last_weekly_message is not None:
                            reply_to = ctx.last_weekly_message.id
                        else:
                            no_message_to_reply_to = True

                    elif mapping.sc_type == Type.WEEKLY:
                        opposite_type = Type.DAILY
                        page = await SCHEDULE_API.weekly()

                        if ctx.last_daily_message is not None:
                            reply_to = ctx.last_daily_message.id
                        else:
                            no_message_to_reply_to = True

                    fmt_schedule: str = await sc_format.group(
                        page.get_group(mapping.name),
                        ctx.settings.zoom.entries.set
                    )

                    reply_hint = messages.format_replied_to_schedule_message(
                        opposite_type
                    )
                    failed_reply_hint = messages.format_failed_reply_to_schedule_message(
                        opposite_type
                    )

                    whole_text_no_reply_hint = (
                        f"{mapping.header}\n\n{fmt_schedule}"
                    )
                    whole_text_with_reply = (
                        f"{reply_hint}\n\n{mapping.header}\n\n{fmt_schedule}"
                    )
                    whole_text_failed_reply = (
                        f"{failed_reply_hint}\n\n{mapping.header}\n\n{fmt_schedule}"
                    )

                    message = CommonBotMessage(
                        can_edit = False,
                        text     = whole_text_with_reply,
                        keyboard = kb.Keyboard([
                            [kb.UPDATE_BUTTON],
                            [kb.RESEND_BUTTON],
                            [kb.SETTINGS_BUTTON],
                            [
                                SCHEDULE_API.ft_daily_url_button(),
                                SCHEDULE_API.ft_weekly_url_button()
                            ],
                            [SCHEDULE_API.r_weekly_url_button()],
                            [kb.MATERIALS_BUTTON, kb.JOURNALS_BUTTON],
                        ], add_back = False),
                        src      = src,
                        chat_id  = chat_id,
                        reply_to = reply_to,
                    )

                    if no_message_to_reply_to:
                        message.text = whole_text_no_reply_hint

                    logger.info(f"broadcasting {mapping.sc_type} to {ctx.chat_id}")

                    try:
                        ctx.last_bot_message = await message.send()
                    except VKAPIError[913]:
                        logger.warning(
                            f"(broadcasting {mapping.sc_type}) "
                            f"{ctx.chat_id} has too many fwd messages, "
                            f"proceeding without forwarding"
                        )

                        message.text = whole_text_failed_reply
                        message.reply_to = None

                        ctx.last_bot_message = await message.send()
                    except Exception as e:
                        logger.error(
                            f"cannot broadcast {mapping.sc_type} to {ctx.chat_id}: {e}"
                        )
                    
                    ctx.navigator.jump_back_to_or_append(HUB.I_MAIN)

                    if mapping.sc_type == Type.DAILY:
                        ctx.last_daily_message = ctx.last_bot_message
                    elif mapping.sc_type == Type.WEEKLY:
                        ctx.last_weekly_message = ctx.last_bot_message

                    if ctx.settings.should_pin:
                        await ctx.last_bot_message.safe_pin()

    async def broadcast(self, notify: Notify, invoker: Optional[BaseCtx] = None):
        from src.data.schedule.compare import ChangeType

        TYPES = {
            Type.WEEKLY: notify.weekly,
            Type.DAILY:  notify.daily
        }

        mappings: list[BroadcastGroup] = []

        for (sc_type, page_compare) in TYPES.items():
            do_detailed_compare = page_compare.date.is_same() if page_compare is not None else False

            CHANGE_TYPES = {
                ChangeType.APPEARED: page_compare.groups.appeared if page_compare else None,
                ChangeType.CHANGED:  page_compare.groups.changed if page_compare else None
            }

            for (change, groups) in CHANGE_TYPES.items():
                groups: list[RepredBaseModel]

                if groups is None:
                    continue

                for group in groups:
                    header = messages.format_group_changed_in_sc_type(
                        change  = change,
                        sc_type = sc_type
                    )

                    name = group.repr_name
                    
                    if change == ChangeType.APPEARED:
                        fmt_changes = sc_format.CompareFormatted(
                            text=None,
                            has_detailed=False
                        )
                    elif change == ChangeType.CHANGED:
                        fmt_changes = sc_format.cmp(
                            group,
                            is_detailed = do_detailed_compare
                        )

                    if fmt_changes.text is not None:
                        header += "\n\n"

                        if fmt_changes.has_detailed and not do_detailed_compare:
                            header += messages.format_detailed_compare_not_shown()
                            header += "\n"

                        header += fmt_changes.text

                    mappings.append(BroadcastGroup(name, header, sc_type))
        
        await self.broadcast_mappings(mappings, invoker)
    
    async def save(self):
        async with aiofiles.open(defs.data_dir.joinpath("ctx.bin"), mode="wb") as f:
            dump = pickle.dumps(self)
            await f.write(dump)
    
    def poll_save(self):
        defs.create_task(self.save())

    async def save_forever(self):
        while True:
            await asyncio.sleep(10 * 60)
            await self.save()

    @classmethod
    def load(cls) -> Ctx:
        path = defs.data_dir.joinpath("ctx.bin")

        with open(path, mode="rb") as f:
            self: Ctx = pickle.load(f)

            for messenger in [self.vk, self.tg]:
                messenger: dict[int, BaseCtx]

                for (id, ctx) in messenger.items():
                    for tchr in ctx.settings.zoom.entries.set:
                        tchr.i_promise_i_will_get_rid_of_this_thing_but_not_now()
                    
                    for tchr in ctx.settings.zoom.new_entries.set:
                        tchr.i_promise_i_will_get_rid_of_this_thing_but_not_now()

            return self

    @classmethod
    def load_or_init(cls: type[Ctx]) -> Ctx:
        path = defs.data_dir.joinpath("ctx.bin")

        if not path.exists():
            self = cls(vk={}, tg={})
            self.poll_save()

            return self
        else:
            return cls.load()


class BaseCommonEvent(BaseModel):
    src: Optional[MESSENGER_SOURCE] = None
    chat_id: Optional[int] = None

    @property
    def is_from_vk(self):
        return self.src == Source.VK

    @property
    def is_from_tg(self):
        return self.src == Source.TG

    @property
    def ctx(self) -> BaseCtx:
        if self.is_from_vk:
            return defs.ctx.vk.get(self.chat_id)
        if self.is_from_tg:
            return defs.ctx.tg.get(self.chat_id)
    
    @property
    def navigator(self) -> Navigator:
        return self.ctx.navigator
    
    def preprocess_text(
        self, 
        text: str, 
        add_tree: bool,
        base_lvl: int = 1,
        tree_values: Values = None
    ) -> str:
        """
        ## Add generic components to `text`
        - wise mystical tree of states on top
        - debug info even higher
        """
        if add_tree:
            text = states_fmt.tree(
                navigator = self.ctx.navigator, 
                values    = tree_values,
                base_lvl  = base_lvl
            ) + "\n\n" + text

        if messages.DEBUGGING:
            text = messages.format_debug(
                trace            = self.ctx.navigator.trace,
                back_trace       = self.ctx.navigator.back_trace,
                last_bot_message = self.ctx.last_bot_message,
                settings         = self.ctx.settings
            ) + "\n\n" + text
        
        return text


class CommonMessage(BaseCommonEvent):
    """
    ## Container for only one source of received event
    - in example, if we received a message from VK,
    we'll pass it to `vk` field, leaving others as `None`
    """
    vk: Optional[VkMessage] = None
    """ ## Info about received VK message """
    tg: Optional[TgMessage] = None
    """ ## Info about received Telegram message """


    @classmethod
    def from_vk(cls: type[CommonMessage], message: VkMessage):
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

    @property
    def is_tg_supergroup(self) -> bool:
        if not self.is_from_tg:
            return False

        return self.tg.chat.type == tg.ChatType.SUPERGROUP
    
    @property
    def is_tg_group(self) -> bool:
        if not self.is_from_tg:
            return False

        return self.tg.chat.type == tg.ChatType.GROUP
    
    @property
    def is_vk_group(self) -> bool:
        if not self.is_from_vk:
            return False
        
        return self.is_group_chat and self.is_from_vk

    @property
    def is_group_chat(self) -> bool:
        if self.is_from_vk:
            return vk.is_group_chat(self.vk.peer_id, self.vk.from_id)
        if self.is_from_tg:
            return tg.is_group_chat(self.tg.chat.type)
    
    @property
    def message_id(self)-> int:
        if self.is_from_vk:
            return self.vk.message_id
        if self.is_from_tg:
            return self.tg.message_id

    @property
    def text(self) -> Optional[str]:
        if self.is_from_vk:
            return self.vk.text
        if self.is_from_tg:
            return self.tg.text

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
    
    def _tg_is_for_bot(self) -> bool:
        if not self.is_from_tg:
            return False

        event = self.tg
        is_group_chat = tg.is_group_chat(event.chat.type)

        def is_invite() -> bool:
            if event.content_type != "new_chat_members":
                return False
            
            for new in event.new_chat_members:
                if new.id == defs.tg_bot_info.id:
                    return True
            
            return False

        def did_user_used_bot_command() -> bool:
            if event.text is None:
                return False
            
            if event.text == "/":
                return False
            elif any(cmd in event.text for cmd in defs.tg_bot_commands):
                return True
            
            return False

        def did_user_mentioned_bot() -> bool:
            if event.entities is None:
                return False

            mentions = tg.extract_mentions(event.entities, event.text)

            # if our bot not in mentions
            if defs.tg_bot_mention not in mentions:
                return False

            return True

        def did_user_replied_to_bot_message() -> bool:
            if event.reply_to_message is None:
                return False

            return event.reply_to_message.from_user.id == defs.tg_bot_info.id

        if not is_invite() and (is_group_chat and not (
            did_user_used_bot_command() or
            did_user_mentioned_bot() or
            did_user_replied_to_bot_message()
        )):
            return False
        
        return True
    
    def _vk_is_for_bot(self) -> bool:
        if not self.is_from_vk:
            return False

        event = self.vk
        is_group_chat = event.peer_id != event.from_id
        bot_id = defs.vk_bot_info.id
        negative_bot_id = -bot_id
        
        def is_invite() -> bool:
            if event.action is None:
                return False

            return (
                event.action.member_id == -defs.vk_bot_info.id
                and event.action.type.value == MessagesMessageActionStatus.CHAT_INVITE_USER.value
            )

        def did_user_mentioned_bot() -> bool:
            """ 
            ## @<bot id> <message> 
            ### `@<bot id>` is a mention
            """
            return event.is_mentioned

        if not is_invite() and (is_group_chat and not (
            did_user_mentioned_bot()
        )):
            return False
        
        return True
    
    def is_for_bot(self) -> bool:
        if self.is_from_vk:
            return self._vk_is_for_bot()
        if self.is_from_tg:
            return self._tg_is_for_bot()

    async def sender_name(self) -> tuple[Optional[str], Optional[str], str]:
        if self.is_from_vk:
            return await vk.name_from_message(self.vk)
        if self.is_from_tg:
            return tg.name_from_message(self.tg)

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
        tree_values: Optional[Values] = None
    ):
        base_lvl = 1

        if Space.INIT in self.ctx.navigator.spaces:
            base_lvl = 2

        text = self.preprocess_text(
            text        = text, 
            add_tree    = add_tree, 
            tree_values = tree_values,
            base_lvl    = base_lvl
        )

        if self.is_from_vk:
            vk_message = self.vk

            result = await vk.chunked_send(
                peer_id          = vk_message.peer_id,
                message          = text,
                keyboard         = keyboard.to_vk().get_json() if keyboard else None,
                dont_parse_links = True,
            )

            chat_id = result[-1].peer_id
            id = result[-1].conversation_message_id
            was_split = len(result) > 1

        elif self.is_from_tg:
            tg_message = self.tg

            result = await tg.chunked_send(
                chat_id      = tg_message.chat.id,
                text         = text,
                reply_markup = keyboard.to_tg() if keyboard else None,
            )

            chat_id = result[-1].chat.id
            id = result[-1].message_id
            was_split = len(result) > 1
        
        bot_message = CommonBotMessage(
            src         = self.src,
            chat_id     = chat_id,
            id          = id,
            was_split   = was_split,
            text        = text,
            keyboard    = keyboard,
            add_tree    = add_tree,
            tree_values = tree_values
        )

        self.ctx.last_bot_message = bot_message

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
    keyboard: kb.Keyboard

    can_edit: bool = True

    add_tree: bool = False
    """ ## If we should add tree of states on top of text """
    tree_values: Optional[Values] = None
    """ ## Optional values to write at the right of each state """

    src: Optional[MESSENGER_SOURCE] = None
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
                peer_id          = self.chat_id,
                message          = self.text,
                keyboard         = self.keyboard.to_vk().get_json(),
                reply_to         = self.reply_to,
                dont_parse_links = True,
            )

            sent_message: MessagesSendUserIdsResponseItem = results[-1]

            chat_id = sent_message.peer_id
            id = sent_message.conversation_message_id

        elif self.is_from_tg:
            result = await tg.chunked_send(
                chat_id                  = self.chat_id,
                text                     = self.text,
                reply_markup             = self.keyboard.to_tg(),
                reply_to_message_id      = self.reply_to,
                disable_web_page_preview = True,
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
                peer_id                 = self.chat_id,
                conversation_message_id = self.id
            )
        
        elif self.is_from_tg:
            await defs.tg_bot.pin_chat_message(
                chat_id    = self.chat_id,
                message_id = self.id
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
                # message gets bigger
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

    force_send: Optional[bool] = None
    """ ## Even if we can edit the message, we may want to send a new one instead """


    @classmethod
    def from_vk(cls: type[CommonEvent], event: RawEvent):
        event_object = event["object"]
        peer_id = event_object["peer_id"]

        self = cls(
            src=Source.VK,
            chat_id=peer_id,
            vk=event,
            force_send=False
        )

        return self
    
    @classmethod
    def from_tg(cls: type[CommonEvent], callback_query: CallbackQuery):
        self = cls(
            src=Source.TG,
            chat_id=callback_query.message.chat.id,
            tg=callback_query,
            force_send=False,
        )

        return self
    
    @property
    def from_message_id(self):
        if self.is_from_vk:
            return self.vk["object"]["conversation_message_id"]
        if self.is_from_tg:
            return self.tg.message.message_id
    
    @property
    def is_from_last_message(self):
        return self.ctx.last_bot_message.id == self.from_message_id
    
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
                chat_id = self.chat_id, 
                user_id = defs.tg_bot_info.id
            )

            return bot.can_pin_messages

    async def show_notification(
        self,
        text: str
    ):
        """
        ## Show little notification on top
        """

        if self.is_from_vk:
            result = await defs.vk_bot.api.messages.send_message_event_answer(
                event_id   = self.vk["object"]["event_id"],
                user_id    = self.vk["object"]["user_id"],
                peer_id    = self.vk["object"]["peer_id"],
                event_data = ShowSnackbarEvent(text=text)
            )
        
        elif self.is_from_tg:
            result = await self.tg.answer(
                text, 
                show_alert=True
            )

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
            text        = text, 
            add_tree    = add_tree, 
            tree_values = tree_values,
            base_lvl    = base_lvl
        )

        was_split = False
        was_sent_instead = False
        sent_more_than_24_hr_ago = (
            self.is_from_last_message and
            self.ctx.last_bot_message.timestamp is not None
            and (self.ctx.last_bot_message.timestamp + 24 * 3600) > time.time()
        ) 

        if self.is_from_vk:
            chat_id = self.vk["object"]["peer_id"]
            message_id = self.vk["object"]["conversation_message_id"]

            async def send():
                nonlocal was_sent_instead
                nonlocal message_id
                nonlocal was_split 

                was_sent_instead = True

                result = await vk.chunked_send(
                    peer_id          = chat_id,
                    message          = text,
                    keyboard         = keyboard.to_vk().get_json() if keyboard else None,
                    dont_parse_links = True,
                )

                message_id = result[-1].conversation_message_id
                was_split = len(result) > 1
            
            if (
                self.force_send
                or sent_more_than_24_hr_ago
                or (self.is_from_last_message and self.ctx.last_bot_message.was_split)
            ):
                await send()
            else:
                try:
                    result = await vk.chunked_edit(
                        peer_id                 = chat_id,
                        conversation_message_id = message_id,
                        message                 = text,
                        keyboard                = keyboard.to_vk().get_json() if keyboard else None,
                        dont_parse_links        = True,
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
                    chat_id = chat_id,
                    text    = text,
                    reply_markup= keyboard.to_tg() if keyboard else None
                )

                message_id = result[-1].message_id
                was_split = len(result) > 1
            else:
                result = await tg.chunked_edit(
                    chat_id      = chat_id,
                    message_id   = message_id,
                    text         = text,
                    reply_markup = keyboard.to_tg() if keyboard else None,
                )

                if len(result[1]) > 0:
                    message_id = result[1][-1].message_id
                    was_split = True

        if was_sent_instead:
            await self.show_notification(
                messages.format_sent_as_new_message()
            )
        
        bot_message = CommonBotMessage(
            src         = self.src,
            chat_id     = chat_id,
            id          = message_id,
            was_split   = was_split,
            text        = text,
            keyboard    = keyboard,
            add_tree    = add_tree,
            tree_values = tree_values
        )

        self.ctx.last_bot_message = bot_message

    async def send_message(
        self,
        text: str, 
        keyboard: Optional[kb.Keyboard] = None,
        add_tree: bool = False,
        tree_values: Optional[Values] = None
    ):
        """
        ## Send message by id inside event
        """

        base_lvl = 1

        if Space.INIT in self.ctx.navigator.spaces:
            base_lvl = 2

        text = self.preprocess_text(
            text        = text, 
            add_tree    = add_tree, 
            tree_values = tree_values,
            base_lvl    = base_lvl
        )

        was_split = False

        if self.is_from_vk:
            chat_id = self.vk["object"]["peer_id"]
            message_id = self.vk["object"]["conversation_message_id"]

            result = await vk.chunked_send(
                peer_id          = chat_id,
                message          = text,
                keyboard         = keyboard.to_vk().get_json() if keyboard else None,
                dont_parse_links = True,
            )

            message_id = result[-1].conversation_message_id
            was_split = len(result) > 1
        
        elif self.is_from_tg:
            chat_id = self.tg.message.chat.id
            message_id = self.tg.message.message_id

            result = await tg.chunked_send(
                chat_id = chat_id,
                text    = text,
                reply_markup= keyboard.to_tg() if keyboard else None
            )

            message_id = result[-1].message_id
            was_split = len(result) > 1

        bot_message = CommonBotMessage(
            src         = self.src,
            chat_id     = chat_id,
            id          = message_id,
            was_split   = was_split,
            text        = text,
            keyboard    = keyboard,
            add_tree    = add_tree,
            tree_values = tree_values
        )

        self.ctx.last_bot_message = bot_message

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
            src       = message.src,
            chat_id   = message.chat_id,
            event_src = Source.MESSAGE,
            message   = message,
        )

        return self
    
    @classmethod
    def from_event(cls: type[CommonEverything], event: CommonEvent):
        self = cls(
            src       = event.src,
            chat_id   = event.chat_id,
            event_src = Source.EVENT,
            event     = event,
        )

        return self

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

    @property
    def corresponding(self) -> Any:
        if self.is_from_event:
            return self.event.corresponding
        if self.is_from_message:
            return self.message.corresponding

    def is_for_bot(self) -> bool:
        if self.is_from_event:
            return True
        if self.is_from_message:
            return self.message.is_for_bot()

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
        - if we received a `message`, we SEND our response `(answer)`
        - if we received an `event`, we EDIT the message with response
        """

        if self.is_from_event:
            event = self.event
            event.force_send = self.force_send

            return await event.edit_message(
                text        = text, 
                keyboard    = keyboard,
                add_tree    = add_tree,
                tree_values = tree_values
            )

        if self.is_from_message:
            message = self.message

            return await message.answer(
                text        = text, 
                keyboard    = keyboard,
                add_tree    = add_tree,
                tree_values = tree_values
            )
    
    async def answer(
        self,
        text: str, 
        keyboard: Optional[kb.Keyboard] = None,
        add_tree: bool = False,
        tree_values: Optional[Values] = None
    ):
        if self.is_from_event:
            event = self.event

            return await event.send_message(
                text        = text, 
                keyboard    = keyboard,
                add_tree    = add_tree,
                tree_values = tree_values
            )

        if self.is_from_message:
            message = self.message

            return await message.answer(
                text        = text, 
                keyboard    = keyboard,
                add_tree    = add_tree,
                tree_values = tree_values
            )
    
    async def send_message(
        self,
        text: str, 
        keyboard: Optional[kb.Keyboard] = None,
        chunker: Callable[[str, Optional[int]], list[str]] = text.chunks
    ):
        if self.is_from_vk:
            return await vk.chunked_send(
                peer_id  = self.chat_id,
                message  = text,
                keyboard = keyboard,
                chunker  = chunker
            )
        if self.is_from_tg:
            return await tg.chunked_send(
                chat_id      = self.chat_id,
                text         = text,
                reply_markup = keyboard,
                chunker      = chunker
            )

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

    defs.create_task(tg_start_polling())
    defs.create_task(vk_run_polling())

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("shutdown, saving ctx and closing log file")

        loop.run_until_complete(defs.ctx.save())
        defs.log_file.close()
    
