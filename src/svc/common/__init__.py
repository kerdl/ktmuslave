from __future__ import annotations
from loguru import logger
from typing import Literal, Optional
from dataclasses import dataclass
from vkbottle import ShowSnackbarEvent
from vkbottle.bot import Message as VkMessage
from aiogram.types import Message as TgMessage, CallbackQuery

from src import defs
from src.svc import vk, telegram as tg
from src.svc.common.navigator import Navigator
from src.svc.vk.types import RawEvent
from src.svc.common.keyboard import Keyboard
from .context import Ctx, TgCtx, VkCtx, BaseCtx


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
    ):
        if self.is_from_vk:
            vk_message = self.vk

            result = await vk_message.answer(
                message          = text,
                keyboard         = keyboard.to_vk().get_json() if keyboard else None,
                dont_parse_links = True,
            )

            self.ctx.last_bot_message_id = result.conversation_message_id

        elif self.is_from_tg:
            tg_message = self.tg

            result = await tg_message.answer(
                text         = text,
                reply_markup = keyboard.to_tg() if keyboard else None,
            )

            self.ctx.last_bot_message_id = result.message_id

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
    ):
        """
        ## Edit message by id inside event
        """

        if self.is_from_vk:

            peer_id = self.vk["object"]["peer_id"]
            conv_msg_id = self.vk["object"]["conversation_message_id"]

            result = await defs.vk_bot.api.messages.edit(
                peer_id                 = peer_id,
                conversation_message_id = conv_msg_id,
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
                disable_web_page_preview = True
            )

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
    ):
        if self.is_from_event:
            event = self.event
            return await event.edit_message(text, keyboard)
        if self.is_from_message:
            message = self.message
            return await message.answer(text, keyboard)

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
    