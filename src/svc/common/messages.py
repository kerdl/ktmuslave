from __future__ import annotations
from typing import Any
from src.data.settings import Settings

from src.svc import common
from src.data import zoom
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


PYTHON_VALUE_REPR = {
    True:  "да",
    False: "нет",
    None:  "н/а"
}

def value_repr(value: Any) -> str:
    if type(value) == int:
        return value

    return PYTHON_VALUE_REPR.get(value) or value


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
    "8==o🤮 trace:\n"
    "{trace}\n"
    "8==o🤮 back_trace:\n"
    "{back_trace}\n"
    "8==o🤮 last_bot_message:\n"
    "   {last_bot_message}\n"
    "8==o🤮 settings:\n"
    "   {settings}"
)
def format_debug(trace: list[State], back_trace: list[State], last_bot_message: common.CommonBotMessage, settings: Settings):
    
    def fmt_trace(trace: list[State]):
        return "\n".join([f"   {state.space}:{state.anchor}" for state in trace])
    
    trace_str = fmt_trace(trace)
    back_trace_str = fmt_trace(back_trace)

    last_bot_message = "впизду этот мессадж он огромный как член у меня в жопе"
    settings         = "похуй"

    return DEBUG.format(
        trace            = trace_str,
        back_trace       = back_trace_str,
        last_bot_message = last_bot_message,
        settings         = settings
    )


CANT_PRESS_OLD_BUTTONS = (
    "Пососи 😒 Вот тебе новое сообщение, "
    "на нём и тыкай куда тебе надо"
)
def format_cant_press_old_buttons():
    return CANT_PRESS_OLD_BUTTONS


EMPTY_PAGE = (
    "🤔 | Пока сюда нихуя не завезли"
)
def format_empty_page():
    return EMPTY_PAGE


PRESS_BEGIN = (
    f"👇 Нажимай {Text.BEGIN}, хуле"
)
def format_press_begin():
    return PRESS_BEGIN


GROUPS = (
    "🖕 | Группы в расписании:\n"
    "   ╰ {groups}"
)
def format_groups(groups: list[str]):
    groups_str = ", ".join(groups)
    return GROUPS.format(groups=groups_str)


MENTION_ME = (
    "😮 Ещё упомяни меня: {mention}, иначе не увижу 😮"
)
def format_mention_me(mention: str):
    return MENTION_ME.format(mention=mention)


REPLY_TO_ME = (
    "😮 Ещё ↩️ ответь ↩️ на это сообщение, иначе не увижу 😮"
)
def format_reply_to_me():
    return REPLY_TO_ME


CHAT_WILL_MIGRATE = (
    "🤔 Из-за этого, эта группа станет супергруппой 🤔\n"
    "Читай подробнее здесь: https://teleme.io/articles/turn_a_telegram_group_into_a_supergroup?hl=ru"
)
def format_chat_will_migrate():
    return CHAT_WILL_MIGRATE


PAGE_NUM = (
    "📄 | Страница {current}/{last}"
)
def format_page_num(current: int, last: int):
    return PAGE_NUM.format(current=current, last=last)


PRESS_BUTTONS_TO_CHANGE = (
    "👇 | Нажми на параметр, чтобы его изменить"
)
def format_press_buttons_to_change():
    return PRESS_BUTTONS_TO_CHANGE


NO_TEXT = (
    "❌ | Ну ты быдло, тут нет текста"
)
def format_no_text():
    return NO_TEXT


CURRENT_VALUE = (
    "📝 | Текущее значение: {value}"
)
def format_current_value(value: Any):
    return CURRENT_VALUE.format(
        value = value_repr(value)
    )


#### Full messages for specific states ####

WELCOME =  (
    "👨🏿 Буду пиздить расписание "
    "с 🌐 ktmu-sutd.ru 🌐 "
    "и делиться с {count}"
)
def format_welcome(is_group_chat: bool):
    if is_group_chat:
        return WELCOME.format(count="вами")
    else:
        return WELCOME.format(count="тобой")


GROUP_INPUT = (
    "💅 | Напиши свою группу\n"
    "   ╰ Формат: 1кдд69, 1-кдд-69, 1КДД69, 1-КДД-69\n"
    "   ╰ Можешь написать ту, которой нет в списке"
)
def format_group_input():
    return GROUP_INPUT


UNKNOWN_GROUP = (
    "❓ | {group} пока нет, всё равно поставить?"
)
def format_unknown_group(group: str):
    return UNKNOWN_GROUP.format(group=group)


INVALID_GROUP = (
    "❌ | Эта хуйня не подходит под формат: 1кдд69, 1-кдд-69, 1КДД69, 1-КДД-69\n"
    "Напиши ещё раз по формату"
)
def format_invalid_group():
    return INVALID_GROUP


BROADCAST = (
    "🔔 | Хочешь получать здесь рассылку расписания?"
)
def format_broadcast():
    return BROADCAST


DO_PIN = (
    "📌 | Хочешь шоб я закреплял рассылку расписания?"
)
def format_do_pin():
    return DO_PIN


RECOMMEND_PIN = (
    "📌 | Я могу закреплять рассылку расписания, "
    "но сейчас у меня нет прав"
)
def format_recommend_pin():
    return RECOMMEND_PIN


PERMIT_PIN_VK = (
    "🚽 | Если хочешь заркеп, назначь меня админом, "
    "либо пропусти если поебать"
)
PERMIT_PIN_TG = (
    "🚽 | Если хочешь закреп, назначь меня админом с правом "
    "\"Закрепление сообщений\", либо пропусти если поебать"
)
def format_permit_pin(src: common.MESSENGER_SOURCE):
    if src == common.Source.VK:
        return PERMIT_PIN_VK
    if src == common.Source.TG:
        return PERMIT_PIN_TG


CANT_PIN_VK = (
    "Нет у меня нихуя, перепроверь мою админку"
)
CANT_PIN_TG = (
    "Нет у меня нихуя, перепроверь моё право \"Закрепление сообщений\""
)
def format_cant_pin(src: common.MESSENGER_SOURCE):
    if src == common.Source.VK:
        return CANT_PIN_VK
    if src == common.Source.TG:
        return CANT_PIN_TG


RECOMMEND_ADDING_ZOOM = (
    "📝 | Ты можешь добавить ссылки, ID, пароли Zoom, "
    "чтобы они показывались в расписании"
)
def format_recommend_adding_zoom():
    return RECOMMEND_ADDING_ZOOM


ZOOM_ADDING_TYPES_EXPLAIN = (
    f"{Text.FROM_TEXT} - пересылаешь сообщения с ссылками, "
    f"автоматом берёт все данные\n"
    f"{Text.MANUALLY} - добавляешь, изменяешь, удаляешь "
    f"по отдельности"
)
def format_zoom_adding_types_explain():
    return ZOOM_ADDING_TYPES_EXPLAIN


FORWARD_ZOOM_DATA = (
    "💬 | Перешли мне сообщения с данными Zoom"
)
SEND_ZOOM_DATA = (
    "💬 | Скопируй сообщения с данными Zoom "
    "и отправь мне в текстовом виде"
)
def format_send_zoom_data(src: common.MESSENGER_SOURCE, is_group_chat: bool):
    if (src == common.Source.VK) or (src == common.Source.TG and not is_group_chat):
        return FORWARD_ZOOM_DATA
    else:
        return SEND_ZOOM_DATA


ZOOM_DATA_FORMAT = (
    "📝 | Формат:\n"
    "   ↵ <Фамилия> <Имя> <Отчество> [ИЛИ] <Фамилия> <И>.<О>.\n"
    "   ↵ <Ссылка>\n"
    "   ↵ <ID>\n"
    "   ↵ <Пароль>\n"
    "   ↵ [ПУСТАЯ СТРОКА]\n"
    "   ↵ ..."
)
def format_zoom_data_format():
    return ZOOM_DATA_FORMAT


DOESNT_CONTAIN_ZOOM = (
    "❌ | Eblan? Посмотри формат, по нему тут нихуя нет 🤨\n"
    "   ╰ 🤔 Блоки без ФИО игнорируются"
)
def format_doesnt_contain_zoom():
    return DOESNT_CONTAIN_ZOOM


YOU_CAN_ADD_MORE = (
    "🤓 | Ты можешь добавить больше или перезаписать что-то, "
    "просто отправь ещё одно сообщение с данными"
)
def format_you_can_add_more():
    return YOU_CAN_ADD_MORE


ENTER_NAME = (
    "🐷 | Отправь новое имя этой записи\n"
    "   ╰ 👉 Например: Ебанько Х.Й., Ебанько Х."
)
def format_enter_name():
    return ENTER_NAME


NAME_IN_DATABASE = (
    "❌ | Это имя уже в баZе"
)
def format_name_in_database():
    return NAME_IN_DATABASE


ENTER_URL = (
    "🌐 | Отправь новую ссылку для этой записи\n"
    "   ╰ 👉 Например: https://us04web.zoom.us/j/2281337300?pwd=p0s0siMOEpotn0e0CHKOmudilaEBANYA"
)
def format_enter_url():
    return ENTER_URL


ENTER_ID = (
    "📍 | Отправь новый ID для этой записи\n"
    "   ╰ 👉 Например: 2281337300"
)
def format_enter_id():
    return ENTER_ID


ENTER_PWD = (
    "🔑 | Отправь новый пароль для этой записи\n"
    "   ╰ 👉 Например: 0oChKo или др."
)
def format_enter_pwd():
    return ENTER_PWD


WILL_BE_ADDED = (
    "❇ Будет добавлено: {count}"
)
def format_will_be_added(count: int):
    return WILL_BE_ADDED.format(
        count = count,
    )


WILL_BE_OVERWRITTEN = (
    "♻ Будет перезаписано: {count}"
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


ZOOM_DATA_WARNING = (
    "❗ | Проверь, чтобы у преподов были "
    "точно такие же имена, как в расписании на ktmu-sutd.ru\n"
    "   ╰ ❌ | Ебанько Хуйловик Йоба\n"
    "   ╰ ✅ | Ебанько Х.Й.\n"
    "❗ | Проверь ссылки, чтобы они случайно "
    "не были обрезаны (еврейская древняя пословица)\n"
    "   ╰ ❌ | posos.us/p0lizhiM0E...\n"
    "   ╰ ✅ | posos.us/p0lizhiM0Epotn0eOCHK0"
)
def format_zoom_data_warning():
    return ZOOM_DATA_WARNING


FINISH = (
    f"👍 | Фпринципи фсё, можешь перепроверить или нажать {Text.FINISH}"
)
def format_finish():
    return FINISH


NO_UPDATES = (
    "🤔 Обновлений не найдено"
)
def format_no_updates():
    return NO_UPDATES

UPDATES_SENT = (
    "✅ Обновления найдены, отправлены в новом сообщении"
)

def format_updates_sent():
    return UPDATES_SENT


TOO_FAST_RETRY_AFTER = (
    "Лее куда торопишься, повтори через {secs}"
)
def format_too_fast_retry_after(secs: int):
    fmt_secs = f"{secs} с."

    return TOO_FAST_RETRY_AFTER.format(
        secs = fmt_secs
    )