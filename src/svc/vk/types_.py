from typing import TypedDict, Literal, Any


class RawEventObject(TypedDict):
    user_id: int
    peer_id: int
    event_id: str
    payload: dict[Any, Any]
    """
    ## Any serializable type can be here
    - but we always use `str`
    """
    conversation_message_id: int

class RawEvent(TypedDict):
    group_id: int
    type: Literal["message_event"] # and maybe more
    event_id: str
    v: str
    """## API `v`ersion"""
    object: RawEventObject
