from pydantic import BaseModel
from src.svc.common.keyboard import Keyboard


class CommonBotTemplate(BaseModel):
    """
    ## Container of message to send later
    - unlike `CommonBotMessage`, this may not
    be already sent, it's just a template
    - used to construct pages from massive data
    """
    text: str
    keyboard: Keyboard