from loguru import logger
from typing import Literal, Optional
from dataclasses import dataclass
from vkbottle import VKAPIError, ShowSnackbarEvent
from vkbottle.bot import Message as VkMessage
from aiogram.types import Message as TgMessage, CallbackQuery

from src import defs
from src.svc import vk, telegram as tg
from src.svc.vk.types import RawEvent
from src.svc.common.keyboard import Keyboard
from .context import Ctx, TgCtx, VkCtx


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
    src: MESSENGER_SOURCE

    @property
    def is_from_vk(self):
        return self.src == Source.VK

    @property
    def is_from_tg(self):
        return self.src == Source.TG

@dataclass
class CommonMessage(BaseCommonEvent):
    vk: Optional[VkMessage] = None
    vk_ctx: Optional[VkCtx] = None

    tg: Optional[TgMessage] = None
    tg_ctx: Optional[TgCtx] = None

    is_group_chat: Optional[bool] = None


    @classmethod
    def from_vk(cls, message: VkMessage):
        vk_ctx = ctx.vk.get(message.peer_id)

        self = cls(
            src=Source.VK,
            vk=message,
            vk_ctx=vk_ctx,
            is_group_chat=vk.is_group_chat(message.peer_id, message.from_id),
        )

        return self
    
    @classmethod
    def from_tg(cls, message: TgMessage):
        tg_ctx = ctx.tg.get(message.chat.id)

        self = cls(
            src=Source.TG,
            tg=message,
            tg_ctx=tg_ctx,
            is_group_chat=tg.is_group_chat(message.chat.type),
        )

        return self

    @property
    def is_tg_supergroup(self):
        return self.tg.chat.type == tg.ChatType.SUPERGROUP
    
    @property
    def is_tg_group(self):
        return self.tg.chat.type == tg.ChatType.GROUP

    @property
    def main_ctx(self) -> Ctx:
        return ctx

    @property
    def chat_id(self) -> int:
        if self.is_from_vk:
            return self.vk.peer_id
        if self.is_from_tg:
            return self.tg.chat.id
    
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

    @property
    def navigator(self):
        if self.src == Source.VK:
            return self.vk_ctx.navigator
        if self.src == Source.TG:
            return self.tg_ctx.navigator

    async def can_pin(self) -> bool:
        if self.is_from_vk:
            return True
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

        elif self.is_from_tg:
            tg_message = self.tg

            result = await tg_message.answer(
                text         = text,
                reply_markup = keyboard.to_tg() if keyboard else None,
            )

@dataclass
class CommonEvent(BaseCommonEvent):
    vk: Optional[RawEvent] = None
    vk_ctx: Optional[VkCtx] = None

    tg_callback_query: Optional[CallbackQuery] = None
    tg_ctx: Optional[TgCtx] = None

    is_group_chat: Optional[bool] = None
    chat_id: Optional[int] = None


    @classmethod
    def from_vk(cls, event: RawEvent):
        event_object = event["object"]
        peer_id = event_object["peer_id"]
        user_id = event_object["user_id"]

        vk_ctx = ctx.vk.get(peer_id)

        self = cls(
            src=Source.VK,
            vk=event,
            vk_ctx=vk_ctx,
            is_group_chat=vk.is_group_chat(peer_id, user_id),
            chat_id=event["object"]["peer_id"]
        )

        return self
    
    @classmethod
    def from_tg_callback_query(cls, callback_query: CallbackQuery):
        tg_ctx = ctx.tg.get(callback_query.message.chat.id)

        self = cls(
            src=Source.TG,
            tg_callback_query=callback_query,
            tg_ctx=tg_ctx,
            is_group_chat=tg.is_group_chat(callback_query.message.chat.type),
            chat_id=callback_query.message.chat.id
        )

        return self
    
    @property
    def is_tg_supergroup(self):
        return self.tg_callback_query.message.chat.type == tg.ChatType.SUPERGROUP
    
    @property
    def is_tg_group(self):
        return self.tg_callback_query.message.chat.type == tg.ChatType.GROUP

    @property
    def navigator(self):
        if self.is_from_vk:
            return self.vk_ctx.navigator
        if self.is_from_tg:
            return self.tg_ctx.navigator
    
    @property
    def message_id(self):
        if self.is_from_vk:
            return self.vk["object"]["conversation_message_id"]
        if self.is_from_tg:
            return self.tg_callback_query.message.message_id

    async def can_pin(self) -> bool:
        if self.is_from_vk:
            try:
                members = await defs.vk_bot.api.messages.get_conversation_members(
                    peer_id = self.vk["object"]["peer_id"]
                )

                return True
            # You don't have access to this chat
            except VKAPIError[917]:
                return False

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
            result = await self.tg_callback_query.answer(
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

            chat_id = self.tg_callback_query.message.chat.id
            message_id = self.tg_callback_query.message.message_id

            result = await defs.tg_bot.edit_message_text(
                chat_id                  = chat_id,
                message_id               = message_id,
                text                     = text,
                reply_markup             = keyboard.to_tg() if keyboard else None,
                disable_web_page_preview = True
            )

@dataclass
class CommonEverything(BaseCommonEvent):
    event_src: EVENT_SOURCE

    message: Optional[CommonMessage] = None
    event: Optional[CommonEvent] = None

    is_group_chat: Optional[bool] = None
    chat_id: Optional[int] = None

    @classmethod
    def from_message(cls, message: CommonMessage):
        self = cls(
            src=message.src,
            event_src=Source.MESSAGE,
            message=message,
            is_group_chat=message.is_group_chat,
            chat_id=message.chat_id
        )

        return self
    
    @classmethod
    def from_event(cls, event: CommonEvent):
        self = cls(
            src=event.src,
            event_src=Source.EVENT,
            event=event,
            is_group_chat=event.is_group_chat,
            chat_id=event.chat_id
        )

        return self

    @property
    def is_from_message(self):
        return self.event_src == Source.MESSAGE
    
    @property
    def is_from_event(self):
        return self.event_src == Source.EVENT
    
    @property
    def is_tg_supergroup(self):
        if self.is_from_event:
            return self.event.is_tg_supergroup
        if self.is_from_message:
            return self.message.is_tg_supergroup
    
    @property
    def is_tg_group(self):
        if self.is_from_event:
            return self.event.is_tg_group
        if self.is_from_message:
            return self.message.is_tg_group

    @property
    def navigator(self):
        if self.is_from_message:
            return self.message.navigator
        if self.is_from_event:
            return self.event.navigator

    async def can_pin(self) -> bool:
        if self.is_from_event:
            return await self.event.can_pin()
        if self.is_from_message:
            return await self.message.can_pin()

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
    