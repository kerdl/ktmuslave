from vkbottle import Bot
from dotenv import get_key


def is_group_chat(peer_id: int, from_id: int) -> bool:
    return peer_id != from_id

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