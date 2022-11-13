import asyncio
from typing import Literal, Optional
from dotenv import get_key
from aiogram import Bot, Router, Dispatcher
from aiogram.types import MessageEntity, ForceReply, InlineKeyboardMarkup, Message

from src import defs, text as text_utils


class ChatType:
    PRIVATE    = "private"
    GROUP      = "group"
    SUPERGROUP = "supergroup"
    CHANNEL    = "channel"

CHAT_TYPE = Literal["private", "group", "supergroup", "channel"]

def is_group_chat(    
    chat_type: CHAT_TYPE
) -> bool:
    return chat_type in [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]


async def chunked_send(
    chat_id: int,
    text: str,
    disable_web_page_preview: bool = True,
    reply_markup: Optional[InlineKeyboardMarkup] = None
) -> list[Message]:
    chunks = text_utils.chunks(text)
    responses = []
    
    for (index, chunk) in enumerate(chunks):
        is_last = (index + 1) == len(chunks)

        result = await defs.tg_bot.send_message(
            chat_id                  = chat_id,
            text                     = chunk,
            disable_web_page_preview = disable_web_page_preview,
            reply_markup             = reply_markup if is_last else None
        )

        responses.append(result)
    
    return responses

async def chunked_edit(
    chat_id: int,
    message_id: int,
    text: str,
    disable_web_page_preview: bool = True,
    reply_markup: Optional[InlineKeyboardMarkup] = None
) -> tuple[Message, list[Message]]:
    chunks = text_utils.chunks(text)

    is_used_first_edit = False

    edit_result = None
    sending_results = []
    
    for (index, chunk) in enumerate(chunks):
        is_last = (index + 1) == len(chunks)

        if not is_used_first_edit:
            result = await defs.tg_bot.edit_message_text(
                chat_id                  = chat_id,
                message_id               = message_id,
                text                     = chunk,
                disable_web_page_preview = disable_web_page_preview,
                reply_markup             = reply_markup if is_last else None
            )

            edit_result = result

            is_used_first_edit = True
        else:
            result = await defs.tg_bot.send_message(
                chat_id                  = chat_id,
                text                     = chunk,
                disable_web_page_preview = disable_web_page_preview,
                reply_markup             = reply_markup if is_last else None
            )

            sending_results.append(result)
    
    return (edit_result, sending_results)

class EntityType:
    MENTION = "mention"
    BOT_COMMAND = "bot_command"

class EventType:
    MESSAGE = "message"
    CALLBACK_QUERY = "callback_query"

def extract_mentions(entities: list[MessageEntity], text: str) -> list[str]:
    mentions: list[str] = []

    for enitity in entities:

        if enitity.type == EntityType.MENTION:
            mention = enitity.extract_from(text)
            mentions.append(mention)
    
    return mentions

def extract_commands(entities: list[MessageEntity], text: str) -> list[str]:
    commands: list[str] = []

    for entity in entities:

        if entity.type == EntityType.BOT_COMMAND:
            command = entity.extract_from(text)
            commands.append(command)
    
    return commands

def force_reply() -> ForceReply:
    return ForceReply(force_reply=True)


def load_bot(loop: asyncio.BaseEventLoop | asyncio.AbstractEventLoop = None) -> Bot:
    """
    ## Set token, load handlers and return a `Bot`
    """

    bot = Bot(token=get_key(".env", "TG_TOKEN"))
    return bot

def load_router() -> Router:
    """
    ## Init router
    """

    r = Router()

    return r

def load_dispatch(router: Router, init_middlewares: bool = True) -> Dispatcher:
    """
    ## Init dispatcher
    """

    dp = Dispatcher()
    dp.include_router(router)

    if init_middlewares:
        from .middlewares import (
            Log,
            Throttling,
            BotMentionFilter,
            CtxCheck,
            CommonMessageMaker,
            CommonEventMaker,
            OldMessagesBlock
        )

        update_outer_middlewares = [
            Log(),
            CtxCheck(),
            Throttling(),
        ]

        message_outer_middlewares = [
            BotMentionFilter(),
            CommonMessageMaker()
        ]

        callback_query_outer_middlewares = [
            CommonEventMaker(),
            OldMessagesBlock()
        ]

    else:
        update_outer_middlewares = []
        message_outer_middlewares = []
        callback_query_outer_middlewares = []

    for mw in update_outer_middlewares:
        dp.update.outer_middleware(mw)
    
    for mw in message_outer_middlewares:
        dp.message.outer_middleware(mw)

    for mw in callback_query_outer_middlewares:
        dp.callback_query.outer_middleware(mw)

    return dp