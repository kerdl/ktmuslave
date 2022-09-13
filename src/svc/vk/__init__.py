from vkbottle import Bot
from dotenv import get_key

def load(
    loop = None, 
    init_handlers: bool = True,
    init_middlewares: bool = True,
) -> Bot:
    """
    ## Set token, load blueprints and return a `Bot`
    """

    bot = Bot(token=get_key(".env", "VK_TOKEN"), loop=loop)

    if init_handlers:
        from . import bps
        from .bps import (
            init,
            hub, 
        )

        blueprints = [
            bps.bp,
            init.bp,
            hub.bp,
        ]
    else:
        blueprints = []

    if init_middlewares:
        from .middlewares import (
            GroupMentionFilter,
            CtxCheckRaw,
            CtxCheckMessage,
            CommonEventMaker,
            CommonMessageMaker,
        )

        message_view_middlewares = [
            GroupMentionFilter,
            CtxCheckMessage,
            CommonMessageMaker,
        ]

        raw_event_view_middlewares = [
            CtxCheckRaw,
            CommonEventMaker,
        ]
    else:
        message_view_middlewares = []
        raw_event_view_middlewares = []

    # bp - BluePrint
    for bp in blueprints:
        bp.load(bot)
    
    # mw - MiddleWare
    for mw in message_view_middlewares:
        bot.labeler.message_view.middlewares.append(mw)
    
    # mw - MiddleWare
    for mw in raw_event_view_middlewares:
        bot.labeler.raw_event_view.middlewares.append(mw)
    
    bot.labeler.message_view.replace_mention = True

    return bot