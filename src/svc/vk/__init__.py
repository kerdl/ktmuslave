from typing import Optional
from vkbottle import Bot, VKAPIError
from vkbottle.tools.dev.mini_types.bot.foreign_message import ForeignMessageMin
from vkbottle_types.responses.messages import MessagesSendUserIdsResponseItem
from vkbottle_types.codegen.responses.messages import BaseBoolInt
from dotenv import get_key
from io import StringIO
import random

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

async def chunked_send(
    peer_id: int,
    message: Optional[str],
    keyboard: Optional[str],
    dont_parse_links: bool = True,
) -> list[MessagesSendUserIdsResponseItem]:
    stream = StringIO(message)
    responses = []

    is_last = False

    while True:
        chunk = stream.read(4096)

        is_last = len(chunk) < 4096

        api_responses: list[MessagesSendUserIdsResponseItem] = (
            await defs.vk_bot.api.messages.send(
                random_id        = random.randint(0, 99999),
                peer_ids         = [peer_id],
                message          = chunk,
                keyboard         = keyboard if is_last else None,
                dont_parse_links = dont_parse_links,
            )
        )

        response = api_responses[0]

        responses.append(response)

        if is_last:
            break

    return responses

async def chunked_edit(
    peer_id: int,
    conversation_message_id: int,
    message: Optional[str],
    keyboard: Optional[str],
    dont_parse_links: bool = True,
) -> tuple[BaseBoolInt, list[MessagesSendUserIdsResponseItem]]:
    stream = StringIO(message)

    is_last = False
    used_first_edit = False

    edit_response = None
    sending_responses = []

    while True:
        chunk = stream.read(4096)

        is_last = len(chunk) < 4096

        if not used_first_edit:
            response: BaseBoolInt = (
                await defs.vk_bot.api.messages.edit(
                    peer_id                 = peer_id,
                    conversation_message_id = conversation_message_id,
                    message                 = chunk,
                    keyboard                = keyboard if is_last else None,
                    dont_parse_links        = True,
            ))

            edit_response = response

            used_first_edit = True
        else:
            api_responses: list[MessagesSendUserIdsResponseItem] = (
                await defs.vk_bot.api.messages.send(
                    random_id        = random.randint(0, 99999),
                    peer_ids         = [peer_id],
                    message          = chunk,
                    keyboard         = keyboard if is_last else None,
                    dont_parse_links = dont_parse_links,
                )
            )

            sending_responses.append(api_responses[0])
        
        if is_last:
            break
    
    return (edit_response, sending_responses)
    


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