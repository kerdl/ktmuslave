from typing import Optional
from vkbottle import Bot, VKAPIError
from vkbottle.tools.dev.mini_types.bot.foreign_message import ForeignMessageMin
from dotenv import get_key

from src import defs


async def has_admin_rights(peer_id: int) -> bool:
    try:
        members = await defs.vk_bot.api.messages.get_conversation_members(
            peer_id = peer_id
        )

        return True
    # You don't have access to this chat
    except VKAPIError[917]:
        return False

def is_group_chat(peer_id: int, from_id: int) -> bool:
    return peer_id != from_id

def text_from_forwards(forwards: list[ForeignMessageMin]) -> Optional[str]: 
    texts: list[str] = []

    for message in forwards:
        if message.text:
            texts.append(message.text)
        
        if message.fwd_messages is not None:
            deeper_text = text_from_forwards(message.fwd_messages)

            if deeper_text is not None:
                texts.append(deeper_text)
    
    if len(texts) < 1:
        return None

    return "\n\n".join(texts)


def load(loop = None) -> Bot:
    """
    ## Set token, load blueprints and return a `Bot`
    """

    bot = Bot(token=get_key(".env", "VK_TOKEN"), loop=loop)

    from .middlewares import (
        BotMentionFilter,
        CtxCheckRaw,
        CtxCheckMessage,
        CommonMessageMaker,
        CommonEventMaker,
        OldMessagesBlock
    )

    message_view_middlewares = [
        BotMentionFilter,
        CtxCheckMessage,
        CommonMessageMaker,
    ]

    raw_event_view_middlewares = [
        CtxCheckRaw,
        CommonEventMaker,
        OldMessagesBlock
    ]
    
    # mw - MiddleWare
    for mw in message_view_middlewares:
        bot.labeler.message_view.middlewares.append(mw)
    
    # mw - MiddleWare
    for mw in raw_event_view_middlewares:
        bot.labeler.raw_event_view.middlewares.append(mw)
    
    bot.labeler.message_view.replace_mention = True

    return bot