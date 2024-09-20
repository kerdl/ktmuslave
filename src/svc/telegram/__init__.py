import asyncio
from typing import (
    Literal,
    Optional,
    Callable,
    Union
)
from aiogram import Bot, Router, Dispatcher
from aiogram.types import (
    MessageEntity,
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
    ChatMemberUpdated
)
import html
from src import defs, text as text_utils


class ChatType:
    PRIVATE    = "private"
    GROUP      = "group"
    SUPERGROUP = "supergroup"
    CHANNEL    = "channel"

CHAT_TYPE = Literal[
    "private",
    "group",
    "supergroup",
    "channel"
]


def is_group_chat(    
    chat_type: CHAT_TYPE
) -> bool:
    return chat_type in [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]

def name_from_message(msg: Union[Message, ChatMemberUpdated]) -> tuple[str, Optional[str], Optional[str]]:
    return (msg.from_user.first_name, msg.from_user.last_name, msg.from_user.username)

def name_from_callback(cb: CallbackQuery) -> tuple[str, Optional[str], Optional[str]]:
    return (cb.from_user.first_name, cb.from_user.last_name, cb.from_user.username)


async def chunked_send(
    chat_id: int,
    text: str,
    disable_web_page_preview: bool = True,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    reply_to_message_id: Optional[int] = None,
    chunker: Callable[[str, Optional[int]], list[str]] = text_utils.chunks
) -> list[Message]:
    chunks = chunker(text)
    responses = []
    
    for (index, chunk) in enumerate(chunks):
        is_first = index == 0
        is_last = (index + 1) == len(chunks)

        result = await defs.tg_bot.send_message(
            chat_id=chat_id,
            text=chunk,
            disable_web_page_preview=disable_web_page_preview,
            reply_markup=reply_markup if is_last else None,
            reply_to_message_id=reply_to_message_id if is_first else None,
            parse_mode="HTML"
        )

        responses.append(result)
    
    return responses

async def chunked_edit(
    chat_id: int,
    message_id: int,
    text: str,
    disable_web_page_preview: bool = True,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    chunker: Callable[[str, Optional[int]], list[str]] = text_utils.chunks
) -> tuple[Message, list[Message]]:
    chunks = chunker(text)

    is_used_first_edit = False

    edit_result = None
    sending_results = []
    
    for (index, chunk) in enumerate(chunks):
        is_last = (index + 1) == len(chunks)

        if not is_used_first_edit:
            result = await defs.tg_bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=chunk,
                disable_web_page_preview=disable_web_page_preview,
                reply_markup=reply_markup if is_last else None,
                parse_mode="HTML"
            )
            edit_result = result
            is_used_first_edit = True
        else:
            result = await defs.tg_bot.send_message(
                chat_id=chat_id,
                text=chunk,
                disable_web_page_preview=disable_web_page_preview,
                reply_markup=reply_markup if is_last else None,
                parse_mode="HTML"
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

def escape_html(text: str) -> str:
    return html.escape(text)

def force_reply() -> ForceReply:
    return ForceReply(force_reply=True)


def load_bot(token: Optional[str] = None) -> Bot:
    """
    ## Set token, load handlers and return a `Bot`
    """
    bot = Bot(token=token)
    return bot

def load_router() -> Router:
    """
    ## Init router
    """
    return Router()

def load_dispatch(router: Router) -> Dispatcher:
    """
    ## Init dispatcher
    """
    dp = Dispatcher()
    dp.include_router(router)
    return dp