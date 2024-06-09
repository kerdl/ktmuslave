from __future__ import annotations
from copy import deepcopy
from typing import Any, Optional, Union, List, TYPE_CHECKING
from typing import Literal
from vkbottle import (
    Keyboard as VkKeyboard, 
    Callback as VkCallback,
    OpenLink as VkLink,
    KeyboardButtonColor as VkColor
)
from aiogram.types import (
    InlineKeyboardMarkup as TgKeyboard, 
    InlineKeyboardButton as TgInlineButton,
    ForceReply as TgForceReply
)
from dataclasses import dataclass
from pydantic import BaseModel, Field as PydField, parse_obj_as

from src.svc import common
from src.data import Emojized, Repred, Translated, Field, Emoji, format as fmt, schedule
from src.svc.vk.keyboard import CMD


if TYPE_CHECKING:
    from src.data.settings import MODE_LITERAL


class Payload:
    # common buttons
    TRUE          = "true"
    FALSE         = "false"
    BACK          = "back"
    NEXT          = "next"
    SKIP          = "skip"
    CONTINUE      = "continue"
    PAGE_BACK     = "page_back"
    PAGE_NEXT     = "page_next"

    # Init buttons
    BEGIN         = "begin"
    DO_PIN        = "do_pin"
    FINISH        = "finish"

    # Settings buttons
    MODE          = "mode"
    ME_STUDENT    = "me_student"
    ME_TEACHER    = "me_teacher"
    GROUP         = "group"
    TEACHER       = "teacher"
    SHOW_NAMES    = "show_names"
    GROUP_MODE    = "group_mode"
    TEACHER_MODE  = "teacher_mode"
    BROADCAST     = "broadcast"
    PIN           = "pin"
    ZOOM          = "zoom"
    EXECUTE_CODE  = "execute_code"
    RESET         = "reset"

    # Zoom buttons
    FROM_TEXT     = "from_text"
    MANUALLY_INIT = "manually_init"
    MANUALLY_HUB  = "manually_hub"
    BROWSER       = "browser"
    ADD_INIT      = "add_init"
    ADD_HUB       = "add_hub"
    ADD_ALL       = "add_all"
    CONFIRM       = "confirm"
    NULL          = "null"
    REMOVE        = "remove"
    REMOVE_ALL    = "remove_all"
    DUMP          = "dump"
    DUMP_AND_REMOVE_ALL = "dump_and_remove_all"
    CLEAR         = "clear"
    NEXT_ZOOM     = "next_zoom"

    NAME          = "name"
    URL           = "url"
    ID            = "id"
    PWD           = "pwd"
    HOST_KEY      = "host_key"
    NOTES         = "notes"

    # Hub buttons
    RESEND        = "resend"
    GO_TO_HUB     = "go_to_hub"
    WEEKLY        = "weekly"
    DAILY         = "daily"
    FOLD          = "fold"
    UNFOLD        = "unfold"
    UPDATE        = "update"
    SETTINGS      = "settings"

class Text:
    # common buttons
    TRUE       = "✓ ПизДА!"
    FALSE      = "✕ МиНЕТ..."
    BACK       = "← Назад"
    NEXT       = "→ Далее"
    SKIP       = "→ Пропустить"
    CONTINUE   = "→ Продолжить"

    # Init buttons
    BEGIN      = "→ Начать"
    DO_PIN     = "✓ Закреплять"
    FINISH     = "→ Закончить"

    # Settings buttons
    MODE         = "⛓️ Режим"
    ME_STUDENT   = "🧑‍🎓 Группа"
    ME_TEACHER   = "🧑‍🏫 Препод"
    GROUP        = "👥 Группа"
    SHOW_NAMES   = "👀 Показать имена"
    GROUP_MODE   = "🔁 Режим группы"
    TEACHER_MODE = "🔁 Режим препода"
    TEACHER      = "👤 Препод"
    BROADCAST    = "✉️ Рассылка"
    PIN          = "📌 Закрепление"
    ZOOM         = "🖥️ Zoom"
    EXECUTE_CODE = "🛠️ Выполнить код"
    RESET        = "🗑️ Сбросить всё"

    # Zoom buttons
    FROM_TEXT           = "💬 Из сообщения"
    MANUALLY            = "✍️ Вручную"
    ADD                 = "+ Добавить"
    ADD_ALL             = "✓ Добавить всё"
    CONFIRM             = "✓ Подтвердить"
    NULL                = "✕ Обнулить"
    REMOVE              = "✕ Удалить"
    REMOVE_ALL          = "✕ Удалить всё"
    DUMP                = "💾 Дамп"
    CLEAR               = "✕ Очистить"
    DUMP_AND_REMOVE_ALL = f"{DUMP} и {REMOVE_ALL}"

    # Hub buttons
    RESEND     = "✉️ Новое сообщение"
    GO_HOME    = "🏠 Вернуться"
    GO_TO_HUB  = "🏠 В хаб"
    WEEKLY     = "⇋ Недельное"
    DAILY      = "⇋ Дневное"
    FOLD       = "⮟ Свернуть"
    UNFOLD     = "⮝ Развернуть"
    UPDATE     = "↻ Обновить"
    SETTINGS   = "⚙️ Настройки"
    FT_DAILY   = "Очн. день"
    FT_WEEKLY  = "Очн. нед."
    R_WEEKLY   = "Дист. нед."
    MATERIALS  = "Материалы"
    JOURNALS   = "Журналы"

COLOR_LITERAL = Literal["gray", "blue", "green", "red"]

class Color:
    """ ## ONLY WORKS IN VK """
    GRAY  = "gray"
    BLUE  = "blue"
    GREEN = "green"
    RED   = "red"

    @staticmethod
    def from_vk(color: VkColor) -> Optional[COLOR_LITERAL]:
        mapping = {
            VkColor.SECONDARY: Color.GRAY,
            VkColor.PRIMARY:   Color.BLUE,
            VkColor.POSITIVE:  Color.GREEN,
            VkColor.NEGATIVE:  Color.RED
        }

        return mapping.get(color)
    
    @staticmethod
    def to_vk(color: COLOR_LITERAL) -> Optional[VkColor]:
        mapping = {
            Color.GRAY:  VkColor.SECONDARY,
            Color.BLUE:  VkColor.PRIMARY,
            Color.GREEN: VkColor.POSITIVE,
            Color.RED:   VkColor.NEGATIVE
        }

        return mapping.get(color)


class Button(BaseModel):
    """ # Represents a common button """
    text: str
    """ ## Button text """
    callback: Optional[str] = None
    """ ## Payload that will be sent on press """
    url: Optional[str] = None
    color: Optional[COLOR_LITERAL] = None
    """ ## Controls tilt angle on `Messerschmitt Me 262` """

    def only_if(self, condition: bool) -> Optional[Button]:
        """ ## Return `Button` if `condition` is `True`, else return `None` """
        if condition is True:
            return self
        else:
            return None
    
    def with_value(self, value: Any) -> Button:
        value_repr = fmt.value_repr(value)

        copied_self = deepcopy(self)
        copied_self.text += f": {value_repr}"

        return copied_self

class Keyboard(BaseModel):
    """
    ## Inline-only cross-platform keyboard
    """
    schematic: list[list[Optional[Button]]] = PydField(default_factory=list)
    """ ## Keyboard itself, the 2D array of buttons """
    add_back: bool = True
    """ ## If we should automatically add back to the bottom """
    next_button: Optional[Button] = None
    """ ## `Next` button, will be placed to the right of `Back` """
    
    def __init__(__pydantic_self__, schematic: Optional[list[list[Optional[Button]]]] = None, **data: Any) -> None:
        super().__init__(**data)
        if schematic is None:
            __pydantic_self__.schematic = []
        elif Keyboard.is_dict_schema(schematic):
            __pydantic_self__.schematic = Keyboard.parse_schema(schematic)
        else:
            __pydantic_self__.schematic = schematic

    @staticmethod
    def is_dict_schema(schematic: list[list[Any]]) -> bool:
        for row in schematic:
            for button in row:
                if button is None: continue
                if isinstance(button, dict): return True
        
        return False

    @staticmethod
    def parse_schema(schematic: list[list[Optional[dict]]]) -> list[list[Button]]:
        parsed_schematic = []
        parsed_row = []

        for row in schematic:
            for button in row:
                if button is None: continue
                btn = Button.parse_obj(button)
                parsed_row.append(btn)
            
            if not parsed_row: continue

            parsed_schematic.append(parsed_row)
            parsed_row = []
        
        return parsed_schematic

    @classmethod
    def hub_default(
        cls: Keyboard,
        sc_type: schedule.TYPE_LITERAL,
        mode: "MODE_LITERAL"
    ) -> Keyboard:
        from src.api.schedule import SCHEDULE_API
        from src.data.settings import Mode

        is_daily = sc_type == schedule.Type.DAILY
        is_weekly = sc_type == schedule.Type.WEEKLY
        is_group_mode = mode == Mode.GROUP
        is_teacher_mode = mode == Mode.TEACHER

        return cls([
            [
                WEEKLY_BUTTON.only_if(is_daily),
                DAILY_BUTTON.only_if(is_weekly)
            ],
            [RESEND_BUTTON],
            [SETTINGS_BUTTON],
            [
                SCHEDULE_API.ft_daily_url_button().only_if(is_group_mode),
                SCHEDULE_API.tchr_ft_daily_url_button().only_if(is_teacher_mode),
                SCHEDULE_API.ft_weekly_url_button().only_if(is_group_mode),
                SCHEDULE_API.tchr_ft_weekly_url_button().only_if(is_teacher_mode),
            ],
            [
                SCHEDULE_API.r_weekly_url_button().only_if(is_group_mode),
                SCHEDULE_API.tchr_r_weekly_url_button().only_if(is_teacher_mode),
            ],
            [MATERIALS_BUTTON, JOURNALS_BUTTON],
        ], add_back=False)

    @classmethod
    def temp_identifier_hub(
        cls: Keyboard,
        sc_type: schedule.TYPE_LITERAL,
        mode: "MODE_LITERAL"
    ) -> Keyboard:
        from src.api.schedule import SCHEDULE_API
        from src.data.settings import Mode

        is_daily = sc_type == schedule.Type.DAILY
        is_weekly = sc_type == schedule.Type.WEEKLY
        is_group_mode = mode == Mode.GROUP
        is_teacher_mode = mode == Mode.TEACHER

        return cls([
            [
                WEEKLY_BUTTON.only_if(is_daily),
                DAILY_BUTTON.only_if(is_weekly)
            ],
            [GO_HOME_BUTTON],
            [
                SCHEDULE_API.ft_daily_url_button().only_if(is_group_mode),
                SCHEDULE_API.tchr_ft_daily_url_button().only_if(is_teacher_mode),
                SCHEDULE_API.ft_weekly_url_button().only_if(is_group_mode),
                SCHEDULE_API.tchr_ft_weekly_url_button().only_if(is_teacher_mode),
            ],
            [
                SCHEDULE_API.r_weekly_url_button().only_if(is_group_mode),
                SCHEDULE_API.tchr_r_weekly_url_button().only_if(is_teacher_mode),
            ],
            [MATERIALS_BUTTON, JOURNALS_BUTTON],
        ], add_back=False)

    @classmethod
    async def hub_broadcast_default(cls: Keyboard, mode: "MODE_LITERAL") -> Keyboard:
        from src.api.schedule import SCHEDULE_API
        from src.data.settings import Mode

        is_group_mode = mode == Mode.GROUP
        is_teacher_mode = mode == Mode.TEACHER

        return cls([
            [RESEND_BUTTON],
            [SETTINGS_BUTTON],
            [
                SCHEDULE_API.ft_daily_url_button().only_if(is_group_mode),
                SCHEDULE_API.tchr_ft_daily_url_button().only_if(is_teacher_mode),
                SCHEDULE_API.ft_weekly_url_button().only_if(is_group_mode),
                SCHEDULE_API.tchr_ft_weekly_url_button().only_if(is_teacher_mode),
            ],
            [
                SCHEDULE_API.r_weekly_url_button().only_if(is_group_mode),
                SCHEDULE_API.tchr_r_weekly_url_button().only_if(is_teacher_mode),
            ],
            [MATERIALS_BUTTON, JOURNALS_BUTTON],
        ], add_back=False)

    @classmethod
    def from_dataclass(
        cls: type[Keyboard],
        dataclass: Union[Translated, Emojized, Repred], 
        ignored_keys: list[str] = [],
        footer: list[list[Button]] = [[]],
        add_back: bool = True, 
        next_button: Optional[Button] = None,
        width: int = 2,
    ) -> Keyboard:
        schema_row: list[Button] = []
        schema: list[Button] = []

        for index, (key, value) in enumerate(dataclass.__dict__.items()):
            if key in ignored_keys:
                continue
            
            is_last = index + 1 == len(dataclass.__dict__)
            emoji = None

            if isinstance(value, Field):
                value: Field
                
                if value.has_warnings:
                    emoji = Emoji.WARN
                
                value = value.value

            elif issubclass(type(value), Repred):
                value: Repred
                value = value.__repr_name__()

            if emoji is None:
                emoji = dataclass.__emojis__.get(key) if value is not None else "🔳"

            translated = dataclass.__translation__.get(key) or key

            if emoji and translated and value is not None:
                text = f"{emoji} {translated}: {common.text.shorten(value)}"
            elif emoji and translated:
                text = f"{emoji} {translated}"
            else:
                text = translated

            button = Button(
                text     = text,
                callback = key,
                color    = Color.BLUE if value is not None else Color.GRAY
            )

            schema_row.append(button)

            if len(schema_row) == width or is_last:
                schema.append(schema_row)
                schema_row = []
        
        for row in footer:
            if not row:
                continue
            
            schema.append(row)

        return cls(
            schematic      = schema,
            add_back    = add_back,
            next_button = next_button
        )

    @classmethod
    def without_back(cls: type[Keyboard]):
        """ ## Shortcut to create `Keyboard` without `Back` button """
        return cls(schematic=[], add_back=False)

    def assign_next(self, button: Optional[Button]):
        """ ## Add `Next` button and return `self` """
        self.next_button = button
        return self

    def _add_footer(self) -> list[list[Optional[Button]]]:
        """ ## Make a copy of `self.schema` and add a footer to it """
        footer = [
            BACK_BUTTON.only_if(self.add_back),
            self.next_button
        ]

        schema = deepcopy(self.schematic)
        schema.append(footer)

        return schema

    @staticmethod
    def filter_schema(schema: list[Button]) -> list[list[Button]]:
        """
        ## Filter out rows that don't contain any buttons
        - `[Button, None, None]` - not filtered out, remains
        - `[None, None, None]`  - filtered out, removed
        """
        filtered: list[list[Button]] = []

        for row in filter(lambda row: any(row), schema):
            filtered.append(row)

        return filtered

    def to_vk(self) -> VkKeyboard:
        """
        ## Convert this keyboard to VK keyboard
        """

        schema = self._add_footer()
        filtered_schema = self.filter_schema(schema)

        vk_kb = VkKeyboard(inline=True)

        # iterate rows - [Button, Button, ...]
        for (i, row) in enumerate(filtered_schema):
            is_last = i == len(filtered_schema) - 1

            # iterate buttons in a row - Button
            for button in row:

                if button is None:
                    continue

                color = Color.to_vk(button.color)
                
                if button.callback is not None:
                    vk_kb.add(VkCallback(button.text, {CMD: button.callback}), color=color)
                elif button.url is not None:
                    vk_kb.add(VkLink(button.url, button.text))
                else:
                    raise ValueError("NO CALLBACK? NO URL?")
            
            if not is_last:
                vk_kb.row()
        
        return vk_kb
    
    def to_tg(self) -> TgKeyboard:
        """
        ## Convert this keyboard to Telegram keyboard
        """

        schema = self._add_footer()
        filtered_schema = self.filter_schema(schema)

        tg_schema: list[list[TgInlineButton]] = []
        
        for row in filtered_schema:
            current_row: list[TgInlineButton] = []

            for button in row:
                if button is None:
                    continue

                if button.callback is not None:
                    tg_btn = TgInlineButton(text=button.text, callback_data=button.callback)
                elif button.url is not None:
                    tg_btn = TgInlineButton(text=button.text, url=button.url)
                else:
                    raise ValueError("NO CALLBACK? NO URL?")
    
                current_row.append(tg_btn)
            
            tg_schema.append(current_row)

        tg_kb = TgKeyboard(inline_keyboard=tg_schema)

        return tg_kb


TRUE_BUTTON = Button(text = Text.TRUE, callback = Payload.TRUE, color = Color.GREEN)
FALSE_BUTTON = Button(text = Text.FALSE, callback = Payload.FALSE, color = Color.RED)
BACK_BUTTON = Button(text = Text.BACK, callback = Payload.BACK)
NEXT_BUTTON = Button(text = Text.NEXT, callback = Payload.NEXT)
SKIP_BUTTON = Button(text = Text.SKIP, callback = Payload.SKIP)
ADD_INIT_BUTTON = Button(text = Text.ADD, callback = Payload.ADD_INIT, color = Color.GREEN)
ADD_HUB_BUTTON = Button(text = Text.ADD, callback = Payload.ADD_HUB, color = Color.GREEN)
CONTINUE_BUTTON = Button(text = Text.CONTINUE, callback = Payload.CONTINUE, color = Color.BLUE)
ADD_ALL_BUTTON = Button(text = Text.ADD_ALL, callback = Payload.ADD_ALL, color = Color.GREEN)
CONFIRM_BUTTON = Button(text = Text.CONFIRM, callback = Payload.CONFIRM, color = Color.GREEN)
NULL_BUTTON = Button(text = Text.NULL, callback = Payload.NULL, color = Color.RED)
REMOVE_BUTTON = Button(text = Text.REMOVE, callback = Payload.REMOVE, color = Color.RED)
REMOVE_ALL_BUTTON = Button(text = Text.REMOVE_ALL, callback = Payload.REMOVE_ALL, color = Color.RED)
DUMP_BUTTON = Button(text = Text.DUMP, callback = Payload.DUMP, color = Color.BLUE)
DUMP_AND_REMOVE_ALL_BUTTON = Button(text = Text.DUMP_AND_REMOVE_ALL, callback = Payload.DUMP_AND_REMOVE_ALL, color = Color.BLUE)
CLEAR_BUTTON = Button(text = Text.CLEAR, callback = Payload.CLEAR, color = Color.RED)

BEGIN_BUTTON = Button(text = Text.BEGIN, callback = Payload.BEGIN)
DO_PIN_BUTTON = Button(text = Text.DO_PIN, callback = Payload.DO_PIN, color = Color.GREEN)
FROM_TEXT_BUTTON = Button(text = Text.FROM_TEXT, callback = Payload.FROM_TEXT, color = Color.GREEN)
MANUALLY_INIT_BUTTON = Button(text = Text.MANUALLY, callback = Payload.MANUALLY_INIT, color = Color.BLUE)
MANUALLY_HUB_BUTTON = Button(text = Text.MANUALLY, callback = Payload.MANUALLY_HUB, color = Color.BLUE)
NEXT_ZOOM_BUTTON = Button(text = Text.NEXT, callback = Payload.NEXT_ZOOM)
FINISH_BUTTON = Button(text = Text.FINISH, callback = Payload.FINISH)

RESEND_BUTTON = Button(text = Text.RESEND, callback = Payload.RESEND, color = Color.BLUE)
GO_HOME_BUTTON = Button(text = Text.GO_HOME, callback = Payload.RESEND, color = Color.BLUE)
GO_TO_HUB_BUTTON = Button(text = Text.GO_TO_HUB, callback = Payload.GO_TO_HUB, color = Color.BLUE)
WEEKLY_BUTTON = Button(text = Text.WEEKLY, callback = Payload.WEEKLY, color = Color.BLUE)
DAILY_BUTTON = Button(text = Text.DAILY, callback = Payload.DAILY, color = Color.BLUE)
FOLD_BUTTON = Button(text = Text.FOLD, callback = Payload.FOLD, color = Color.BLUE)
UNFOLD_BUTTON = Button(text = Text.UNFOLD, callback = Payload.UNFOLD, color = Color.BLUE)
UPDATE_BUTTON = Button(text = Text.UPDATE, callback = Payload.UPDATE, color = Color.BLUE)
SETTINGS_BUTTON = Button(text = Text.SETTINGS, callback = Payload.SETTINGS)

MODE_BUTTON = Button(text = Text.MODE, callback = Payload.MODE)
ME_STUDENT_BUTTON = Button(text = Text.ME_STUDENT, callback = Payload.ME_STUDENT)
ME_TEACHER_BUTTON = Button(text = Text.ME_TEACHER, callback = Payload.ME_TEACHER)
GROUP_BUTTON = Button(text = Text.GROUP, callback = Payload.GROUP, color = Color.BLUE)
TEACHER_BUTTON = Button(text = Text.TEACHER, callback = Payload.TEACHER, color = Color.BLUE)
SHOW_NAMES_BUTTON = Button(text = Text.SHOW_NAMES, callback = Payload.SHOW_NAMES, color = Color.BLUE)
GROUP_MODE_BUTTON = Button(text = Text.GROUP_MODE, callback = Payload.GROUP_MODE, color = Color.BLUE)
TEACHER_MODE_BUTTON = Button(text = Text.TEACHER_MODE, callback = Payload.TEACHER_MODE, color = Color.BLUE)
BROADCAST_BUTTON = Button(text = Text.BROADCAST, callback = Payload.BROADCAST, color = Color.BLUE)
PIN_BUTTON = Button(text = Text.PIN, callback = Payload.PIN, color = Color.BLUE)
ZOOM_BUTTON = Button(text = Text.ZOOM, callback = Payload.ZOOM, color = Color.BLUE)
EXECUTE_CODE_BUTTON = Button(text = Text.EXECUTE_CODE, callback = Payload.EXECUTE_CODE, color = Color.BLUE)
RESET_BUTTON = Button(text = Text.RESET, callback = Payload.RESET, color = Color.RED)

MATERIALS_BUTTON = Button(text = Text.MATERIALS, url = schedule.MATERIALS_URL)
JOURNALS_BUTTON = Button(text = Text.JOURNALS, url = schedule.JOURNALS_URL)
