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

def load_dispatch(
    router: Router, 
    init_middlewares: bool = True,
) -> Dispatcher:
    """
    ## Init dispatcher
    """

    dp = Dispatcher()
    dp.include_router(router)

    if init_middlewares:
        from .middlewares import (
            CtxCheck,
            CommonMessageMaker,
            CommonEventMaker
        )

        update_outer_middlewares = [
            CtxCheck()
        ]

        message_outer_middlewares = [
            CommonMessageMaker()
        ]

        callback_query_outer_middlewares = [
            CommonEventMaker()
        ]
    else:
        update_outer_middlewares = []

    for mw in update_outer_middlewares:
        dp.update.outer_middleware(mw)
    
    for mw in message_outer_middlewares:
        dp.message.outer_middleware(mw)

    for mw in callback_query_outer_middlewares:
        dp.callback_query.outer_middleware(mw)

    return dp