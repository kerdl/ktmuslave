from __future__ import annotations
import html
from typing import Any, Optional, TYPE_CHECKING
from src import defs
from src.svc import common
from src.data.settings import Settings
from src.data import zoom, format as fmt
from src.data.schedule import compare
from src.parse.zoom import Key
from src.svc import telegram as tg
from src.svc.common.states import State
from src.svc.common.keyboard import Text


if TYPE_CHECKING:
    from src.data.settings import MODE_LITERAL


DEBUGGING = False


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
    mention = ""
    footer_addition = ""

    if everything.is_group_chat:
        if everything.is_from_vk:
            mention = defs.vk_bot_mention
            footer_addition = format_mention_me(mention)

        elif everything.is_from_tg:
            footer_addition = format_reply_to_me()

    return footer_addition

MSG_DEBUG = (
    "8==o🤮 trace:\n"
    "{trace}\n"
    "8==o🤮 back_trace:\n"
    "{back_trace}"
)
def format_debug(
    trace: list[State],
    back_trace: list[State],
    last_bot_message: common.CommonBotMessage,
    settings: Settings
):
    def fmt_trace(trace: list[State]):
        return "\n".join([f"   {state.space}:{state.anchor}" for state in trace])

    trace_str = fmt_trace(trace)
    back_trace_str = fmt_trace(back_trace)

    return MSG_DEBUG.format(
        trace=trace_str,
        back_trace=back_trace_str,
    )


MSG_CANT_PRESS_OLD_BUTTONS = (
    "Вот тебе новое сообщение, "
    "тыкай на нём"
)
def format_cant_press_old_buttons():
    return MSG_CANT_PRESS_OLD_BUTTONS

MSG_SENT_AS_NEW_MESSAGE = (
    "Отправлено новым сообщением"
)
def format_sent_as_new_message():
    return MSG_SENT_AS_NEW_MESSAGE
    

MSG_EMPTY_PAGE = (
    "🤔 | Пусто. Можешь добавить записи с помощью кнопки ниже."
)
def format_empty_page():
    return MSG_EMPTY_PAGE


MSG_PRESS_BEGIN = (
    f"👇 Нажимай {Text.BEGIN}"
)
def format_press_begin():
    return MSG_PRESS_BEGIN


MSG_GROUPS = (
    "📋 | Группы в расписании:\n"
    "  └ {groups}"
)
def format_groups(groups: list[str]):
    groups_str = ", ".join(groups) or "пусто"
    return MSG_GROUPS.format(groups=groups_str)

MSG_TEACHERS = (
    "📋 | Преподы в расписании:\n"
    "  └ {teachers}"
)
def format_teachers(teachers: list[str]):
    teachers_str = ", ".join(teachers) or "пусто"
    return MSG_TEACHERS.format(teachers=teachers_str)


MSG_MENTION_ME = (
    "Ещё упомяни меня: {mention}, иначе не увижу"
)
def format_mention_me(mention: str):
    return MSG_MENTION_ME.format(mention=mention)


MSG_REPLY_TO_ME = (
    "Ещё ↩️ ответь ↩️ на это сообщение, иначе не увижу"
)
def format_reply_to_me():
    return MSG_REPLY_TO_ME


MSG_CHAT_WILL_MIGRATE = (
    "🤔 Из-за этого, эта группа станет супергруппой\n"
    "Читай подробнее здесь: https://teleme.io/articles/turn_a_telegram_group_into_a_supergroup?hl=ru"
)
def format_chat_will_migrate():
    return MSG_CHAT_WILL_MIGRATE


MSG_PAGE_NUM = (
    "📄 | Страница {current}/{last}"
)
def format_page_num(current: int, last: int):
    return MSG_PAGE_NUM.format(current=current, last=last)


MSG_PRESS_BUTTONS_TO_CHANGE = (
    "👇 | Нажми на параметр, чтобы его изменить"
)
def format_press_buttons_to_change():
    return MSG_PRESS_BUTTONS_TO_CHANGE


MSG_NO_TEXT = (
    "❌ | Тут нет текста"
)
def format_no_text():
    return MSG_NO_TEXT


MSG_CURRENT_VALUE = (
    "📝 | Текущее значение: {value}"
)
def format_current_value(value: Any):
    return MSG_CURRENT_VALUE.format(
        value = fmt.value_repr(value)
    )


MSG_CANT_CONNECT_TO_SCHEDULE_SERVER = (
    "🤔 | Невозможно подключиться к серверу расписания"
)
def format_cant_connect_to_schedule_server() -> str:
    return MSG_CANT_CONNECT_TO_SCHEDULE_SERVER


MSG_SCHEDULE_UNAVAILABLE = (
    "🤔 | Расписание недоступно"
)
def format_schedule_unavailable() -> str:
    return MSG_SCHEDULE_UNAVAILABLE


#### Full messages for specific states ####

MSG_WELCOME =  (
    "👨🏿 Буду пиздить расписание "
    "с ktmu-sutd.ru "
    "и делиться с {noun}"
)
def format_welcome(is_group_chat: bool):
    if is_group_chat:
        return MSG_WELCOME.format(noun="вами")
    else:
        return MSG_WELCOME.format(noun="тобой")

MSG_CHOOSE_SCHEDULE_MODE = (
    "⛓️ | Выбери режим расписания"
)
def format_choose_schedule_mode():
    return MSG_CHOOSE_SCHEDULE_MODE

MSG_GROUP_INPUT = (
    "💅 | Напиши свою группу\n"
    "📌 | Формат:\n"
    "  └ 1кдд69\n"
    "  └ 1-кдд-69\n"
    "  └ 1КДД69\n"
    "  └ 1-КДД-69"
)
def format_group_input():
    return MSG_GROUP_INPUT

MSG_TEACHER_INPUT = (
    "💅 | Напиши свою фамилию\n"
    "📌 | Формат:\n"
    "  └ Говновоз Ж.Д.\n"
    "  └ Говновоз жд\n"
    "  └ Говновоз"
)
def format_teacher_input():
    return MSG_TEACHER_INPUT


MSG_UNKNOWN_IDENTIFIER = (
    "❓ | {identifier} пока нет, всё равно поставить?"
)
def format_unknown_identifier(identifier: str):
    return MSG_UNKNOWN_IDENTIFIER.format(identifier=identifier)


MSG_INVALID_GROUP = (
    "❌ | Это не подходит под формат:\n"
    "  └ 1кдд69\n"
    "  └ 1-кдд-69\n"
    "  └ 1КДД69\n"
    "  └ 1-КДД-69\n"
    "💡 | Напиши ещё раз по формату"
)
def format_invalid_group():
    return MSG_INVALID_GROUP


MSG_INVALID_TEACHER = (
    "❌ | Это не подходит под формат:\n"
    "  └ Говновоз Ж.Д.\n"
    "  └ Говновоз жд\n"
    "  └ Говновоз\n"
    "💡 | Напиши ещё раз по формату"
)
def format_invalid_teacher():
    return MSG_INVALID_TEACHER


MSG_FORBIDDEN_FORMAT_TEACHER = (
    "❌ | Препода нет в расписании, такой формат использовать нельзя"
    "💡 | Используй:\n"
    "  └ Говновоз Ж.Д.\n"
    "  └ Говновоз жд"
)
def format_forbidden_format_teacher():
    return MSG_FORBIDDEN_FORMAT_TEACHER


MSG_BROADCAST = (
    "🔔 | Хочешь получать здесь рассылку, когда у группы меняется расписание?"
)
def format_broadcast():
    return MSG_BROADCAST


MSG_TCHR_BROADCAST = (
    "🔔 | Хочешь получать здесь рассылку, когда у препода меняется расписание?"
)
def format_tchr_broadcast():
    return MSG_TCHR_BROADCAST


MSG_DO_PIN = (
    "📌 | Хочешь шоб я закреплял рассылку расписания?"
)
def format_do_pin():
    return MSG_DO_PIN


MSG_RECOMMEND_PIN = (
    "📌 | Я могу закреплять рассылку расписания, "
    "но сейчас у меня нет прав"
)
def format_recommend_pin():
    return MSG_RECOMMEND_PIN


MSG_PERMIT_PIN_VK = (
    "🚽 | Если хочешь заркеп, назначь меня админом, "
    "либо пропусти если поебать"
)
MSG_PERMIT_PIN_TG = (
    "🚽 | Если хочешь закреп, назначь меня админом с правом "
    "\"Закрепление сообщений\", либо пропусти если поебать"
)
def format_permit_pin(src: common.MESSENGER_OR_EVT_SOURCE):
    if src == common.Source.VK:
        return MSG_PERMIT_PIN_VK
    if src == common.Source.TG:
        return MSG_PERMIT_PIN_TG


MSG_CANT_PIN_VK = (
    "❌ Не получилось, проверь мою админку"
)
MSG_CANT_PIN_TG = (
    "❌ Не получилось, проверь моё право \"Закрепление сообщений\""
)
def format_cant_pin(src: common.MESSENGER_OR_EVT_SOURCE):
    if src == common.Source.VK:
        return MSG_CANT_PIN_VK
    if src == common.Source.TG:
        return MSG_CANT_PIN_TG


MSG_RECOMMEND_ADDING_ZOOM = (
    "📝 | Ты можешь добавить ссылки, ID, пароли Zoom и заметки, "
    "чтобы они показывались в расписании"
)
def format_recommend_adding_zoom():
    return MSG_RECOMMEND_ADDING_ZOOM


MSG_CHOOSE_ADDING_TYPE = (
    "📝 | Выбери как ты хочешь добавить запись/записи"
)
def format_choose_adding_type():
    return MSG_CHOOSE_ADDING_TYPE


MSG_ZOOM_ADD_FROM_TEXT_EXPLAIN = (
    f"{Text.FROM_TEXT} - пишешь одно сообщение по формату, "
    "автоматом берёт все данные"
)
def format_zoom_add_from_text_explain():
    return MSG_ZOOM_ADD_FROM_TEXT_EXPLAIN


MSG_ZOOM_ADD_MANUALLY_INIT_EXPLAIN = (
    f"{Text.MANUALLY} - добавляешь, изменяешь, удаляешь "
    "по отдельности"
)
def format_zoom_add_manually_init_explain():
    return MSG_ZOOM_ADD_MANUALLY_INIT_EXPLAIN


MSG_ZOOM_ADD_MANUALLY_HUB_EXPLAIN = (
    f"{Text.MANUALLY} - добавить новое имя вручную"
)
def format_zoom_add_manually_hub_explain():
    return MSG_ZOOM_ADD_MANUALLY_HUB_EXPLAIN


MSG_SEND_ZOOM_DATA = (
    "💬 | Напиши сообщение с данными Zoom по формату"
)
def format_send_zoom_data():
    return MSG_SEND_ZOOM_DATA


MSG_ZOOM_DATA_FORMAT = (
    "📝 | Формат:\n"
    f"   ↵ {Key.NAME}: <Фамилия> <И>.<О>.\n"
    f"   ↵ {Key.URL}: <Ссылка>\n"
    f"   ↵ {Key.ID}: <ID>\n"
    f"   ↵ {'/'.join(Key.PWD)}: <Код>\n"
    f"   ↵ {Key.NOTES}: <Любой текст>\n"
    f"   ↵ ..."
)
def format_zoom_data_format(do_escape: bool = False):
    text = MSG_ZOOM_DATA_FORMAT
    
    if do_escape:
        return html.escape(text)

    return text


MSG_TCHR_ZOOM_DATA_FORMAT = (
    "📝 | Формат:\n"
    f"   ↵ {Key.NAME}: <Имя записи>\n"
    f"   ↵ {Key.URL}: <Ссылка>\n"
    f"   ↵ {Key.ID}: <ID>\n"
    f"   ↵ {'/'.join(Key.PWD)}: <Код>\n"
    f"   ↵ {Key.HOST_KEY}: <Ключ хоста>\n"
    f"   ↵ {Key.NOTES}: <Любой текст>\n"
    f"   ↵ ..."
)
def format_tchr_zoom_data_format(do_escape: bool = False):
    text = MSG_TCHR_ZOOM_DATA_FORMAT
    
    if do_escape:
        return html.escape(text)

    return text


MSG_ZOOM_EXAMPLE = (
    "🔖 | Например:\n"
    "<code>"
    "   имя: Говновоз Ж.Д.\n"
    "   ссылка: https://us04web.zoom.us/j/2281337300?pwd=I4mTir3d0fPl4yingWithMyW00d\n"
    "   Ид: 22813376969\n"
    "   Код: 0oChK0\n"
    "\n"
    "   имя: Говновоз Ж.\n"
    "   Ид: 22813376969\n"
    "   заметки: говновоз жидкий дрист https://www.nsopw.gov"
    "</code>"
)
def format_zoom_example(do_markup: bool = True):
    text = MSG_ZOOM_EXAMPLE
    
    if not do_markup:
        return tg.remove_markup(text)
    
    return text


MSG_TCHR_ZOOM_EXAMPLE = (
    "🔖 | Например:\n"
    "<code>"
    "   имя: Для 1КДД69\n"
    "   ссылка: https://us04web.zoom.us/j/2281337300?pwd=I4mTir3d0fPl4yingWithMyW00d\n"
    "   Ид: 22813376969\n"
    "   Код: 0oChK0\n"
    "   ключ: mRp3ni5\n"
    "\n"
    "   Имя: Доп. занятия\n"
    "   Ид: 22813376969\n"
    "   заметки: только 2КДД69"
    "</code>"
)
def format_tchr_zoom_example(do_markup: bool = True):
    text = MSG_TCHR_ZOOM_EXAMPLE
    
    if not do_markup:
        return tg.remove_markup(text)
    
    return text


MSG_MASS_ZOOM_DATA_EXPLAIN = (
    "❗ Обязательно ставь префикс в начале строки, регистр неважен\n"
    "💡 Можешь писать в разной последовательности и пропускать некоторые поля\n"
    "💡 В одном сообщении может быть несколько блоков, смотри пример"
)
def format_mass_zoom_data_explain():
    return MSG_MASS_ZOOM_DATA_EXPLAIN


MSG_DOESNT_CONTAIN_ZOOM = (
    f"❌ | По формату тут ничего нет\n"
    f"  └ 💡 Блоки без ФИО игнорируются\n"
    f"  └ 💡 Имена больше {zoom.NAME_LIMIT} символов игнорируются"
)
def format_doesnt_contain_zoom():
    return MSG_DOESNT_CONTAIN_ZOOM


MSG_TCHR_DOESNT_CONTAIN_ZOOM = (
    f"❌ | По формату тут ничего нет\n"
    f"  └ 💡 Блоки без имён игнорируются\n"
    f"  └ 💡 Имена больше {zoom.NAME_LIMIT} символов игнорируются"
)
def format_tchr_doesnt_contain_zoom():
    return MSG_TCHR_DOESNT_CONTAIN_ZOOM


MSG_YOU_CAN_ADD_MORE = (
    "🤓 | Ты можешь добавить больше или перезаписать что-то, "
    "просто отправь ещё одно сообщение с данными"
)
def format_you_can_add_more():
    return MSG_YOU_CAN_ADD_MORE


MSG_VALUE_TOO_BIG = (
    "❌ | Сократи до {limit} символов"
)
def format_value_too_big(limit: int):
    return MSG_VALUE_TOO_BIG.format(limit=limit)


MSG_ENTER_NAME = (
    "🐷 | Отправь новое имя этой записи\n"
    "  └ 👉 Например: <code>Говновоз Ж.Д.</code>, <code>Говновоз Ж.</code>"
)
def format_enter_name(do_markup: bool = True):
    text = MSG_ENTER_NAME
    
    if not do_markup:
        return tg.remove_markup(text)
    
    return text


MSG_TCHR_ENTER_NAME = (
    "🐷 | Отправь новое имя этой записи\n"
    "  └ 👉 Например: <code>Для 1КДД69</code>, <code>Доп. занятия</code>"
)
def format_tchr_enter_name(do_markup: bool = True):
    text = MSG_TCHR_ENTER_NAME
    
    if not do_markup:
        return tg.remove_markup(text)
    
    return text


MSG_NAME_IN_DATABASE = (
    "❌ | Это имя уже в базе"
)
def format_name_in_database():
    return MSG_NAME_IN_DATABASE


MSG_ENTER_URL = (
    "🌐 | Отправь новую ссылку для этой записи\n"
    "  └ 👉 Например: <code>https://us04web.zoom.us/j/2281337300?pwd=I4mTir3d0fPl4yingWithMyW00d</code>"
)
def format_enter_url(do_markup: bool = True):
    text = MSG_ENTER_URL
    
    if not do_markup:
        return tg.remove_markup(text)
    
    return text


MSG_ENTER_ID = (
    "📍 | Отправь новый ID для этой записи\n"
    "  └ 👉 Например: <code>2281337300</code>"
)
def format_enter_id(do_markup: bool = True):
    text = MSG_ENTER_ID

    if not do_markup:
        return tg.remove_markup(text)
    
    return text


MSG_ENTER_PWD = (
    "🔑 | Отправь новый пароль для этой записи\n"
    "  └ 👉 Например: <code>0oChKo</code> или др."
)
def format_enter_pwd(do_markup: bool = True):
    text = MSG_ENTER_PWD

    if not do_markup:
        return tg.remove_markup(text)
    
    return text


MSG_ENTER_HOST_KEY = (
    "🔒 | Отправь новый ключ хоста для этой записи\n"
    "  └ 👉 Например: <code>mRp3ni5</code> или др."
)
def format_enter_host_key(do_markup: bool = True):
    text = MSG_ENTER_HOST_KEY

    if not do_markup:
        return tg.remove_markup(text)
    
    return text


MSG_ENTER_NOTES = (
    "📝 | Отправь заметки для этой записи\n"
    "  └ 👉 Например: почта и Google Drive"
)
def format_enter_notes():
    return MSG_ENTER_NOTES


MSG_TCHR_ENTER_NOTES = (
    "📝 | Отправь заметки для этой записи"
)
def format_thcr_enter_notes():
    return MSG_TCHR_ENTER_NOTES


MSG_WILL_BE_ADDED = (
    "❇ Будет добавлено: {count}"
)
def format_will_be_added(count: int):
    return MSG_WILL_BE_ADDED.format(
        count = count,
    )


MSG_WILL_BE_OVERWRITTEN = (
    "♻ Будет перезаписано: {count}"
)
def format_will_be_overwritten(count: int):
    return MSG_WILL_BE_OVERWRITTEN.format(
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


MSG_DUMP_EXPLAIN = (
    f"💾 | Ты можешь преобразовать "
    f"все добавленные здесь записи в текстовый вид "
    f"и добавить их в другом диалоге через функцию {Text.FROM_TEXT}\n\n"
    f"💡 | Если записей слишком много, "
    f"они могут быть отправлены несколькими сообщениями\n\n"
    f"👇 | Нажимай {Text.DUMP} чтобы засрать беседу"
)
def format_dump_explain():
    return MSG_DUMP_EXPLAIN


MSG_REMOVE_CONFIRMATION = (
    "🗑️ | Точно {removal_type} все записи?"
)
def format_remove_confirmation(removal_type: str):
    return MSG_REMOVE_CONFIRMATION.format(removal_type=removal_type)


MSG_YOU_CAN_DUMP_ENTRIES_BEFORE_REMOVAL = (
    "💾 | Ты можешь сделать дамп "
    "перед удалением, чтобы не потерять их"
)
def format_you_can_dump_entries_before_removal():
    return MSG_YOU_CAN_DUMP_ENTRIES_BEFORE_REMOVAL


MSG_FINISH = (
    f"👍 | Готово, можешь перепроверить "
    f"или нажать {Text.FINISH}"
)
def format_finish():
    return MSG_FINISH


MSG_GROUP_SETTING_EXPLAIN = (
    f"{Text.GROUP}: ""{group}\n"
    f"└ Настройки группы, с которой работает негр"
)
MSG_TEACHER_SETTING_EXPLAIN = (
    f"{Text.TEACHER}: ""{teacher}\n"
    f"└ Настройки препода, с которым работает негр"
)
MSG_BROADCAST_SETTING_EXPLAIN = (
    f"{Text.BROADCAST}: ""{broadcast}\n"
    f"└ Получишь ли ты новое сообщение "
    f"при обновлении расписания для установленной группы"
)
MSG_TCHR_BROADCAST_SETTING_EXPLAIN = (
    f"{Text.BROADCAST}: ""{broadcast}\n"
    f"└ Получишь ли ты новое сообщение "
    f"при обновлении расписания для установленного препода"
)
MSG_PIN_SETTING_EXPLAIN = (
    f"{Text.PIN}: ""{do_pin}\n"
    f"└ Закрепит ли негр рассылку расписания"
)
MSG_ZOOM_SETTING_EXPLAIN = (
    f"{Text.ZOOM}: ""{zoom}\n"
    f"└ Настройки данных преподов: "
    f"их имена, ссылки, ID, пароли и заметки, "
    f"которые показываются в расписании"
)
MSG_TCHR_ZOOM_SETTING_EXPLAIN = (
    f"{Text.ZOOM}: ""{zoom}\n"
    f"└ Настройки данных Zoom: "
    f"ссылки, ID, пароли и заметки, "
    f"которые показываются в расписании"
)
MSG_RESET_SETTING_EXPLAIN = (
    f"{Text.RESET}\n"
    f"└ Сбросить все данные "
    f"и начать первоначальную настройку"
)
def format_settings_main(
    is_group_chat: bool,
    group: str,
    broadcast: bool,
    do_pin: bool,
    zoom: int
) -> str:
    text = ""

    text += MSG_GROUP_SETTING_EXPLAIN.format(
        group=fmt.value_repr(group)
    ) + "\n"
    text += "\n"
    text += MSG_BROADCAST_SETTING_EXPLAIN.format(
        broadcast=fmt.value_repr(broadcast)
    ) + "\n"
    text += "\n"
    if is_group_chat:
        text += MSG_PIN_SETTING_EXPLAIN.format(
            do_pin=fmt.value_repr(do_pin)
        ) + "\n"
        text += "\n"
    text += MSG_ZOOM_SETTING_EXPLAIN.format(
        zoom=fmt.value_repr(zoom)
    ) + "\n"
    text += "\n"
    text += MSG_RESET_SETTING_EXPLAIN + "\n"

    return text

def format_tchr_settings_main(
    is_group_chat: bool,
    teacher: str,
    broadcast: bool,
    do_pin: bool,
    zoom: int
) -> str:
    text = ""

    text += MSG_TEACHER_SETTING_EXPLAIN.format(
        teacher=fmt.value_repr(teacher)
    ) + "\n"
    text += "\n"
    text += MSG_TCHR_BROADCAST_SETTING_EXPLAIN.format(
        broadcast=fmt.value_repr(broadcast)
    ) + "\n"
    text += "\n"
    if is_group_chat:
        text += MSG_PIN_SETTING_EXPLAIN.format(
            do_pin=fmt.value_repr(do_pin)
        ) + "\n"
        text += "\n"
    text += MSG_TCHR_ZOOM_SETTING_EXPLAIN.format(
        zoom=fmt.value_repr(zoom)
    ) + "\n"
    text += "\n"
    text += MSG_RESET_SETTING_EXPLAIN + "\n"

    return text


MSG_RESET_EXPLAIN = (
    f"🗑️ | Это сбросит все настройки + Zoom данные "
    f"и потребует пройти начальную настройку\n\n"
    f"👇 | Нажимай {Text.RESET} если тоже хочешь "
    f"болезнь Альцгеймера"
)
def format_reset_explain() -> str:
    return MSG_RESET_EXPLAIN


MSG_LOGS_EMPTY = (
    "<Empty logs>"
)
def format_logs_empty(do_escape: bool = False) -> str:
    text = MSG_LOGS_EMPTY
    if do_escape:
        return html.escape(text)

    return text


MSG_EXECUTION_ERROR = (
    "❌ Error: {error}"
)
def format_execution_error(
    error: str,
    traceback: Optional[str] = None
) -> str:
    exec_error_message = MSG_EXECUTION_ERROR
    if traceback is not None:
        exec_error_message += "\n\n"
        exec_error_message += traceback

    return exec_error_message.format(error=error)


MSG_EXECUTE_CODE_EXPLAIN = (
    "🛠️ | Напиши код для выполнения в асинхронном рантайме\n\n"
    "Для вывода сообщений: {print_example}\n\n"
    "Полезные пути:\n"
    "src.defs (defs -> (redis, ctx -> get_everyone))\n"
    "src.svc.common.keyboard (Keyboard, *_BUTTON)\n"
    "src.svc.common.states.tree (HUB, SETTINGS, ...)"
)
def format_execute_code_explain(
    exposed_vars: list[str],
    print_example: str
) -> str:
    return MSG_EXECUTE_CODE_EXPLAIN.format(
        exposed_vars=", ".join(exposed_vars),
        print_example=print_example
    )


MSG_NO_RIGHTS = (
    "Тебе это недоступно"
)
def format_no_rights() -> str:
    return MSG_NO_RIGHTS


MSG_NO_SCHEDULE = (
    "🤔 Группы нет в этом расписании"
)
def format_no_schedule() -> str:
    return MSG_NO_SCHEDULE


MSG_TCHR_NO_SCHEDULE = (
    "🤔 Препода нет в этом расписании"
)
def format_tchr_no_schedule() -> str:
    return MSG_TCHR_NO_SCHEDULE


MSG_SCHEDULE_FOOTER = (
    "⏱ Последнее обновление: {last_update}\n"
    "✉ Период автообновления: {update_period}"
)
def format_schedule_footer(last_update: Any, update_period: Any) -> str:
    return MSG_SCHEDULE_FOOTER.format(
        last_update=last_update if last_update else "неизвестно",
        update_period=f"{update_period} мин" if update_period else "неизвестно"
    )


MSG_MANUAL_UPDATES_ARE_DISABLED = (
    "❌ Ручные обновления теперь недоступны"
)
def format_manual_updates_are_disabled():
    return MSG_MANUAL_UPDATES_ARE_DISABLED


MSG_NOT_IMPLEMENTED_ERROR = (
    "🤔 Функция не реализована"
)
def format_not_implemented_error() -> str:
    return MSG_NOT_IMPLEMENTED_ERROR


MSG_GROUP_CHANGED_IN_SCHEDULE = (
    "🧭 Группа {change} в расписании"
)
def format_group_changed_in_schedule(change: compare.ChangeType):
    if change == compare.ChangeType.APPEARED:
        repr_change = "появилась"
    elif change == compare.ChangeType.CHANGED:
        repr_change = "изменилась"

    return MSG_GROUP_CHANGED_IN_SCHEDULE.format(
        change=repr_change
    )


MSG_TEACHER_CHANGED_IN_SCHEDULE = (
    "🧭 Препод {change} в расписании"
)
def format_teacher_changed_in_schedule(change: compare.ChangeType):
    if change == compare.ChangeType.APPEARED:
        repr_change = "появился"
    elif change == compare.ChangeType.CHANGED:
        repr_change = "изменился"

    return MSG_TEACHER_CHANGED_IN_SCHEDULE.format(
        change=repr_change
    )


MSG_REPLIED_TO_SCHEDULE_MESSAGE = (
    "👆 Прошлое расписание в ответном сообщении"
)
def format_replied_to_schedule_message():
    return MSG_REPLIED_TO_SCHEDULE_MESSAGE


MSG_DETAILED_COMPARE_NOT_SHOWN = (
    "(детальные изменения не показаны)"
)
def format_detailed_compare_not_shown():
    return MSG_DETAILED_COMPARE_NOT_SHOWN
