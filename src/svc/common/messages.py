from __future__ import annotations
from typing import Any
from src.data.settings import Settings

from src.svc import common
from src.data import zoom, format as fmt, schedule
from src.data.schedule import compare
from src.parse.zoom import Key
from src.svc.common.states import State
from src.svc.common.keyboard import Text


DEBUGGING = False


class Builder:
    def __init__(
        self, 
        separator: str = "\n\n",
    ) -> None:
        self.separator = separator
        self.components: list[str] = []
    
    def add(self, text: str) -> Builder:
        if text == "":
            return self

        self.components.append(text)
        return self
    
    def add_if(self, text: str, condition: bool):
        if condition:
            self.add(text)
        
        return self

    def make(self) -> str:
        return self.separator.join(self.components)


#### Common footers and headers ####

def default_footer_addition(everything: common.CommonEverything):
    """
    # Notice about bot mentioning

    ## Why
    - we filter anything that is not for us
    - so we should ask user to reply
    or mention the bot
    """

    from src import defs

    mention = ""
    footer_addition = ""

    if everything.is_group_chat:

        if everything.is_from_vk:
            mention = defs.vk_bot_mention
            footer_addition = format_mention_me(mention)

        elif everything.is_from_tg:
            footer_addition = format_reply_to_me()
    
    return footer_addition

DEBUG = (
    "8==oğ¤® trace:\n"
    "{trace}\n"
    "8==oğ¤® back_trace:\n"
    "{back_trace}\n"
)
def format_debug(trace: list[State], back_trace: list[State], last_bot_message: common.CommonBotMessage, settings: Settings):
    
    def fmt_trace(trace: list[State]):
        return "\n".join([f"âââ{state.space}:{state.anchor}" for state in trace])
    
    trace_str = fmt_trace(trace)
    back_trace_str = fmt_trace(back_trace)

    return DEBUG.format(
        trace            = trace_str,
        back_trace       = back_trace_str,
    )


CANT_PRESS_OLD_BUTTONS = (
    "ĞĞ¾ÑĞ¾ÑĞ¸ ğ ĞĞ¾Ñ ÑĞµĞ±Ğµ Ğ½Ğ¾Ğ²Ğ¾Ğµ ÑĞ¾Ğ¾Ğ±ÑĞµĞ½Ğ¸Ğµ, "
    "Ğ½Ğ° Ğ½ÑĞ¼ Ğ¸ ÑÑĞºĞ°Ğ¹ ĞºÑĞ´Ğ° ÑĞµĞ±Ğµ Ğ½Ğ°Ğ´Ğ¾"
)
def format_cant_press_old_buttons():
    return CANT_PRESS_OLD_BUTTONS

SENT_AS_NEW_MESSAGE = (
    "ĞÑĞ¿ÑĞ°Ğ²Ğ»ĞµĞ½Ğ¾ Ğ½Ğ¾Ğ²ÑĞ¼ ÑĞ¾Ğ¾Ğ±ÑĞµĞ½Ğ¸ĞµĞ¼"
)
def format_sent_as_new_message():
    return SENT_AS_NEW_MESSAGE

EMPTY_PAGE = (
    "ğ¤ | ĞĞ¾ĞºĞ° ÑÑĞ´Ğ° Ğ½Ğ¸ÑÑÑ Ğ½Ğµ Ğ·Ğ°Ğ²ĞµĞ·Ğ»Ğ¸"
)
def format_empty_page():
    return EMPTY_PAGE


PRESS_BEGIN = (
    f"ğ ĞĞ°Ğ¶Ğ¸Ğ¼Ğ°Ğ¹ {Text.BEGIN}, ÑÑĞ»Ğµ"
)
def format_press_begin():
    return PRESS_BEGIN


GROUPS = (
    "ğ | ĞÑÑĞ¿Ğ¿Ñ Ğ² ÑĞ°ÑĞ¿Ğ¸ÑĞ°Ğ½Ğ¸Ğ¸:\n"
    "ââââ° {groups}"
)
def format_groups(groups: list[str]):
    groups_str = ", ".join(groups)
    return GROUPS.format(groups=groups_str)


MENTION_ME = (
    "ğ® ĞÑÑ ÑĞ¿Ğ¾Ğ¼ÑĞ½Ğ¸ Ğ¼ĞµĞ½Ñ: {mention}, Ğ¸Ğ½Ğ°ÑĞµ Ğ½Ğµ ÑĞ²Ğ¸Ğ¶Ñ ğ®"
)
def format_mention_me(mention: str):
    return MENTION_ME.format(mention=mention)


REPLY_TO_ME = (
    "ğ® ĞÑÑ â©ï¸ Ğ¾ÑĞ²ĞµÑÑ â©ï¸ Ğ½Ğ° ÑÑĞ¾ ÑĞ¾Ğ¾Ğ±ÑĞµĞ½Ğ¸Ğµ, Ğ¸Ğ½Ğ°ÑĞµ Ğ½Ğµ ÑĞ²Ğ¸Ğ¶Ñ ğ®"
)
def format_reply_to_me():
    return REPLY_TO_ME


CHAT_WILL_MIGRATE = (
    "ğ¤ ĞĞ·-Ğ·Ğ° ÑÑĞ¾Ğ³Ğ¾, ÑÑĞ° Ğ³ÑÑĞ¿Ğ¿Ğ° ÑÑĞ°Ğ½ĞµÑ ÑÑĞ¿ĞµÑĞ³ÑÑĞ¿Ğ¿Ğ¾Ğ¹ ğ¤\n"
    "Ğ§Ğ¸ÑĞ°Ğ¹ Ğ¿Ğ¾Ğ´ÑĞ¾Ğ±Ğ½ĞµĞµ Ğ·Ğ´ĞµÑÑ: https://teleme.io/articles/turn_a_telegram_group_into_a_supergroup?hl=ru"
)
def format_chat_will_migrate():
    return CHAT_WILL_MIGRATE


PAGE_NUM = (
    "ğ | Ğ¡ÑÑĞ°Ğ½Ğ¸ÑĞ° {current}/{last}"
)
def format_page_num(current: int, last: int):
    return PAGE_NUM.format(current=current, last=last)


PRESS_BUTTONS_TO_CHANGE = (
    "ğ | ĞĞ°Ğ¶Ğ¼Ğ¸ Ğ½Ğ° Ğ¿Ğ°ÑĞ°Ğ¼ĞµÑÑ, ÑÑĞ¾Ğ±Ñ ĞµĞ³Ğ¾ Ğ¸Ğ·Ğ¼ĞµĞ½Ğ¸ÑÑ"
)
def format_press_buttons_to_change():
    return PRESS_BUTTONS_TO_CHANGE


NO_TEXT = (
    "â | ĞÑ ÑÑ Ğ±ÑĞ´Ğ»Ğ¾, ÑÑÑ Ğ½ĞµÑ ÑĞµĞºÑÑĞ°"
)
def format_no_text():
    return NO_TEXT


CURRENT_VALUE = (
    "ğ | Ğ¢ĞµĞºÑÑĞµĞµ Ğ·Ğ½Ğ°ÑĞµĞ½Ğ¸Ğµ: {value}"
)
def format_current_value(value: Any):
    return CURRENT_VALUE.format(
        value = fmt.value_repr(value)
    )


#### Full messages for specific states ####

WELCOME =  (
    "ğ¨ğ¿ ĞÑĞ´Ñ Ğ¿Ğ¸Ğ·Ğ´Ğ¸ÑÑ ÑĞ°ÑĞ¿Ğ¸ÑĞ°Ğ½Ğ¸Ğµ "
    "Ñ ğ ktmu-sutd.ru ğ "
    "Ğ¸ Ğ´ĞµĞ»Ğ¸ÑÑÑÑ Ñ {count}"
)
def format_welcome(is_group_chat: bool):
    if is_group_chat:
        return WELCOME.format(count="Ğ²Ğ°Ğ¼Ğ¸")
    else:
        return WELCOME.format(count="ÑĞ¾Ğ±Ğ¾Ğ¹")


GROUP_INPUT = (
    "ğ | ĞĞ°Ğ¿Ğ¸ÑĞ¸ ÑĞ²Ğ¾Ñ Ğ³ÑÑĞ¿Ğ¿Ñ\n"
    "ââââ° Ğ¤Ğ¾ÑĞ¼Ğ°Ñ: 1ĞºĞ´Ğ´69, 1-ĞºĞ´Ğ´-69, 1ĞĞĞ69, 1-ĞĞĞ-69\n"
    "ââââ° ĞĞ¾Ğ¶ĞµÑÑ Ğ½Ğ°Ğ¿Ğ¸ÑĞ°ÑÑ ÑÑ, ĞºĞ¾ÑĞ¾ÑĞ¾Ğ¹ Ğ½ĞµÑ Ğ² ÑĞ¿Ğ¸ÑĞºĞµ"
)
def format_group_input():
    return GROUP_INPUT


UNKNOWN_GROUP = (
    "â | {group} Ğ¿Ğ¾ĞºĞ° Ğ½ĞµÑ, Ğ²ÑÑ ÑĞ°Ğ²Ğ½Ğ¾ Ğ¿Ğ¾ÑÑĞ°Ğ²Ğ¸ÑÑ?"
)
def format_unknown_group(group: str):
    return UNKNOWN_GROUP.format(group=group)


INVALID_GROUP = (
    "â | Ğ­ÑĞ° ÑÑĞ¹Ğ½Ñ Ğ½Ğµ Ğ¿Ğ¾Ğ´ÑĞ¾Ğ´Ğ¸Ñ Ğ¿Ğ¾Ğ´ ÑĞ¾ÑĞ¼Ğ°Ñ: 1ĞºĞ´Ğ´69, 1-ĞºĞ´Ğ´-69, 1ĞĞĞ69, 1-ĞĞĞ-69\n"
    "ĞĞ°Ğ¿Ğ¸ÑĞ¸ ĞµÑÑ ÑĞ°Ğ· Ğ¿Ğ¾ ÑĞ¾ÑĞ¼Ğ°ÑÑ"
)
def format_invalid_group():
    return INVALID_GROUP


BROADCAST = (
    "ğ | Ğ¥Ğ¾ÑĞµÑÑ Ğ¿Ğ¾Ğ»ÑÑĞ°ÑÑ Ğ·Ğ´ĞµÑÑ ÑĞ°ÑÑÑĞ»ĞºÑ ÑĞ°ÑĞ¿Ğ¸ÑĞ°Ğ½Ğ¸Ñ?"
)
def format_broadcast():
    return BROADCAST


DO_PIN = (
    "ğ | Ğ¥Ğ¾ÑĞµÑÑ ÑĞ¾Ğ± Ñ Ğ·Ğ°ĞºÑĞµĞ¿Ğ»ÑĞ» ÑĞ°ÑÑÑĞ»ĞºÑ ÑĞ°ÑĞ¿Ğ¸ÑĞ°Ğ½Ğ¸Ñ?"
)
def format_do_pin():
    return DO_PIN


RECOMMEND_PIN = (
    "ğ | Ğ¯ Ğ¼Ğ¾Ğ³Ñ Ğ·Ğ°ĞºÑĞµĞ¿Ğ»ÑÑÑ ÑĞ°ÑÑÑĞ»ĞºÑ ÑĞ°ÑĞ¿Ğ¸ÑĞ°Ğ½Ğ¸Ñ, "
    "Ğ½Ğ¾ ÑĞµĞ¹ÑĞ°Ñ Ñ Ğ¼ĞµĞ½Ñ Ğ½ĞµÑ Ğ¿ÑĞ°Ğ²"
)
def format_recommend_pin():
    return RECOMMEND_PIN


PERMIT_PIN_VK = (
    "ğ½ | ĞÑĞ»Ğ¸ ÑĞ¾ÑĞµÑÑ Ğ·Ğ°ÑĞºĞµĞ¿, Ğ½Ğ°Ğ·Ğ½Ğ°ÑÑ Ğ¼ĞµĞ½Ñ Ğ°Ğ´Ğ¼Ğ¸Ğ½Ğ¾Ğ¼, "
    "Ğ»Ğ¸Ğ±Ğ¾ Ğ¿ÑĞ¾Ğ¿ÑÑÑĞ¸ ĞµÑĞ»Ğ¸ Ğ¿Ğ¾ĞµĞ±Ğ°ÑÑ"
)
PERMIT_PIN_TG = (
    "ğ½ | ĞÑĞ»Ğ¸ ÑĞ¾ÑĞµÑÑ Ğ·Ğ°ĞºÑĞµĞ¿, Ğ½Ğ°Ğ·Ğ½Ğ°ÑÑ Ğ¼ĞµĞ½Ñ Ğ°Ğ´Ğ¼Ğ¸Ğ½Ğ¾Ğ¼ Ñ Ğ¿ÑĞ°Ğ²Ğ¾Ğ¼ "
    "\"ĞĞ°ĞºÑĞµĞ¿Ğ»ĞµĞ½Ğ¸Ğµ ÑĞ¾Ğ¾Ğ±ÑĞµĞ½Ğ¸Ğ¹\", Ğ»Ğ¸Ğ±Ğ¾ Ğ¿ÑĞ¾Ğ¿ÑÑÑĞ¸ ĞµÑĞ»Ğ¸ Ğ¿Ğ¾ĞµĞ±Ğ°ÑÑ"
)
def format_permit_pin(src: common.MESSENGER_SOURCE):
    if src == common.Source.VK:
        return PERMIT_PIN_VK
    if src == common.Source.TG:
        return PERMIT_PIN_TG


CANT_PIN_VK = (
    "ĞĞµÑ Ñ Ğ¼ĞµĞ½Ñ Ğ½Ğ¸ÑÑÑ, Ğ¿ĞµÑĞµĞ¿ÑĞ¾Ğ²ĞµÑÑ Ğ¼Ğ¾Ñ Ğ°Ğ´Ğ¼Ğ¸Ğ½ĞºÑ"
)
CANT_PIN_TG = (
    "ĞĞµÑ Ñ Ğ¼ĞµĞ½Ñ Ğ½Ğ¸ÑÑÑ, Ğ¿ĞµÑĞµĞ¿ÑĞ¾Ğ²ĞµÑÑ Ğ¼Ğ¾Ñ Ğ¿ÑĞ°Ğ²Ğ¾ \"ĞĞ°ĞºÑĞµĞ¿Ğ»ĞµĞ½Ğ¸Ğµ ÑĞ¾Ğ¾Ğ±ÑĞµĞ½Ğ¸Ğ¹\""
)
def format_cant_pin(src: common.MESSENGER_SOURCE):
    if src == common.Source.VK:
        return CANT_PIN_VK
    if src == common.Source.TG:
        return CANT_PIN_TG


RECOMMEND_ADDING_ZOOM = (
    "ğ | Ğ¢Ñ Ğ¼Ğ¾Ğ¶ĞµÑÑ Ğ´Ğ¾Ğ±Ğ°Ğ²Ğ¸ÑÑ ÑÑÑĞ»ĞºĞ¸, ID, Ğ¿Ğ°ÑĞ¾Ğ»Ğ¸ Zoom Ğ¸ Ğ·Ğ°Ğ¼ĞµÑĞºĞ¸, "
    "ÑÑĞ¾Ğ±Ñ Ğ¾Ğ½Ğ¸ Ğ¿Ğ¾ĞºĞ°Ğ·ÑĞ²Ğ°Ğ»Ğ¸ÑÑ Ğ² ÑĞ°ÑĞ¿Ğ¸ÑĞ°Ğ½Ğ¸Ğ¸"
)
def format_recommend_adding_zoom():
    return RECOMMEND_ADDING_ZOOM


CHOOSE_ADDING_TYPE = (
    "ğ | ĞÑĞ±ĞµÑĞ¸ ĞºĞ°Ğº ÑÑ ÑĞ¾ÑĞµÑÑ Ğ´Ğ¾Ğ±Ğ°Ğ²Ğ¸ÑÑ Ğ·Ğ°Ğ¿Ğ¸ÑÑ/Ğ·Ğ°Ğ¿Ğ¸ÑĞ¸"
)
def format_choose_adding_type():
    return CHOOSE_ADDING_TYPE


ZOOM_ADD_FROM_TEXT_EXPLAIN = (
    f"{Text.FROM_TEXT} - Ğ¿Ğ¸ÑĞµÑÑ Ğ¾Ğ´Ğ½Ğ¾ Ğ±Ğ¾Ğ»ÑÑĞ¾Ğµ ÑĞ¾Ğ¾Ğ±ÑĞµĞ½Ğ¸Ğµ Ğ¿Ğ¾ ÑĞ¾ÑĞ¼Ğ°ÑÑ, "
    f"Ğ°Ğ²ÑĞ¾Ğ¼Ğ°ÑĞ¾Ğ¼ Ğ±ĞµÑÑÑ Ğ²ÑĞµ Ğ´Ğ°Ğ½Ğ½ÑĞµ"
)
def format_zoom_add_from_text_explain():
    return ZOOM_ADD_FROM_TEXT_EXPLAIN


ZOOM_ADD_MANUALLY_INIT_EXPLAIN = (
    f"{Text.MANUALLY} - Ğ´Ğ¾Ğ±Ğ°Ğ²Ğ»ÑĞµÑÑ, Ğ¸Ğ·Ğ¼ĞµĞ½ÑĞµÑÑ, ÑĞ´Ğ°Ğ»ÑĞµÑÑ "
    f"Ğ¿Ğ¾ Ğ¾ÑĞ´ĞµĞ»ÑĞ½Ğ¾ÑÑĞ¸"
)
def format_zoom_add_manually_init_explain():
    return ZOOM_ADD_MANUALLY_INIT_EXPLAIN


ZOOM_ADD_MANUALLY_HUB_EXPLAIN = (
    f"{Text.MANUALLY} - Ğ´Ğ¾Ğ±Ğ°Ğ²Ğ¸ÑÑ Ğ½Ğ¾Ğ²Ğ¾Ğµ Ğ¸Ğ¼Ñ Ğ²ÑÑÑĞ½ÑÑ"
)
def format_zoom_add_manually_hub_explain():
    return ZOOM_ADD_MANUALLY_HUB_EXPLAIN


SEND_ZOOM_DATA = (
    "ğ¬ | ĞĞ°Ğ¿Ğ¸ÑĞ¸ ÑĞ¾Ğ¾Ğ±ÑĞµĞ½Ğ¸Ğµ Ñ Ğ´Ğ°Ğ½Ğ½ÑĞ¼Ğ¸ Zoom Ğ¿Ğ¾ ÑĞ¾ÑĞ¼Ğ°ÑÑ"
)
def format_send_zoom_data():
    return SEND_ZOOM_DATA


ZOOM_DATA_FORMAT = (
    f"ğ | Ğ¤Ğ¾ÑĞ¼Ğ°Ñ:\n"
    f"ââââµ {Key.NAME}: <Ğ¤Ğ°Ğ¼Ğ¸Ğ»Ğ¸Ñ> <Ğ>.<Ğ>.\n"
    f"ââââµ {Key.URL}: <Ğ¡ÑÑĞ»ĞºĞ°>\n"
    f"ââââµ {Key.ID}: <ID>\n"
    f"ââââµ {Key.PWD}: <ĞĞ¾Ğ´>\n"
    f"ââââµ {Key.NOTES}: <ĞÑĞ±Ğ¾Ğ¹ ÑĞµĞºÑÑ, Ğ½Ğ°Ğ¿ÑĞ¸Ğ¼ĞµÑ ÑĞ²Ğ¾Ğ¹ Ğ¼Ğ¸Ğ½Ğ¸-ÑĞ°Ğ½ÑĞ¸Ğº, ÑÑÑĞ»Ñ Ğ½Ğ° ÑÑÑÑĞ¸ Ğ¿Ğ¾ÑĞ½Ğ¾ Ğ¸Ğ»Ğ¸ Ğ² ĞºÑĞ°Ğ¹Ğ½ĞµĞ¼ ÑĞ»ÑÑĞ°Ğµ Ğ¿Ğ¾ÑÑĞ° Ğ¸ Google Drive>\n"
    f"ââââµ ..."
)
def format_zoom_data_format():
    return ZOOM_DATA_FORMAT


MASS_ZOOM_DATA_EXPLAIN = (
    "â ĞĞ±ÑĞ·Ğ°ÑĞµĞ»ÑĞ½Ğ¾ ÑÑĞ°Ğ²Ñ Ğ¿ÑĞµÑĞ¸ĞºÑ Ğ² Ğ½Ğ°ÑĞ°Ğ»Ğµ ÑÑÑĞ¾ĞºĞ¸ (\"ĞĞ¼Ñ:\", \"ÑÑÑĞ»ĞºĞ°:\", \"ĞĞ´:\"), Ğ¼Ğ¾Ğ¶Ğ½Ğ¾ Ñ Ğ±Ğ¾Ğ»ÑÑĞ¾Ğ¹ Ğ±ÑĞºĞ²Ñ\n"
    "ğ¡ ĞĞ¾Ğ¶ĞµÑÑ Ğ¿Ğ¸ÑĞ°ÑÑ Ğ² ÑĞ°Ğ·Ğ½Ğ¾Ğ¹ Ğ¿Ğ¾ÑĞ»ĞµĞ´Ğ¾Ğ²Ğ°ÑĞµĞ»ÑĞ½Ğ¾ÑÑĞ¸ Ğ¸ Ğ¿ÑĞ¾Ğ¿ÑÑĞºĞ°ÑÑ Ğ½ĞµĞºĞ¾ÑĞ¾ÑÑĞµ Ğ¿Ğ¾Ğ»Ñ"
)
def format_mass_zoom_data_explain():
    return MASS_ZOOM_DATA_EXPLAIN


DOESNT_CONTAIN_ZOOM = (
    f"â | Eblan? ĞĞ¾ÑĞ¼Ğ¾ÑÑĞ¸ ÑĞ¾ÑĞ¼Ğ°Ñ, Ğ¿Ğ¾ Ğ½ĞµĞ¼Ñ ÑÑÑ Ğ½Ğ¸ÑÑÑ Ğ½ĞµÑ ğ¤¨\n"
    f"ââââ° ğ¤ ĞĞ»Ğ¾ĞºĞ¸ Ğ±ĞµĞ· Ğ¤ĞĞ Ğ¸Ğ³Ğ½Ğ¾ÑĞ¸ÑÑÑÑÑÑ\n"
    f"ââââ° ğ¤ ĞĞ¼ĞµĞ½Ğ° Ğ±Ğ¾Ğ»ÑÑĞµ {zoom.NAME_LIMIT} ÑĞ¸Ğ¼Ğ²Ğ¾Ğ»Ğ¾Ğ² Ğ¸Ğ³Ğ½Ğ¾ÑĞ¸ÑÑÑÑÑÑ"
)
def format_doesnt_contain_zoom():
    return DOESNT_CONTAIN_ZOOM


YOU_CAN_ADD_MORE = (
    "ğ¤ | Ğ¢Ñ Ğ¼Ğ¾Ğ¶ĞµÑÑ Ğ´Ğ¾Ğ±Ğ°Ğ²Ğ¸ÑÑ Ğ±Ğ¾Ğ»ÑÑĞµ Ğ¸Ğ»Ğ¸ Ğ¿ĞµÑĞµĞ·Ğ°Ğ¿Ğ¸ÑĞ°ÑÑ ÑÑĞ¾-ÑĞ¾, "
    "Ğ¿ÑĞ¾ÑÑĞ¾ Ğ¾ÑĞ¿ÑĞ°Ğ²Ñ ĞµÑÑ Ğ¾Ğ´Ğ½Ğ¾ ÑĞ¾Ğ¾Ğ±ÑĞµĞ½Ğ¸Ğµ Ñ Ğ´Ğ°Ğ½Ğ½ÑĞ¼Ğ¸"
)
def format_you_can_add_more():
    return YOU_CAN_ADD_MORE


VALUE_TOO_BIG = (
    "â | ĞĞ° Ñ Ğ½Ğµ Ğ¿ÑĞ¾ Ğ´Ğ»Ğ¸Ğ½Ñ ÑÑÑ Ğ² ÑĞ²Ğ¾ĞµĞ¹ Ğ¶Ğ¾Ğ¿Ğµ, ÑĞ¾ĞºÑĞ°ÑĞ¸ Ğ´Ğ¾ {limit} ÑĞ¸Ğ¼Ğ²Ğ¾Ğ»Ğ¾Ğ²"
)
def format_value_too_big(limit: int):
    return VALUE_TOO_BIG.format(limit=limit)


ENTER_NAME = (
    "ğ· | ĞÑĞ¿ÑĞ°Ğ²Ñ Ğ½Ğ¾Ğ²Ğ¾Ğµ Ğ¸Ğ¼Ñ ÑÑĞ¾Ğ¹ Ğ·Ğ°Ğ¿Ğ¸ÑĞ¸\n"
    "ââââ° ğ ĞĞ°Ğ¿ÑĞ¸Ğ¼ĞµÑ: ĞĞ±Ğ°Ğ½ÑĞºĞ¾ Ğ¥.Ğ., ĞĞ±Ğ°Ğ½ÑĞºĞ¾ Ğ¥."
)
def format_enter_name():
    return ENTER_NAME


NAME_IN_DATABASE = (
    "â | Ğ­ÑĞ¾ Ğ¸Ğ¼Ñ ÑĞ¶Ğµ Ğ² Ğ±Ğ°ZĞµ"
)
def format_name_in_database():
    return NAME_IN_DATABASE


ENTER_URL = (
    "ğ | ĞÑĞ¿ÑĞ°Ğ²Ñ Ğ½Ğ¾Ğ²ÑÑ ÑÑÑĞ»ĞºÑ Ğ´Ğ»Ñ ÑÑĞ¾Ğ¹ Ğ·Ğ°Ğ¿Ğ¸ÑĞ¸\n"
    "ââââ° ğ ĞĞ°Ğ¿ÑĞ¸Ğ¼ĞµÑ: https://us04web.zoom.us/j/2281337300?pwd=p0s0siMOEpotn0e0CHKOmudilaEBANYA"
)
def format_enter_url():
    return ENTER_URL


ENTER_ID = (
    "ğ | ĞÑĞ¿ÑĞ°Ğ²Ñ Ğ½Ğ¾Ğ²ÑĞ¹ ID Ğ´Ğ»Ñ ÑÑĞ¾Ğ¹ Ğ·Ğ°Ğ¿Ğ¸ÑĞ¸\n"
    "ââââ° ğ ĞĞ°Ğ¿ÑĞ¸Ğ¼ĞµÑ: 2281337300"
)
def format_enter_id():
    return ENTER_ID


ENTER_PWD = (
    "ğ | ĞÑĞ¿ÑĞ°Ğ²Ñ Ğ½Ğ¾Ğ²ÑĞ¹ Ğ¿Ğ°ÑĞ¾Ğ»Ñ Ğ´Ğ»Ñ ÑÑĞ¾Ğ¹ Ğ·Ğ°Ğ¿Ğ¸ÑĞ¸\n"
    "ââââ° ğ ĞĞ°Ğ¿ÑĞ¸Ğ¼ĞµÑ: 0oChKo Ğ¸Ğ»Ğ¸ Ğ´Ñ."
)
def format_enter_pwd():
    return ENTER_PWD

ENTER_NOTES = (
    "ğ | ĞÑĞ¿ÑĞ°Ğ²Ñ Ğ·Ğ°Ğ¼ĞµÑĞºĞ¸ Ğ´Ğ»Ñ ÑÑĞ¾Ğ¹ Ğ·Ğ°Ğ¿Ğ¸ÑĞ¸\n"
    "ââââ° ğ ĞĞ°Ğ¿ÑĞ¸Ğ¼ĞµÑ: ÑĞ²Ğ¾Ğ¹ Ğ¼Ğ¸Ğ½Ğ¸-ÑĞ°Ğ½ÑĞ¸Ğº, ÑÑÑĞ»Ñ Ğ½Ğ° ÑÑÑÑĞ¸ Ğ¿Ğ¾ÑĞ½Ğ¾ Ğ¸Ğ»Ğ¸ Ğ² ĞºÑĞ°Ğ¹Ğ½ĞµĞ¼ ÑĞ»ÑÑĞ°Ğµ Ğ¿Ğ¾ÑÑĞ° Ğ¸ Google Drive"
)
def format_enter_notes():
    return ENTER_NOTES


WILL_BE_ADDED = (
    "â ĞÑĞ´ĞµÑ Ğ´Ğ¾Ğ±Ğ°Ğ²Ğ»ĞµĞ½Ğ¾: {count}"
)
def format_will_be_added(count: int):
    return WILL_BE_ADDED.format(
        count = count,
    )


WILL_BE_OVERWRITTEN = (
    "â» ĞÑĞ´ĞµÑ Ğ¿ĞµÑĞµĞ·Ğ°Ğ¿Ğ¸ÑĞ°Ğ½Ğ¾: {count}"
)
def format_will_be_overwritten(count: int):
    return WILL_BE_OVERWRITTEN.format(
        count = count,
    )


def format_zoom_mass_adding_overview(
    adding: zoom.Entries, 
    overwriting: zoom.Entries
):

    sections: list[str] = []

    if len(adding) > 0:
        entries = common.text.indent(adding.format_compact())
        text = format_will_be_added(len(adding))
        text += "\n"
        text += entries

        sections.append(text)
    
    if len(overwriting) > 0:
        entries = common.text.indent(overwriting.format_compact())
        text = format_will_be_overwritten(len(overwriting))
        text += "\n"
        text += entries

        sections.append(text)

    return "\n".join(sections)


DUMP_EXPLAIN = (
    f"ğ¾ | Ğ¢Ñ Ğ¼Ğ¾Ğ¶ĞµÑÑ Ğ¿ÑĞµĞ¾Ğ±ÑĞ°Ğ·Ğ¾Ğ²Ğ°ÑÑ Ğ²ÑĞµ Ğ´Ğ¾Ğ±Ğ°Ğ²Ğ»ĞµĞ½Ğ½ÑĞµ Ğ·Ğ´ĞµÑÑ Ğ·Ğ°Ğ¿Ğ¸ÑĞ¸ Ğ² ÑĞµĞºÑÑĞ¾Ğ²ÑĞ¹ Ğ²Ğ¸Ğ´ "
    f"Ğ¸ Ğ´Ğ¾Ğ±Ğ°Ğ²Ğ¸ÑÑ Ğ¸Ñ Ğ² Ğ´ÑÑĞ³Ğ¾Ğ¼ Ğ´Ğ¸Ğ°Ğ»Ğ¾Ğ³Ğµ ÑĞµÑĞµĞ· ÑÑĞ½ĞºÑĞ¸Ñ {Text.FROM_TEXT}\n\n"
    f"ğ¡ | ĞÑĞ»Ğ¸ Ğ·Ğ°Ğ¿Ğ¸ÑĞµĞ¹ ÑĞ»Ğ¸ÑĞºĞ¾Ğ¼ Ğ¼Ğ½Ğ¾Ğ³Ğ¾, Ğ¾Ğ½Ğ¸ Ğ¼Ğ¾Ğ³ÑÑ Ğ±ÑÑÑ Ğ¾ÑĞ¿ÑĞ°Ğ²Ğ»ĞµĞ½Ñ Ğ½ĞµÑĞºĞ¾Ğ»ÑĞºĞ¸Ğ¼Ğ¸ ÑĞ¾Ğ¾Ğ±ÑĞµĞ½Ğ¸ÑĞ¼Ğ¸\n\n"
    f"ğ | ĞĞ°Ğ¶Ğ¸Ğ¼Ğ°Ğ¹ {Text.DUMP} ÑÑĞ¾Ğ±Ñ Ğ·Ğ°ÑÑĞ°ÑÑ Ğ±ĞµÑĞµĞ´Ñ"
)
def format_dump_explain():
    return DUMP_EXPLAIN


FINISH = (
    f"ğ | Ğ¤Ğ¿ÑĞ¸Ğ½ÑĞ¸Ğ¿Ğ¸ ÑÑÑ, Ğ¼Ğ¾Ğ¶ĞµÑÑ Ğ¿ĞµÑĞµĞ¿ÑĞ¾Ğ²ĞµÑĞ¸ÑÑ Ğ¸Ğ»Ğ¸ Ğ½Ğ°Ğ¶Ğ°ÑÑ {Text.FINISH}"
)
def format_finish():
    return FINISH


NO_UPDATES = (
    "ğ¤ ĞĞ±Ğ½Ğ¾Ğ²Ğ»ĞµĞ½Ğ¸Ğ¹ Ğ½Ğµ Ğ½Ğ°Ğ¹Ğ´ĞµĞ½Ğ¾"
)
def format_no_updates():
    return NO_UPDATES

UPDATES_SENT = (
    "â ĞĞ±Ğ½Ğ¾Ğ²Ğ»ĞµĞ½Ğ¸Ñ Ğ½Ğ°Ğ¹Ğ´ĞµĞ½Ñ, Ğ±ÑĞ´ÑÑ Ğ¾ÑĞ¿ÑĞ°Ğ²Ğ»ĞµĞ½Ñ Ğ² Ğ½Ğ¾Ğ²Ğ¾Ğ¼ ÑĞ¾Ğ¾Ğ±ÑĞµĞ½Ğ¸Ğ¸"
)
def format_updates_sent():
    return UPDATES_SENT

UPDATES_TIMEOUT = (
    "ĞÑĞµĞ²ÑÑĞµĞ½Ğ¾ Ğ²ÑĞµĞ¼Ñ Ğ¾Ğ±Ğ½Ğ¾Ğ²Ğ»ĞµĞ½Ğ¸Ñ, Ğ¿Ğ¾Ğ²ÑĞ¾ÑĞ¸ Ğ¿Ğ¾Ğ¿ÑÑĞºÑ Ğ¿Ğ¾Ğ·Ğ¶Ğµ"
)
def format_updates_timeout():
    return UPDATES_TIMEOUT


TOO_FAST_RETRY_AFTER = (
    "ĞĞµĞµ ĞºÑĞ´Ğ° ÑĞ¾ÑĞ¾Ğ¿Ğ¸ÑÑÑÑ, Ğ¿Ğ¾Ğ²ÑĞ¾ÑĞ¸ ÑĞµÑĞµĞ· {secs}"
)
def format_too_fast_retry_after(secs: int):
    fmt_secs = f"{secs} Ñ."

    return TOO_FAST_RETRY_AFTER.format(
        secs = fmt_secs
    )


GROUP_CHANGED_IN_SC_TYPE = (
    "ĞÑÑĞ¿Ğ¿Ğ° {change} Ğ² {sc_type}"
)
def format_group_changed_in_sc_type(
    change: compare.ChangeType,
    sc_type: schedule.Type
):
    if change == compare.ChangeType.APPEARED:
        repr_change = "Ğ¿Ğ¾ÑĞ²Ğ¸Ğ»Ğ°ÑÑ"
    elif change == compare.ChangeType.CHANGED:
        repr_change = "Ğ¸Ğ·Ğ¼ĞµĞ½Ğ¸Ğ»Ğ°ÑÑ"

    if sc_type == schedule.Type.DAILY:
        repr_sc_type = "Ğ´Ğ½ĞµĞ²Ğ½Ğ¾Ğ¼"
    elif sc_type == schedule.Type.WEEKLY:
        repr_sc_type = "Ğ½ĞµĞ´ĞµĞ»ÑĞ½Ğ¾Ğ¼"
    
    return GROUP_CHANGED_IN_SC_TYPE.format(
        change  = repr_change,
        sc_type = repr_sc_type
    )


REPLIED_TO_SCHEDULE_MESSAGE = (
    "ğ ĞĞ¾ÑĞ»ĞµĞ´Ğ½ĞµĞµ {sc_type} Ğ² Ğ¾ÑĞ²ĞµÑĞ½Ğ¾Ğ¼ ÑĞ¾Ğ¾Ğ±ÑĞµĞ½Ğ¸Ğ¸"
)
def format_replied_to_schedule_message(sc_type: schedule.TYPE_LITERAL):
    if sc_type == schedule.Type.DAILY:
        repr_sc_type = "Ğ´Ğ½ĞµĞ²Ğ½Ğ¾Ğµ"
    elif sc_type == schedule.Type.WEEKLY:
        repr_sc_type = "Ğ½ĞµĞ´ĞµĞ»ÑĞ½Ğ¾Ğµ"

    return REPLIED_TO_SCHEDULE_MESSAGE.format(
        sc_type = repr_sc_type
    )


FAILED_REPLY_TO_SCHEDULE_MESSAGE = (
    "ğ¥º ĞĞµ ÑĞ´Ğ°Ğ»Ğ¾ÑÑ Ğ¾ÑĞ²ĞµÑĞ¸ÑÑ Ğ½Ğ° Ğ¿Ğ¾ÑĞ»ĞµĞ´Ğ½ĞµĞµ {sc_type} ÑĞ°ÑĞ¿Ğ¸ÑĞ°Ğ½Ğ¸Ğµ, "
    f"Ğ½Ğ°ÑĞ¾Ğ´Ğ¸ ĞµĞ³Ğ¾ ÑĞµÑĞµĞ· Ğ¿Ğ¾Ğ¸ÑĞº Ğ¸Ğ»Ğ¸ Ğ·Ğ°Ğ¿ÑĞ¾ÑĞ¸ ÑĞµÑĞµĞ· ĞºĞ½Ğ¾Ğ¿ĞºÑ {Text.RESEND}"
)
def format_failed_reply_to_schedule_message(sc_type: schedule.TYPE_LITERAL):
    if sc_type == schedule.Type.DAILY:
        repr_sc_type = "Ğ´Ğ½ĞµĞ²Ğ½Ğ¾Ğµ"
    elif sc_type == schedule.Type.WEEKLY:
        repr_sc_type = "Ğ½ĞµĞ´ĞµĞ»ÑĞ½Ğ¾Ğµ"

    return FAILED_REPLY_TO_SCHEDULE_MESSAGE.format(
        sc_type = repr_sc_type
    )

DETAILED_COMPARE_NOT_SHOWN = (
    "(Ğ¸Ğ·Ğ¼ĞµĞ½Ğ¸Ğ»Ğ°ÑÑ Ğ´Ğ°ÑĞ°, Ğ´ĞµÑĞ°Ğ»ÑĞ½ÑĞµ Ğ¸Ğ·Ğ¼ĞµĞ½ĞµĞ½Ğ¸Ñ Ğ¿Ğ¾Ğ´ â¢ Ğ½Ğµ Ğ¿Ğ¾ĞºĞ°Ğ·Ğ°Ğ½Ñ)"
)
def format_detailed_compare_not_shown():
    return DETAILED_COMPARE_NOT_SHOWN