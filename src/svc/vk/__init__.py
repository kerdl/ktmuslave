from vkbottle import Bot
from dotenv import get_key

def load(loop = None) -> Bot:
    """
    ## Set token, load blueprints and return a `Bot`
    """

    bot = Bot(token=get_key(".env", "VK_TOKEN"), loop=loop)

    from .bps import (
        init,
        hub, 
    )

    from .middlewares import (
        CommonMessageMaker,
        CtxCheck
    )

    blueprints = [
        init.bp,
        hub.bp,
    ]

    message_view_middlewares = [
        CommonMessageMaker,
        CtxCheck
    ]

    raw_event_view_middlewares = [

    ]

    # bp - BluePrint
    for bp in blueprints:
        bp.load(bot)
    
    # mw - MiddleWare
    for mw in message_view_middlewares:
        bot.labeler.message_view.middlewares.append(mw)
    
    # mw - MiddleWare
    for mw in raw_event_view_middlewares:
        bot.labeler.raw_event_view.middlewares.append(mw)
    
    return bot