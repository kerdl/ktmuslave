from vkbottle import Bot
from dotenv import get_key

def load(loop = None) -> Bot:
    """
    ## Set token, load blueprints and return a `Bot`
    """

    from .bps import (
        hub, 
        settings
    )

    blueprints = [
        hub.bp,
        settings.bp
    ]

    bot = Bot(token=get_key(".env", "VK_TOKEN"), loop=loop)

    for bp in blueprints:
        bp.load(bot)
    
    return bot