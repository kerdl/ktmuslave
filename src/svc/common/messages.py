from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING
from dotenv import get_key

from src import defs, ENV_PATH
from src.data.settings import Settings
from src.svc import common
from src.data import zoom, format as fmt, schedule
from src.data.schedule import compare
from src.parse.zoom import Key
from src.svc.common.states import State
from src.svc.common.keyboard import Text, Payload


if TYPE_CHECKING:
    from src.data.settings import MODE_LITERAL


DEBUGGING = True


class Builder:
    def __init__(
        self,
        separator: str = "\n\n",
    ) -> None:
        self.separator = separator
        self.components: list[str] = []

    def add(self, text: str) -> Builder:
        if text == "" or text is None:
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
    "Вот тебе новое сообщение, "
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
    "🤔 | Пусто. Можешь добавить записи с помощью кнопки ниже."
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
    "📋 | Группы в расписании:\n"
    "  └ {groups}"
)
def format_groups(groups: list[str]):
    groups_str = ", ".join(groups)
    return GROUPS.format(groups=groups_str)

TEACHERS = (
    "📋 | Преподы в расписании:\n"
    "  └ {teachers}"
)
def format_teachers(teachers: list[str]):
    teachers_str = ", ".join(teachers)
    return TEACHERS.format(teachers=teachers_str)


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
    "❌ | Тут нет текста"
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

CHOOSE_SCHEDULE_MODE = (
    "⛓️ | Выбери режим расписания"
)
def format_choose_schedule_mode():
    return CHOOSE_SCHEDULE_MODE

GROUP_INPUT = (
    "💅 | Напиши свою группу\n"
    "📌 | Формат:\n"
    "  └ 1кдд69\n"
    "  └ 1-кдд-69\n"
    "  └ 1КДД69\n"
    "  └ 1-КДД-69\n"
)
def format_group_input():
    return GROUP_INPUT

TEACHER_INPUT = (
    "💅 | Напиши свою фамилию\n"
    "📌 | Формат:\n"
    "  └ Говновоз Ж.Д.\n"
    "  └ Говновоз жд\n"
    "  └ Говновоз\n"
)
def format_teacher_input():
    return TEACHER_INPUT


UNKNOWN_IDENTIFIER = (
    "❓ | {identifier} пока нет, всё равно поставить?"
)
def format_unknown_identifier(identifier: str):
    return UNKNOWN_IDENTIFIER.format(identifier=identifier)


INVALID_GROUP = (
    "❌ | Эта хуйня не подходит под формат:\n"
    "  └ 1кдд69\n"
    "  └ 1-кдд-69\n"
    "  └ 1КДД69\n"
    "  └ 1-КДД-69\n"
    "💡 | Напиши ещё раз по формату"
)
def format_invalid_group():
    return INVALID_GROUP


INVALID_TEACHER = (
    "❌ | Эта хуйня не подходит под формат:\n"
    "  └ Говновоз Ж.Д.\n"
    "  └ Говновоз жд\n"
    "  └ Говновоз\n"
    "💡 | Напиши ещё раз по формату"
)
def format_invalid_teacher():
    return INVALID_TEACHER


FORBIDDEN_FORMAT_TEACHER = (
    "❌ | Препода нет в расписании, такой формат использовать нельзя"
    "💡 | Используй:\n"
    "  └ Говновоз Ж.Д.\n"
    "  └ Говновоз жд\n"
)
def format_forbidden_format_teacher():
    return FORBIDDEN_FORMAT_TEACHER


BROADCAST = (
    "🔔 | Хочешь получать здесь рассылку, когда у группы меняется расписание?"
)
def format_broadcast():
    return BROADCAST


TCHR_BROADCAST = (
    "🔔 | Хочешь получать здесь рассылку, когда у препода меняется расписание?"
)
def format_tchr_broadcast():
    return TCHR_BROADCAST


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
    "❌ Нихуя нет, перепроверь мою админку"
)
CANT_PIN_TG = (
    "❌ Нихуя нет, перепроверь моё право \"Закрепление сообщений\""
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
    f"{Text.FROM_TEXT} - пишешь одно сообщение по формату, "
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
    f"   ↵ {Key.NOTES}: <Любой текст>\n"
    f"   ↵ ..."
)
def format_zoom_data_format():
    return ZOOM_DATA_FORMAT


TCHR_ZOOM_DATA_FORMAT = (
    f"📝 | Формат:\n"
    f"   ↵ {Key.NAME}: <Имя записи>\n"
    f"   ↵ {Key.URL}: <Ссылка>\n"
    f"   ↵ {Key.ID}: <ID>\n"
    f"   ↵ {'/'.join(Key.PWD)}: <Код>\n"
    f"   ↵ {Key.HOST_KEY}: <Ключ хоста>\n"
    f"   ↵ {Key.NOTES}: <Любой текст>\n"
    f"   ↵ ..."
)
def format_tchr_zoom_data_format():
    return TCHR_ZOOM_DATA_FORMAT


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


TCHR_ZOOM_EXAMPLE = (
    "🔖 | Например:\n"
    "имя: Для 1КДД69\n"
    "ссылка: https://pornhub.com\n"
    "Ид: 22813376969\n"
    "Код: 0oChK0\n"
    "ключ: h0stk3y\n"
    "\n"
    "Имя: Доп. занятия\n"
    "Ид: 22813376969\n"
    "заметки: впускать только 2КДД69"
)
def format_tchr_zoom_example():
    return TCHR_ZOOM_EXAMPLE


MASS_ZOOM_DATA_EXPLAIN = (
    "❗ Обязательно ставь префикс в начале строки, регистр неважен\n"
    "💡 Можешь писать в разной последовательности и пропускать некоторые поля"
)
def format_mass_zoom_data_explain():
    return MASS_ZOOM_DATA_EXPLAIN


DOESNT_CONTAIN_ZOOM = (
    f"❌ | По формату тут ничего нет\n"
    f"  └ 💡 Блоки без ФИО игнорируются\n"
    f"  └ 💡 Имена больше {zoom.NAME_LIMIT} символов игнорируются"
)
def format_doesnt_contain_zoom():
    return DOESNT_CONTAIN_ZOOM


TCHR_DOESNT_CONTAIN_ZOOM = (
    f"❌ | По формату тут ничего нет\n"
    f"  └ 💡 Блоки без имён игнорируются\n"
    f"  └ 💡 Имена больше {zoom.NAME_LIMIT} символов игнорируются"
)
def format_tchr_doesnt_contain_zoom():
    return TCHR_DOESNT_CONTAIN_ZOOM


YOU_CAN_ADD_MORE = (
    "🤓 | Ты можешь добавить больше или перезаписать что-то, "
    "просто отправь ещё одно сообщение с данными"
)
def format_you_can_add_more():
    return YOU_CAN_ADD_MORE


VALUE_TOO_BIG = (
    "❌ | Сократи до {limit} символов"
)
def format_value_too_big(limit: int):
    return VALUE_TOO_BIG.format(limit=limit)


ENTER_NAME = (
    "🐷 | Отправь новое имя этой записи\n"
    "  └ 👉 Например: Ебанько Х.Й., Ебанько Х."
)
def format_enter_name():
    return ENTER_NAME


TCHR_ENTER_NAME = (
    "🐷 | Отправь новое имя этой записи\n"
    "  └ 👉 Например: Для 1КДД69, Доп. занятия"
)
def format_tchr_enter_name():
    return TCHR_ENTER_NAME


NAME_IN_DATABASE = (
    "❌ | Это имя уже в баZе"
)
def format_name_in_database():
    return NAME_IN_DATABASE


ENTER_URL = (
    "🌐 | Отправь новую ссылку для этой записи\n"
    "  └ 👉 Например: https://us04web.zoom.us/j/2281337300?pwd=p0s0siMOEpotn0e0CHKOmudilaEBANYA"
)
def format_enter_url():
    return ENTER_URL


ENTER_ID = (
    "📍 | Отправь новый ID для этой записи\n"
    "  └ 👉 Например: 2281337300"
)
def format_enter_id():
    return ENTER_ID


ENTER_PWD = (
    "🔑 | Отправь новый пароль для этой записи\n"
    "  └ 👉 Например: 0oChKo или др."
)
def format_enter_pwd():
    return ENTER_PWD


ENTER_HOST_KEY = (
    "🔒 | Отправь новый ключ хоста для этой записи\n"
    "  └ 👉 Например: 0oChKo или др."
)
def format_enter_host_key():
    return ENTER_HOST_KEY


ENTER_NOTES = (
    "📝 | Отправь заметки для этой записи\n"
    "  └ 👉 Например: почта и Google Drive"
)
def format_enter_notes():
    return ENTER_NOTES


TCHR_ENTER_NOTES = (
    "📝 | Отправь заметки для этой записи"
)
def format_thcr_enter_notes():
    return TCHR_ENTER_NOTES


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
    overwriting: zoom.Entries,
    mode: "MODE_LITERAL"
):
    sections: list[str] = []

    if len(adding) > 0:
        entries = common.text.indent(adding.format_compact(mode))
        text = format_will_be_added(len(adding))
        text += "\n"
        text += entries

        sections.append(text)

    if len(overwriting) > 0:
        entries = common.text.indent(overwriting.format_compact(mode))
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


REMOVE_CONFIRMATION = (
    "🗑️ | Точно {removal_type} все записи?"
)
def format_remove_confirmation(removal_type: str):
    return REMOVE_CONFIRMATION.format(removal_type=removal_type)


YOU_CAN_DUMP_ENTRIES_BEFORE_REMOVAL = (
    "💾 | Ты можешь сделать дамп перед удалением, чтобы не потерять их"
)
def format_you_can_dump_entries_before_removal():
    return YOU_CAN_DUMP_ENTRIES_BEFORE_REMOVAL


FINISH = (
    f"👍 | Фпринципи фсё, можешь перепроверить или нажать {Text.FINISH}"
)
def format_finish():
    return FINISH


GROUP_SETTING_EXPLAIN = (
    f"{Text.GROUP} - настройки группы, с которой работает негр"
)
TEACHER_SETTING_EXPLAIN = (
    f"{Text.TEACHER} - настройки препода, с которым работает негр"
)
BROADCAST_SETTING_EXPLAIN = (
    f"{Text.BROADCAST} - получишь ли ты новое сообщение при обновлении расписания для установленной группы"
)
TCHR_BROADCAST_SETTING_EXPLAIN = (
    f"{Text.BROADCAST} - получишь ли ты новое сообщение при обновлении расписания для установленного препода"
)
PIN_SETTING_EXPLAIN = (
    f"{Text.PIN} - закрепит ли негр рассылку расписания"
)
ZOOM_SETTING_EXPLAIN = (
    f"{Text.ZOOM} - настройки данных преподов: их имена, ссылки, ID, пароли и заметки, которые показываются в расписании"
)
TCHR_ZOOM_SETTING_EXPLAIN = (
    f"{Text.ZOOM} - настройки данных Zoom: ссылки, ID, пароли и заметки, которые показываются в расписании"
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


LOGS_EMPTY = (
    "<Empty logs>"
)
def format_logs_empty() -> str:
    return LOGS_EMPTY


EXECUTION_ERROR = (
    "❌ Error: {error}"
)
def format_execution_error(error: str, traceback: Optional[str] = None) -> str:
    exec_error_message = EXECUTION_ERROR
    if traceback is not None:
        exec_error_message += "\n\n"
        exec_error_message += traceback

    return exec_error_message.format(error=error)


EXECUTE_CODE_EXPLAIN = (
    "🛠️ | Напиши код для выполнения в асинхронном рантайме\n\n"
    "Для вывода сообщений: {print_example}\n\n"
    "Полезные пути:\n"
    "src.defs (defs -> (redis, ctx -> get_everyone))\n"
    "src.svc.common.keyboard (Keyboard, *_BUTTON)\n"
    "src.svc.common.states.tree (HUB, SETTINGS, ...)\n"
)
def format_execute_code_explain(exposed_vars: list[str], print_example: str) -> str:
    return EXECUTE_CODE_EXPLAIN.format(
        exposed_vars=", ".join(exposed_vars),
        print_example=print_example
    )


NO_RIGHTS = (
    "Хуй знает как у тебя это получилось, но тебе это недоступно"
)
def format_no_rights() -> str:
    return NO_RIGHTS


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
MANUAL_UPDATES_ARE_DISABLED = (
    "Ручные обновления теперь недоступны"
)
def format_manual_updates_are_disabled():
    return MANUAL_UPDATES_ARE_DISABLED


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


TEACHER_CHANGED_IN_SC_TYPE = (
    "Препод {change} в {sc_type}"
)
def format_teacher_changed_in_sc_type(
    change: compare.ChangeType,
    sc_type: schedule.Type
):
    if change == compare.ChangeType.APPEARED:
        repr_change = "появился"
    elif change == compare.ChangeType.CHANGED:
        repr_change = "изменился"

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

NOT_MAINTAINED_ANYMORE = (
    "⚠️⚠️⚠️\n"
    "Бот больше не обслуживается. Расписание дистанта не работает.\n\n"
    "Формат дистант расписания поменялся, в будущем возможно поменяется и очка, а переписывать код желания нет.\n"
    "Создателя отчислили летом 2023-го, и ему больше нет дела до этого.\n\n"
    "🔧 Кто хочет переделать/доработать бота сам, сюда: https://github.com/kerdl/ktmuslave.\n"
    f"💼 Кто хочет задать вопрос или что-то предложить: {get_key(ENV_PATH, 'ADMIN_CONTACT_MAIL')}."
)
def format_not_maintained_anymore():
    return NOT_MAINTAINED_ANYMORE
