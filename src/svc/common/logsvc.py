from __future__ import annotations
from src import defs
from . import CommonEverything, CommonMessage, CommonEvent, MESSENGER_SOURCE, MESSENGER_OR_EVT_SOURCE, Source
from src.svc.vk.types_ import RawEvent
import datetime
from dataclasses import dataclass
from typing import Literal, Optional
from aiogram.types import CallbackQuery, ChatMemberUpdated, Message as TgMessage
from vkbottle.bot import Message as VkMessage
from pydantic import BaseModel


class LoggerSrc:
    MESSAGE = "message"
    CALLBACK = "callback"
    VK_MESSAGE = "vk_message"
    TG_MESSAGE = "tg_message"
    TG_EDITED_MESSAGE = "tg_edited_message"
    TG_CHANNEL_POST = "tg_channel_post"
    TG_EDITED_CHANNEL_POST = "tg_edited_channel_post"
    BCAST_MESSAGE = "bcast_message"

    def from_common(src: MESSENGER_OR_EVT_SOURCE) -> MESSAGE_SRC_LITERAL:
        if src == Source.VK:
            return LoggerSrc.VK_MESSAGE
        if src == Source.TG:
            return LoggerSrc.TG_MESSAGE

        return src


EVENT_SRC_LITERAL = Literal["message", "callback"]
CALLBACK_SRC_LITERAL = Literal["vk_callback", "tg_callback_query", "tg_my_chat_member"]
MESSAGE_SRC_LITERAL = Literal[
    "vk_message",
    "tg_message",
    "tg_edited_message",
    "tg_channel_post",
    "tg_edited_channel_post",
    "bcast_message"
]


@dataclass
class Logger:
    addr: str

    async def log_everything(self, everything: CommonEverything):
        ...

    async def log_broadcast(self, bcast):
        ...


class BroadcastEvent(BaseModel):
    src: MESSENGER_SOURCE
    chat_id: int
    changes: Optional[str]

class UnionMessage(BaseModel):
    src: MESSAGE_SRC_LITERAL
    dt: datetime.datetime
    vk_message: Optional[VkMessage]
    tg_message: Optional[TgMessage]
    tg_edited_message: Optional[TgMessage]
    tg_channel_post: Optional[TgMessage]
    tg_edited_channel_post: Optional[TgMessage]
    bcast_message: Optional[BroadcastEvent]

    @classmethod
    def from_common_message(cls: type[UnionMessage], message: CommonMessage) -> UnionMessage:
        return cls(
            src=LoggerSrc.from_common(message.src),
            dt=message.dt,
            vk_message=message.vk,
            tg_message=message.tg,
            tg_edited_message=message.tg_edited_message,
            tg_channel_post=message.tg_channel_post,
            tg_edited_channel_post=message.tg_edited_channel_post,
        )

class UnionCallback(BaseModel):
    src: CALLBACK_SRC_LITERAL
    dt: datetime.datetime
    vk_callback: Optional[RawEvent]
    tg_callback_query: Optional[CallbackQuery]
    tg_my_chat_member: Optional[ChatMemberUpdated]

    @classmethod
    def from_common_event(cls: type[UnionCallback], event: CommonEvent) -> UnionCallback:
        return cls(
            src=LoggerSrc.from_common(event.src),
            dt=event.dt,
            vk_callback=event.vk,
            tg_callback_query=event.tg,
            tg_my_chat_member=event.tg_my_chat_member
        )

class UnionEvent(BaseModel):
    src: MESSENGER_SOURCE
    evt_src: EVENT_SRC_LITERAL
    message: UnionMessage
    callback: UnionCallback

    @classmethod
    def from_everything(cls: type[UnionEvent], everything: CommonEverything) -> UnionEvent:
        if everything.is_from_message:
            evt_src = LoggerSrc.MESSAGE
        elif everything.is_from_event:
            evt_src = LoggerSrc.CALLBACK

        return cls(
            src=everything.src,
            evt_src=evt_src,
            message=everything.message,
            callback=everything.event
        )
