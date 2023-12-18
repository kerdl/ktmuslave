from __future__ import annotations
from typing import Any, Optional
from src.data.settings import Settings

from src.svc import common
from src.data import zoom, format as fmt, schedule
from src.data.schedule import compare
from src.parse.zoom import Key
from src.svc.common.states import State
from src.svc.common.keyboard import Text, Payload


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
    "8==o🤮 trace:\n"
    "{trace}\n"
    "8==o🤮 back_trace:\n"
    "{back_trace}\n"
)
def format_debug(trace: list[State], back_trace: list[State], last_bot_message: common.CommonBotMessage, settings: Settings):
    
    def fmt_trace(trace: list[State]):
        return "\n".join([f"   {state.space}:{state.anchor}" for state in trace])
    
    trace_str = fmt_trace(trace)
    back_trace_str = fmt_trace(back_trace)

    return DEBUG.format(
        trace            = trace_str,
        back_trace       = back_trace_str,
    )


CANT_PRESS_OLD_BUTTONS = (
    "Пососи 😒 Вот тебе новое сообщение, "
    "на нём и тыкай куда тебе надо"
)
def format_cant_press_old_buttons():
    return CANT_PRESS_OLD_BUTTONS

SENT_AS_NEW_MESSAGE = (
    "Отправлено новым сообщением"
)
def format_sent_as_new_message():
    return SENT_AS_NEW_MESSAGE

EMPTY_PAGE = (
    "🤔 | Пока сюда нихуя не завезли"
)
def format_empty_page():
    return EMPTY_PAGE


NO_MORE_PAGES = (
    "■ Дальше ничего нет"
)
def format_no_more_pages() -> str:
    return NO_MORE_PAGES


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
        value = fmt.value_repr(value)
    )


CANT_CONNECT_TO_SCHEDULE_SERVER = (
    f"🤔 | Невозможно подключиться к серверу расписания"
)
def format_cant_connect_to_schedule_server() -> str:
    return CANT_CONNECT_TO_SCHEDULE_SERVER


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
    "🔔 | Хочешь получать здесь рассылку, когда у группы меняется расписание?"
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
def format_permit_pin(src: common.MESSENGER_OR_EVT_SOURCE):
    if src == common.Source.VK:
        return PERMIT_PIN_VK
    if src == common.Source.TG:
        return PERMIT_PIN_TG


CANT_PIN_VK = (
    "❌ Нет у меня нихуя, перепроверь мою админку"
)
CANT_PIN_TG = (
    "❌ Нет у меня нихуя, перепроверь моё право \"Закрепление сообщений\""
)
def format_cant_pin(src: common.MESSENGER_OR_EVT_SOURCE):
    if src == common.Source.VK:
        return CANT_PIN_VK
    if src == common.Source.TG:
        return CANT_PIN_TG


RECOMMEND_ADDING_ZOOM = (
    "📝 | Ты можешь добавить ссылки, ID, пароли Zoom и заметки, "
    "чтобы они показывались в расписании"
)
def format_recommend_adding_zoom():
    return RECOMMEND_ADDING_ZOOM


CHOOSE_ADDING_TYPE = (
    "📝 | Выбери как ты хочешь добавить запись/записи"
)
def format_choose_adding_type():
    return CHOOSE_ADDING_TYPE


ZOOM_ADD_FROM_TEXT_EXPLAIN = (
    f"{Text.FROM_TEXT} - пишешь одно большое сообщение по формату, "
    f"автоматом берёт все данные"
)
def format_zoom_add_from_text_explain():
    return ZOOM_ADD_FROM_TEXT_EXPLAIN


ZOOM_ADD_MANUALLY_INIT_EXPLAIN = (
    f"{Text.MANUALLY} - добавляешь, изменяешь, удаляешь "
    f"по отдельности"
)
def format_zoom_add_manually_init_explain():
    return ZOOM_ADD_MANUALLY_INIT_EXPLAIN


ZOOM_ADD_MANUALLY_HUB_EXPLAIN = (
    f"{Text.MANUALLY} - добавить новое имя вручную"
)
def format_zoom_add_manually_hub_explain():
    return ZOOM_ADD_MANUALLY_HUB_EXPLAIN


SEND_ZOOM_DATA = (
    "💬 | Напиши сообщение с данными Zoom по формату"
)
def format_send_zoom_data():
    return SEND_ZOOM_DATA


ZOOM_DATA_FORMAT = (
    f"📝 | Формат:\n"
    f"   ↵ {Key.NAME}: <Фамилия> <И>.<О>.\n"
    f"   ↵ {Key.URL}: <Ссылка>\n"
    f"   ↵ {Key.ID}: <ID>\n"
    f"   ↵ {'/'.join(Key.PWD)}: <Код>\n"
    f"   ↵ {Key.NOTES}: <Любой текст, например твой мини-фанфик, ссыль на фурри порно или в крайнем случае почта и Google Drive>\n"
    f"   ↵ ..."
)
def format_zoom_data_format():
    return ZOOM_DATA_FORMAT


ZOOM_EXAMPLE = (
    "🔖 | Например:\n"
    "имя: Ебанько Х.Й.\n"
    "ссылка: https://pornhub.com\n"
    "Ид: 22813376969\n"
    "Код: 0oChK0\n"
    "\n"
    "имя: Говновоз Ж.\n"
    "Ид: 22813376969\n"
    "заметки: выебывается на парах"
)
def format_zoom_example():
    return ZOOM_EXAMPLE


MASS_ZOOM_DATA_EXPLAIN = (
    "❗ Обязательно ставь префикс в начале строки (\"Имя:\", \"ссылка:\", \"Ид:\"), можно с большой буквы\n"
    "💡 Можешь писать в разной последовательности и пропускать некоторые поля"
)
def format_mass_zoom_data_explain():
    return MASS_ZOOM_DATA_EXPLAIN


DOESNT_CONTAIN_ZOOM = (
    f"❌ | Eblan? Посмотри формат, по нему тут нихуя нет 🤨\n"
    f"   ╰ 🤔 Блоки без ФИО игнорируются\n"
    f"   ╰ 🤔 Имена больше {zoom.NAME_LIMIT} символов игнорируются"
)
def format_doesnt_contain_zoom():
    return DOESNT_CONTAIN_ZOOM


YOU_CAN_ADD_MORE = (
    "🤓 | Ты можешь добавить больше или перезаписать что-то, "
    "просто отправь ещё одно сообщение с данными"
)
def format_you_can_add_more():
    return YOU_CAN_ADD_MORE


VALUE_TOO_BIG = (
    "❌ | Да я не про длину хуя в твоей жопе, сократи до {limit} символов"
)
def format_value_too_big(limit: int):
    return VALUE_TOO_BIG.format(limit=limit)


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

ENTER_NOTES = (
    "📝 | Отправь заметки для этой записи\n"
    "   ╰ 👉 Например: твой мини-фанфик, ссыль на фурри порно или в крайнем случае почта и Google Drive"
)
def format_enter_notes():
    return ENTER_NOTES


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


DUMP_EXPLAIN = (
    f"💾 | Ты можешь преобразовать все добавленные здесь записи в текстовый вид "
    f"и добавить их в другом диалоге через функцию {Text.FROM_TEXT}\n\n"
    f"💡 | Если записей слишком много, они могут быть отправлены несколькими сообщениями\n\n"
    f"👇 | Нажимай {Text.DUMP} чтобы засрать беседу"
)
def format_dump_explain():
    return DUMP_EXPLAIN


FINISH = (
    f"👍 | Фпринципи фсё, можешь перепроверить или нажать {Text.FINISH}"
)
def format_finish():
    return FINISH


GROUP_SETTING_EXPLAIN = (
    f"{Text.GROUP} - настройки группы, с которой работает негр"
)
BROADCAST_SETTING_EXPLAIN = (
    f"{Text.BROADCAST} - получишь ли ты новое сообщение при обновлении расписания для установленной группы"
)
PIN_SETTING_EXPLAIN = (
    f"{Text.PIN} - закрепит ли негр рассылку расписания"
)
ZOOM_SETTING_EXPLAIN = (
    f"{Text.ZOOM} - настройки данных преподов: их имена, ссылки, ID, пароли и заметки, которые показываются в расписании"
)
RESET_SETTING_EXPLAIN = (
    f"{Text.RESET} - сбросить все данные и начать первоначальную настройку"
)
def format_settings_main(is_group_chat: bool) -> str:
    text = ""

    text += f"{GROUP_SETTING_EXPLAIN}\n"
    text += "\n"
    text += f"{BROADCAST_SETTING_EXPLAIN}\n"
    text += "\n"
    if is_group_chat:
        text += f"{PIN_SETTING_EXPLAIN}\n"
        text += "\n" 
    text += f"{ZOOM_SETTING_EXPLAIN}\n"
    text += "\n"
    text += f"{RESET_SETTING_EXPLAIN}\n"

    return text


RESET_EXPLAIN = (
    f"🗑️ | Это сбросит все настройки + Zoom данные и потребует пройти начальную настройку\n\n"
    f"👇 | Нажимай {Text.RESET} чтобы у тебя тоже была болезнь Альцгеймера"
)
def format_reset_explain() -> str:
    return RESET_EXPLAIN


NO_SCHEDULE = (
    f"🤔 Твоей группы нет в этом расписании"
)
def format_no_schedule() -> str:
    return NO_SCHEDULE


SCHEDULE_FOOTER = (
    "⏱ Последнее обновление: {last_update}\n"
    "✉ Период автообновления: {update_period} мин"
)
def format_schedule_footer(last_update: Any, update_period: Any) -> str:
    return SCHEDULE_FOOTER.format(
        last_update=last_update,
        update_period=update_period
    )


NO_UPDATES = (
    "🤔 Обновлений не найдено"
)
def format_no_updates():
    return NO_UPDATES

UPDATES_SENT = (
    "✅ Обновления найдены, будут отправлены в новом сообщении"
)
def format_updates_sent():
    return UPDATES_SENT

UPDATES_TIMEOUT = (
    "Превышено время обновления, повтори попытку позже"
)
def format_updates_timeout():
    return UPDATES_TIMEOUT


TOO_FAST_RETRY_AFTER = (
    "Лее куда торопишься, повтори через {secs}"
)
def format_too_fast_retry_after(secs: int):
    fmt_secs = f"{secs} с."

    return TOO_FAST_RETRY_AFTER.format(
        secs = fmt_secs
    )


NOT_IMPLEMENTED_ERROR = (
    "🤔 Функция не реализована"
)
def format_not_implemented_error() -> str:
    return NOT_IMPLEMENTED_ERROR


GROUP_CHANGED_IN_SC_TYPE = (
    "Группа {change} в {sc_type}"
)
def format_group_changed_in_sc_type(
    change: compare.ChangeType,
    sc_type: schedule.Type
):
    if change == compare.ChangeType.APPEARED:
        repr_change = "появилась"
    elif change == compare.ChangeType.CHANGED:
        repr_change = "изменилась"

    if sc_type == schedule.Type.DAILY:
        repr_sc_type = "дневном"
    elif sc_type == schedule.Type.WEEKLY:
        repr_sc_type = "недельном"
    
    return GROUP_CHANGED_IN_SC_TYPE.format(
        change  = repr_change,
        sc_type = repr_sc_type
    )


REPLIED_TO_SCHEDULE_MESSAGE = (
    "👆 Последнее {sc_type} в ответном сообщении"
)
def format_replied_to_schedule_message(sc_type: schedule.TYPE_LITERAL):
    if sc_type == schedule.Type.DAILY:
        repr_sc_type = "дневное"
    elif sc_type == schedule.Type.WEEKLY:
        repr_sc_type = "недельное"

    return REPLIED_TO_SCHEDULE_MESSAGE.format(
        sc_type = repr_sc_type
    )


FAILED_REPLY_TO_SCHEDULE_MESSAGE = (
    "🥺 Не удалось ответить на последнее {sc_type} расписание, "
    f"находи его через поиск или запроси через кнопку {Text.RESEND}"
)
def format_failed_reply_to_schedule_message(sc_type: schedule.TYPE_LITERAL):
    if sc_type == schedule.Type.DAILY:
        repr_sc_type = "дневное"
    elif sc_type == schedule.Type.WEEKLY:
        repr_sc_type = "недельное"

    return FAILED_REPLY_TO_SCHEDULE_MESSAGE.format(
        sc_type = repr_sc_type
    )

DETAILED_COMPARE_NOT_SHOWN = (
    "(изменилась дата, детальные изменения под • не показаны)"
)
def format_detailed_compare_not_shown():
    return DETAILED_COMPARE_NOT_SHOWN