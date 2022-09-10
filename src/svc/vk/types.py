from typing import TypedDict, Literal, Any


class RawEventObject(TypedDict):
    user_id: int
    peer_id: int
    event_id: str
    payload: dict[Any, Any]
    conversation_message_id: int

class RawEvent(TypedDict):
    group_id: int
    type: Literal["message_event"]
    event_id: str
    v: str
    object: RawEventObject