from __future__ import annotations
from loguru import logger
import time
import asyncio
import random
from typing import Any, Literal, Optional
from copy import deepcopy
from dataclasses import dataclass
from vkbottle import ShowSnackbarEvent
from vkbottle.bot import Message as VkMessage
from vkbottle_types.responses.messages import MessagesSendUserIdsResponseItem
from aiogram.types import Chat as TgChat, Message as TgMessage, CallbackQuery

from src import defs
from src.svc import vk, telegram as tg
from src.svc.common.states import formatter as states_fmt, Values
from src.svc.common.navigator import Navigator
from src.svc.common import pagination, messages, error
from src.svc.vk.types import RawEvent
from src.svc.common.keyboard import Keyboard
from src.data import zoom
from src.data.settings import Settings, Group
from .states.tree import Init, Hub


@dataclass
class BaseCtx:
    navigator: Navigator
    settings: Settings
    last_call: float
    """ ## Last UNIX time when user interacted with bot """
    pages: pagination.Container
    last_bot_message: Optional[CommonBotMessage]

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

@dataclass
class VkCtx(BaseCtx):
    peer_id: int

@dataclass
class TgCtx(BaseCtx):
    chat: TgChat

@dataclass
class Ctx:
    vk: dict[int, VkCtx]
    tg: dict[int, TgCtx]


    def add_vk(self, peer_id: int) -> None:
        navigator = Navigator([Init.I_MAIN], [], set())
        settings = Settings(Group(), zoom.Container.default())

        self.vk[peer_id] = VkCtx(
            navigator           = navigator, 
            settings            = settings, 
            last_call           = time.time(),
            pages               = pagination.Container.default(),
            last_bot_message    = None,
            peer_id             = peer_id
        )

        logger.info("created ctx for vk {}", peer_id)

        return self.vk[peer_id]

    def add_tg(self, chat: TgChat) -> None:
        navigator = Navigator([Init.I_MAIN], [], set())
        settings = Settings(Group(), zoom.Container.default())

        self.tg[chat.id] = TgCtx(
            navigator           = navigator, 
            settings            = settings, 
            last_call           = time.time(),
            pages               = pagination.Container.default(),
            last_bot_message    = None,
            chat                = chat
        )

        logger.info("created ctx for tg {}", chat.id)

        return self.tg[chat.id]

ctx = Ctx({}, {})

class Source:
    VK = "vk"
    TG = "tg"
    MESSAGE = "message"
    EVENT = "event"

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
        tree_values: Values
    ) -> str:
        if add_tree:
            text = states_fmt.tree(
                self.ctx.navigator, 
                tree_values
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
    vk: Optional[VkMessage] = None
    tg: Optional[TgMessage] = None


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
    def is_tg_supergroup(self):
        return self.tg.chat.type == tg.ChatType.SUPERGROUP
    
    @property
    def is_tg_group(self):
        if not self.is_from_tg:
            return False

        return self.tg.chat.type == tg.ChatType.GROUP
    
    @property
    def is_vk_group(self):
        if not self.is_from_vk:
            return False
        
        return self.is_group_chat and self.is_from_vk


    @property
    def is_group_chat(self):
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
    def text(self) -> str:
        if self.is_from_vk:
            return self.vk.text
        if self.is_from_tg:
            return self.tg.text

    async def vk_has_admin_rights(self) -> bool:
        if not self.is_from_vk:
            return False

        return await vk.has_admin_rights(self.vk.peer_id)

    async def can_pin(self) -> bool:
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
        keyboard: Optional[Keyboard] = None,
        add_tree: bool = False,
        tree_values: Optional[Values] = None
    ):

        text = self.preprocess_text(
            text        = text, 
            add_tree    = add_tree, 
            tree_values = tree_values
        )

        if self.is_from_vk:
            vk_message = self.vk

            result = await vk_message.answer(
                message          = text,
                keyboard         = keyboard.to_vk().get_json() if keyboard else None,
                dont_parse_links = True,
            )

            chat_id = result.peer_id
            id = result.conversation_message_id

        elif self.is_from_tg:
            tg_message = self.tg

            result = await tg_message.answer(
                text         = text,
                reply_markup = keyboard.to_tg() if keyboard else None,
            )

            chat_id = result.chat.id
            id = result.message_id
        
        bot_message = CommonBotMessage(
            src         = self.src,
            chat_id     = chat_id,
            id          = id,
            text        = text,
            keyboard    = keyboard,
            add_tree    = add_tree,
            tree_values = tree_values
        )

        self.ctx.last_bot_message = bot_message

@dataclass
class CommonBotTemplate:
    text: str
    keyboard: Keyboard

@dataclass
class CommonBotMessage:
    text: str
    keyboard: Keyboard

    add_tree: bool
    tree_values: Optional[Values]

    src: Optional[MESSENGER_SOURCE]
    chat_id: Optional[int]
    id: Optional[int]

    @property
    def is_from_vk(self):
        return self.src == Source.VK
    
    @property
    def is_from_tg(self):
        return self.src == Source.TG

    async def send(self) -> CommonBotMessage:
        if self.is_from_vk:
            result = await defs.vk_bot.api.messages.send(
                random_id        = random.randint(0, 99999),
                peer_ids         = [self.chat_id],
                message          = self.text,
                keyboard         = self.keyboard.to_vk().get_json(),
                dont_parse_links = True,
            )

            sent_message: MessagesSendUserIdsResponseItem = result[0]

            chat_id = sent_message.peer_id
            id = sent_message.conversation_message_id

        elif self.is_from_tg:
            result = await defs.tg_bot.send_message(
                chat_id                  = self.chat_id,
                text                     = self.text,
                reply_markup             = self.keyboard.to_tg(),
                disable_web_page_preview = True,
            )

            chat_id = result.chat.id
            id = result.message_id
        
        bot_message = deepcopy(self)

        bot_message.chat_id = chat_id
        bot_message.id = id

        return bot_message
    
    def __str__(self) -> str:
        attrs = []

        for (name, value) in self.__dict__.items():

            repr_name = name
            repr_value = value

            if name in ["text"]:
                repr_value = "..."
            
            attrs.append(f"{repr_name}={repr_value}")
        
        attrs_str = ""
        attrs_str = "\n".join(attrs)

        return attrs_str

@dataclass
class CommonEvent(BaseCommonEvent):
    vk: Optional[RawEvent] = None
    tg: Optional[CallbackQuery] = None


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
        keyboard: Optional[Keyboard] = None,
        add_tree: bool = False,
        tree_values: Optional[Values] = None
    ):
        """
        ## Edit message by id inside event
        """

        text = self.preprocess_text(
            text        = text, 
            add_tree    = add_tree, 
            tree_values = tree_values
        )

        if self.is_from_vk:

            chat_id = self.vk["object"]["peer_id"]
            message_id = self.vk["object"]["conversation_message_id"]

            result = await defs.vk_bot.api.messages.edit(
                peer_id                 = chat_id,
                conversation_message_id = message_id,
                message                 = text,
                keyboard                = keyboard.to_vk().get_json() if keyboard else None,
                dont_parse_links        = True,
            )
        
        elif self.is_from_tg:

            chat_id = self.tg.message.chat.id
            message_id = self.tg.message.message_id

            result = await defs.tg_bot.edit_message_text(
                chat_id                  = chat_id,
                message_id               = message_id,
                text                     = text,
                reply_markup             = keyboard.to_tg() if keyboard else None,
                disable_web_page_preview = True,
            )

        bot_message = CommonBotMessage(
            src         = self.src,
            chat_id     = chat_id,
            id          = message_id,
            text        = text,
            keyboard    = keyboard,
            add_tree    = add_tree,
            tree_values = tree_values
        )

        self.ctx.last_bot_message = bot_message

@dataclass
class CommonEverything(BaseCommonEvent):
    event_src: Optional[EVENT_SOURCE] = None

    message: Optional[CommonMessage] = None
    event: Optional[CommonEvent] = None


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
        keyboard: Optional[Keyboard] = None,
        add_tree: bool = False,
        tree_values: Optional[Values] = None
    ):
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
    