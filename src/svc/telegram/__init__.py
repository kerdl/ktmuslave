import asyncio
from typing import Literal
from dotenv import get_key
from aiogram import Bot, Router, Dispatcher
from aiogram.types import MessageEntity, ForceReply


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


class EntityType:
    MENTION = "mention"
    BOT_COMMAND = "bot_command"


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
            BotMentionFilter,
            CtxCheck,
            CommonMessageMaker,
            CommonEventMaker
        )

        update_outer_middlewares = [
            CtxCheck()
        ]

        message_outer_middlewares = [
            BotMentionFilter(),
            CommonMessageMaker()
        ]

        callback_query_outer_middlewares = [
            CommonEventMaker()
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