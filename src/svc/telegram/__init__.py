import asyncio
from typing import Any
from dotenv import get_key
from aiogram import Bot, Dispatcher


def load_bot(loop: asyncio.BaseEventLoop | asyncio.AbstractEventLoop = None) -> Bot:
    """
    ## Set token, load handlers and return a `Bot`
    """

    bot = Bot(token=get_key(".env", "TG_TOKEN"), loop=loop)
    return bot

def load_dispatch(bot: Any, loop: Any = None) -> Dispatcher:
    """
    ## Init dispatcher that routes through all handlers

    ```
    @dp.message_handler(commands=['suck', 'penis'])
    async def thing_that_will_process_a_new_message(message): ...
    ```python

    `^` that is a handler
    """

    dp = Dispatcher(bot, loop)
    return dp