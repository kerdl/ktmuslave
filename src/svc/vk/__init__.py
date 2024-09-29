from typing import Optional, Callable
from vkbottle import Bot, VKAPIError, GroupEventType, API, LoopWrapper
from vkbottle.http import SingleAiohttpClient
from vkbottle.bot import Message, MessageEvent
from vkbottle.tools.mini_types.bot.foreign_message import ForeignMessageMin
from vkbottle_types.responses.messages import MessagesSendUserIdsResponseItem
from vkbottle_types.objects import MessagesForward, BaseBoolInt
from aiohttp import TCPConnector
import random
import asyncio

from src import defs, text
from src.svc.vk.types_ import RawEvent, MessageV2


async def has_admin_rights(peer_id: int) -> bool:
    try:
        await defs.vk_bot.api.messages.get_conversation_members(
            peer_id = peer_id
        )
        return True
    # You don't have access to this chat
    except VKAPIError[917]:
        return False

async def name_from_message(msg: MessageV2) -> tuple[Optional[str], Optional[str], str]:
    user = (await defs.vk_bot.api.users.get(user_ids=[msg.from_id]))
    if len(user) < 1: return (None, None, msg.from_id)
    user = user[0]
    return (user.first_name, user.last_name, user.nickname or str(user.id))

async def name_from_raw(raw: RawEvent) -> tuple[Optional[str], Optional[str], str]:
    user = (await defs.vk_bot.api.users.get(user_ids=[raw["object"]["user_id"]]))
    if len(user) < 1: return (None, None, raw["object"]["user_id"])
    user = user[0]
    return (user.first_name, user.last_name, user.nickname or str(user.id))


async def chunked_send(
    peer_id: int,
    message: Optional[str] = None,
    keyboard: Optional[str] = None,
    reply_to: Optional[int] = None,
    dont_parse_links: bool = True,
    chunker: Callable[[str, Optional[int]], list[str]] = text.chunks
) -> list[MessagesSendUserIdsResponseItem]:
    chunks = chunker(message)
    responses = []

    fwd = None

    if reply_to is not None:
        fwd = MessagesForward(
            is_reply=True,
            conversation_message_ids=[reply_to],
            peer_id=peer_id
        )

    for (index, chunk) in enumerate(chunks):
        is_first = index == 0
        is_last = (index + 1) == len(chunks)

        api_responses: list[MessagesSendUserIdsResponseItem] = (
            await defs.vk_bot.api.messages.send(
                random_id=random.randint(0, 99999),
                peer_ids=[peer_id],
                message=chunk,
                keyboard=keyboard if is_last else None,
                forward=fwd if is_first else None,
                dont_parse_links=dont_parse_links,
            )
        )
        response = api_responses[0]
        responses.append(response)

    return responses

async def chunked_edit(
    peer_id: int,
    conversation_message_id: int,
    message: Optional[str],
    keyboard: Optional[str],
    dont_parse_links: bool = True,
    chunker: Callable[[str, Optional[int]], list[str]] = text.chunks
) -> tuple[BaseBoolInt, list[MessagesSendUserIdsResponseItem]]:
    chunks = chunker(message)

    used_first_edit = False

    edit_response = None
    sending_responses = []

    for (index, chunk) in enumerate(chunks):
        is_last = (index + 1) == len(chunks)

        if not used_first_edit:
            response: BaseBoolInt = (await defs.vk_bot.api.messages.edit(
                peer_id=peer_id,
                conversation_message_id=conversation_message_id,
                message=chunk,
                keyboard=keyboard if is_last else None,
                dont_parse_links=True,
            ))
            edit_response = response
            used_first_edit = True
        else:
            api_responses: list[MessagesSendUserIdsResponseItem] = (
                await defs.vk_bot.api.messages.send(
                    random_id=random.randint(0, 99999),
                    peer_ids=[peer_id],
                    message=chunk,
                    keyboard=keyboard if is_last else None,
                    dont_parse_links=dont_parse_links,
                )
            )
            sending_responses.append(api_responses[0])
    
    return (edit_response, sending_responses)
    


def is_group_chat(peer_id: int, from_id: int) -> bool:
    return peer_id != from_id

def text_from_forwards(forwards: list[MessageV2]) -> Optional[str]: 
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


def load(token: Optional[str] = None, loop: asyncio.AbstractEventLoop = None) -> Bot:
    """
    ## Set token, load dummy handlers and return a `Bot`
    """
    # disabling SSL verification
    # because VK uses self-signed shit
    connector = TCPConnector(ssl=False, loop=loop)
    http_client = SingleAiohttpClient(connector=connector)
    api = API(token=token, http_client=http_client)
    loop_wrapper = LoopWrapper()
    loop_wrapper.loop = loop
    bot = Bot(token=token, api=api, loop_wrapper=loop_wrapper)

    # vkbottle does not call raw event middlewares
    # if there's no raw event handlers
    @bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent)
    async def event_dummy(*_): ...

    @bot.on.message()
    async def message_dummy(*_): ...

    bot.labeler.message_view.replace_mention = True

    return bot