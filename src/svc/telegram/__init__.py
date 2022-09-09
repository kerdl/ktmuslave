import asyncio
from typing import Any
from dotenv import get_key
from aiogram import Bot, Router, Dispatcher


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

def load_dispatch(router: Router) -> Dispatcher:
    """
    ## Init dispatcher
    """

    dp = Dispatcher()
    dp.include_router(router)
    return dp