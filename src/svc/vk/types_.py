from __future__ import annotations
from typing import TypedDict, Literal, Optional, Any
from vkbottle.bot import Message as MessageV1
from vkbottle.tools.mini_types.base.mention import Mention
from vkbottle_types.codegen.objects import (
    MessagesActionOneOf,
    MessagesMessageActionPhoto
)
from pydantic import BaseModel, Field


ACTION_STATUS_LITERAL = Literal[
    "chat_photo_update"
    "chat_photo_remove"
    "chat_create"
    "chat_title_update"
    "chat_invite_user"
    "chat_kick_user"
    "chat_pin_message"
    "chat_unpin_message"
    "chat_invite_user_by_link"
    "chat_invite_user_by_message_request"
    "chat_screenshot"
]


class RawEventObject(TypedDict):
    user_id: int
    peer_id: int
    event_id: str
    payload: dict[Any, Any]
    """
    # Any serializable type
    We always use `str`
    """
    conversation_message_id: int

class RawEvent(TypedDict):
    group_id: int
    type: Literal["message_event"] # and maybe more
    event_id: str
    v: str
    """# API version"""
    object: RawEventObject


class ActionPhotoV2(BaseModel):
    photo_50: str = Field(default_factory=str)
    photo_100: str = Field(default_factory=str)
    photo_200: str = Field(default_factory=str)
    
    def from_v1(v1: MessagesMessageActionPhoto) -> ActionPhotoV2:
        return ActionPhotoV2(
            photo_50=v1.photo_50,
            photo_100=v1.photo_100,
            photo_200=v1.photo_200,
        )

class ActionV2(BaseModel):
    type: Optional[ACTION_STATUS_LITERAL] = None
    conversation_message_id: Optional[int] = None
    email: Optional[str] = None
    member_id: Optional[int] = None
    message: Optional[str] = None
    photo: Optional[ActionPhotoV2] = None
    text: Optional[str] = None
    
    def from_v1(v1: MessagesActionOneOf) -> ActionV2:
        return ActionV2(
            type=v1.type.value,
            conversation_message_id=v1.conversation_message_id,
            email=v1.email,
            memeber_id=v1.member_id,
            message=v1.message,
            photo=ActionPhotoV2.from_v1(v1.photo),
            text=v1.text
        )

class MentionV2(BaseModel):
    id: int
    text: str
    
    def from_v1(v1: Mention) -> MentionV2:
        return MentionV2(
            id=v1.id,
            text=v1.text
        )

class MessageV2(BaseModel):
    """
    # Partial vkbottle Message as a pydantic V2 model
    
    The only reason behind this is that pydantic fails
    to serialize V1 models (vkbottle.bot.Message)
    inside V2 models (my database model).
    
    I'm never using vkbottle again. Fuck you.
    
    Not only their imports take >10s to process,
    but they also don't migrate their models. Shame.
    """
    action: Optional[ActionV2] = None
    conversation_message_id: Optional[int] = None
    date: Optional[int] = None
    from_id: Optional[int] = None
    fwd_messages: list[MessageV2] = Field(default_factory=list)
    id: Optional[int] = None
    peer_id: Optional[int] = None
    text: Optional[str] = None
    replace_mention: Optional[bool] = None
    group_id: Optional[int] = None
    _mention: Optional[MentionV2] = None

    def from_v1(v1: MessageV1) -> MessageV2:
        return MessageV2(
            action=ActionV2.from_v1(v1.action) if v1.action else None,
            conversation_message_id=v1.conversation_message_id,
            date=v1.date,
            from_id=v1.from_id,
            fwd_messages=[
                MessageV2.from_v1(v1_fwd) for v1_fwd in v1.fwd_messages
            ] if v1.fwd_messages else [],
            id=v1.id,
            peer_id=v1.peer_id,
            text=v1.text,
            replace_mention=v1.replace_mention,
            group_id=v1.group_id,
            _mention=MentionV2.from_v1(v1._mention) if v1._mention else None
        )

    @property
    def message_id(self) -> int:
        return self.conversation_message_id or self.id
    
    @property
    def mention(self) -> Optional[MentionV2]:
        if not self.replace_mention: return None
        return self._mention
    
    @property
    def is_mentioned(self) -> bool:
        if self.mention and self.group_id:
            return self.mention.id == -self.group_id
        return False