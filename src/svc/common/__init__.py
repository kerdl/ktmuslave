from __future__ import annotations
from loguru import logger
import time
import asyncio
import random
from typing import Any, Literal, Optional, Callable
from copy import deepcopy
from dataclasses import dataclass
from vkbottle import ShowSnackbarEvent
from vkbottle.bot import Message as VkMessage
from vkbottle_types.responses.messages import MessagesSendUserIdsResponseItem
from aiogram.types import Chat as TgChat, Message as TgMessage, CallbackQuery

from src import defs
from src.svc import vk, telegram as tg
from src import text
from src.svc.common.states import formatter as states_fmt, Values
from src.svc.common.states.tree import Hub
from src.svc.common.navigator import Navigator
from src.svc.common import pagination, messages, error
from src.svc.vk.types import RawEvent
from src.svc.common import keyboard as kb
from src.data import zoom
from src.data.schedule import Schedule, format as sc_format, Type, TYPE_LITERAL
from src.data.settings import Settings, Group
from src.api.schedule import Notify
from .states.tree import Init, Hub, Space


@dataclass
class BroadcastGroup:
    name: str
    header: str
    sc_type: TYPE_LITERAL


@dataclass
class BaseCtx:
    is_registered: bool

    navigator: Navigator
    """ # `Back`, `next` buttons tracer """
    settings: Settings
    """ # Storage for settings and zoom data """
    schedule: Schedule
    """ # Schedule data """
    
    last_call: float
    """
    # Last UNIX time when user interacted with bot

    ## Used
    - to throttle users who
    click buttons too fast
    """

    pages: pagination.Container
    """
    # Page storage for big data

    ## Used
    - to store generated pages
    for massive data that can't
    fit in one message (like zoom entries)
    """
    last_everything: Optional[CommonEverything]
    """
    # Last received event

    ## Used
    - for `navigator`, that passes `everything`
    to `on_enter`, `on_exit` methods of states
    """
    last_bot_message: Optional[CommonBotMessage]
    """
    # Last message sent by the bot

    ## Used
    - to resend it when for some reason
    user interacts with OLD messages
    """

    def register(self) -> None:
        self.is_registered = True

    async def throttle(self) -> None:
        """ ## Stop executing for a short period to avoid rate limit """

        current_time = time.time()

        # allowed to call again after 2 seconds
        next_allowed_time = self.last_call + 2

        if next_allowed_time > current_time:
            # then throttle
            logger.warning("TROLLING")
            sleep_secs_until_allowed: float = next_allowed_time - current_time

            await asyncio.sleep(sleep_secs_until_allowed)

        self.last_call = current_time
    
    def set_everything(self, everything: CommonEverything) -> None:
        self.last_everything = everything
        self.navigator.everything = everything

@dataclass
class VkCtx(BaseCtx):
    """ ## Context specific to VK """
    peer_id: int

@dataclass
class TgCtx(BaseCtx):
    """ ## Context specific to Telegram """
    chat: TgChat

@dataclass
class Ctx:
    """ ## Global context storage"""
    vk: dict[int, VkCtx]
    """
    ## VK chats
    - stored in a dict of `{peer_id: ctx}`
    """
    tg: dict[int, TgCtx]
    """
    ## Telegram chats
    - stored in a dict of `{chat_id: ctx}`
    """

    def add_vk(self, peer_id: int) -> VkCtx:
        navigator = Navigator.default()
        settings = Settings.default()
        schedule = Schedule.default()
        pages = pagination.Container.default()

        self.vk[peer_id] = VkCtx(
            is_registered    = False,
            navigator        = navigator, 
            settings         = settings, 
            schedule         = schedule,
            last_call        = time.time(),
            pages            = pages,
            last_everything  = None,
            last_bot_message = None,
            peer_id          = peer_id
        )

        logger.info("created ctx for vk {}", peer_id)

        return self.vk[peer_id]

    def add_tg(self, chat: TgChat) -> TgCtx:
        navigator = Navigator.default()
        settings = Settings.default()
        schedule = Schedule.default()
        pages = pagination.Container.default()

        self.tg[chat.id] = TgCtx(
            is_registered    = False,
            navigator        = navigator, 
            settings         = settings, 
            schedule         = schedule,
            last_call        = time.time(),
            pages            = pages,
            last_everything  = None,
            last_bot_message = None,
            chat             = chat
        )

        logger.info("created ctx for tg {}", chat.id)

        return self.tg[chat.id]

    async def broadcast_mappings(self, mappings: list[BroadcastGroup]):
        from src.api.schedule import SCHEDULE_API

        groups = [group.name for group in mappings]

        CTX_TYPES = {
            Source.VK: self.vk,
            Source.TG: self.tg
        }

        for (src, storage) in CTX_TYPES.items():
            storage: dict[int, BaseCtx]

            for (chat_id, ctx) in storage.items():
                user_group = ctx.settings.group.confirmed
                should_broadcast = ctx.settings.broadcast

                if user_group not in groups:
                    continue

                if not should_broadcast:
                    continue

                mappings_to_send = [
                    mapping for mapping in mappings if mapping.name == user_group
                ]
                
                for mapping in mappings_to_send:
                    if mapping.sc_type == Type.DAILY:
                        page = await SCHEDULE_API.cached_daily()

                    elif mapping.sc_type == Type.WEEKLY:
                        page = await SCHEDULE_API.cached_weekly()

                    fmt_schedule: str = sc_format.group(
                        page.get_group(mapping.name),
                        ctx.settings.zoom.entries.set
                    )

                    whole_text = f"{mapping.header}\n\n{fmt_schedule}"

                    message = CommonBotMessage(
                        can_edit = False,
                        text     = whole_text,
                        keyboard = kb.Keyboard([
                            [kb.UPDATE_BUTTON],
                            [kb.SETTINGS_BUTTON]
                        ], add_back = False),
                        src      = src,
                        chat_id  = chat_id
                    )

                    ctx.navigator.jump_back_to_or_append(Hub.I_MAIN)

                    ctx.last_bot_message = await message.send()

    async def broadcast(self, notify: Notify):
        from src.data.schedule.compare import GroupCompare, ChangeType

        TYPES = {
            Type.WEEKLY: notify.weekly,
            Type.DAILY:  notify.daily
        }

        mappings: list[BroadcastGroup] = []

        for (sc_type, page_compare) in TYPES.items():
            if sc_type == Type.WEEKLY:
                repr_type = "недельном"
            elif sc_type == Type.DAILY:
                repr_type = "дневном"

            CHANGE_TYPES = {
                ChangeType.APPEARED: page_compare.groups.appeared if page_compare else None,
                ChangeType.CHANGED:  page_compare.groups.changed if page_compare else None
            }

            for (change, groups) in CHANGE_TYPES.items():
                if groups is None:
                    continue

                if change == ChangeType.APPEARED:
                    groups: list[Group]
                    repr_change = "появилась"

                elif change == ChangeType.CHANGED:
                    groups: list[GroupCompare]
                    repr_change = "изменилась"
                    
                header = f"Группа {repr_change} в {repr_type}"

                for group in groups:
                    name = group.repr_name
                    
                    if change == ChangeType.APPEARED:
                        fmt_changes = None
                    elif change == ChangeType.CHANGED:
                        fmt_changes = sc_format.notify(group)

                    if fmt_changes is not None:
                        header += "\n\n"
                        header += fmt_changes

                    mappings.append(BroadcastGroup(name, header, sc_type))
        
        await self.broadcast_mappings(mappings)


ctx = Ctx({}, {})

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
EVENT_SOURCE = Literal["message", "event"]


@dataclass
class BaseCommonEvent:
    src: Optional[MESSENGER_SOURCE] = None
    chat_id: Optional[int] = None

    @property
    def is_from_vk(self):
        return self.src == Source.VK

    @property
    def is_from_tg(self):
        return self.src == Source.TG
    
    @property
    def vk_ctx(self) -> VkCtx:
        return ctx.vk.get(self.chat_id)
    
    @property
    def tg_ctx(self) -> TgCtx:
        return ctx.tg.get(self.chat_id)

    @property
    def ctx(self) -> BaseCtx:
        if self.is_from_vk:
            return self.vk_ctx
        if self.is_from_tg:
            return self.tg_ctx
    
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


@dataclass
class CommonMessage(BaseCommonEvent):
    """
    ## Container for only one source of recieved event
    - in example, if we recieved a message from VK,
    we'll pass it to `vk` field, leaving others as `None`
    """
    vk: Optional[VkMessage] = None
    """ ## Info about recieved VK message """
    tg: Optional[TgMessage] = None
    """ ## Info about recieved Telegram message """


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

@dataclass
class CommonBotTemplate:
    """
    ## Container of message to send later
    - unlike `CommonBotMessage`, this may not
    be already sent, it's just a template
    - used to construct pages from massive data
    """
    text: str
    keyboard: kb.Keyboard

@dataclass
class CommonBotMessage:
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
    was_split: Optional[bool] = None

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

        return bot_message
    
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

@dataclass
class CommonEvent(BaseCommonEvent):
    vk: Optional[RawEvent] = None
    """ ## Info about recieved VK callback button click """
    tg: Optional[CallbackQuery] = None
    """ ## Info about recieved Telegram callback button click """


    @classmethod
    def from_vk(cls, event: RawEvent):
        event_object = event["object"]
        peer_id = event_object["peer_id"]

        self = cls(
            src=Source.VK,
            vk=event,
            chat_id=peer_id
        )

        return self
    
    @classmethod
    def from_tg(cls, callback_query: CallbackQuery):
        self = cls(
            src=Source.TG,
            tg=callback_query,
            chat_id=callback_query.message.chat.id
        )

        return self
    
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

        if self.is_from_vk:
            chat_id = self.vk["object"]["peer_id"]
            message_id = self.vk["object"]["conversation_message_id"]

            if self.ctx.last_bot_message.was_split:
                result = await vk.chunked_send(
                    peer_id          = chat_id,
                    message          = text,
                    keyboard         = keyboard.to_vk().get_json() if keyboard else None,
                    dont_parse_links = True,
                )

                message_id = result[-1].conversation_message_id
                was_split = len(result) > 1

            else:
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
        
        elif self.is_from_tg:
            chat_id = self.tg.message.chat.id
            message_id = self.tg.message.message_id

            if self.ctx.last_bot_message.was_split:
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

@dataclass
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
    """ ## Info about recieved message """
    event: Optional[CommonEvent] = None
    """ ## Info about recieved callback button press """

    @classmethod
    def from_message(cls: type[CommonEverything], message: CommonMessage):
        self = cls(
            src=message.src,
            event_src=Source.MESSAGE,
            message=message,
        )

        return self
    
    @classmethod
    def from_event(cls, event: CommonEvent):
        self = cls(
            src=event.src,
            event_src=Source.EVENT,
            event=event,
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
    def vk_ctx(self) -> VkCtx:
        if self.is_from_message:
            return self.message.vk_ctx
        if self.is_from_event:
            return self.event.vk_ctx
    
    @property
    def tg_ctx(self) -> TgCtx:
        if self.is_from_message:
            return self.message.tg_ctx
        if self.is_from_event:
            return self.event.tg_ctx

    @property
    def ctx(self) -> BaseCtx:
        if self.is_from_vk:
            return self.vk_ctx
        if self.is_from_tg:
            return self.tg_ctx
    
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
        - if we recieved an `event`, we EDIT the message with response
        """

        if self.is_from_event:
            event = self.event

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

def run_forever():
    """
    ## Run all services
    """
    from src import defs

    loop = defs.loop

    vk = defs.vk_bot
    tg = defs.tg_dispatch
    tg_bot = defs.tg_bot

    loop.create_task(tg.start_polling(tg_bot))
    loop.create_task(vk.run_polling())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("keyboard interrupt")
    