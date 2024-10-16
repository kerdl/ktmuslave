from __future__ import annotations
from copy import deepcopy
from typing import Any, Optional, Union
from typing import Literal
from vkbottle import (
    Keyboard as VkKeyboard, 
    Callback as VkCallback,
    OpenLink as VkLink,
    KeyboardButtonColor as VkColor
)
from aiogram.types import (
    InlineKeyboardMarkup as TgKeyboard, 
    InlineKeyboardButton as TgInlineButton
)
from pydantic import BaseModel, Field as PydField
from src import defs
from src.svc import common
from src.data import (
    Emojized,
    Repred,
    Translated,
    DataField,
    Emoji,
    format as fmt
)
from src.svc.vk.keyboard import CMD


class Payload:
    # common buttons
    TRUE = "true"
    FALSE = "false"
    BACK = "back"
    FORWARD = "forward"
    PAGE_PREVIOUS = "page_previous"
    PAGE_NEXT = "page_next"
    PAGE_PREVIOUS_JUMP = "page_previous_jump"
    PAGE_NEXT_JUMP = "page_next_jump"
    SKIP = "skip"
    CONTINUE = "continue"

    # Init buttons
    BEGIN = "begin"
    DO_PIN = "do_pin"
    FINISH = "finish"

    # Settings buttons
    MODE = "mode"
    ME_STUDENT = "me_student"
    ME_TEACHER = "me_teacher"
    GROUP = "group"
    TEACHER = "teacher"
    SHOW_NAMES = "show_names"
    GROUP_MODE = "group_mode"
    TEACHER_MODE = "teacher_mode"
    BROADCAST = "broadcast"
    PIN = "pin"
    ZOOM = "zoom"
    TIME = "time"
    EXECUTE_CODE = "execute_code"
    RESET = "reset"

    # Zoom buttons
    FROM_TEXT = "from_text"
    MANUALLY_INIT = "manually_init"
    MANUALLY_HUB = "manually_hub"
    BROWSER = "browser"
    ADD_INIT = "add_init"
    ADD_HUB = "add_hub"
    ADD_ALL = "add_all"
    CONFIRM = "confirm"
    NULL = "null"
    REMOVE = "remove"
    REMOVE_ALL = "remove_all"
    DUMP = "dump"
    DUMP_AND_REMOVE_ALL = "dump_and_remove_all"
    CLEAR = "clear"
    NEXT_ZOOM = "next_zoom"

    NAME = "name"
    URL = "url"
    ID = "id"
    PWD = "pwd"
    HOST_KEY = "host_key"
    NOTES = "notes"

    # Hub buttons
    RESEND = "resend"
    GO_TO_HUB = "go_to_hub"
    WEEKLY = "weekly"
    DAILY = "daily"
    FOLD = "fold"
    UNFOLD = "unfold"
    UPDATE = "update"
    SETTINGS = "settings"

class Text:
    # common buttons
    TRUE = "✓ ПизДА!"
    FALSE = "✕ МиНЕТ..."
    BACK = "← Назад"
    FORWARD = "→ Далее"
    PREVIOUS = "←"
    NEXT = "→"
    #PREVIOUS_JUMP = "⇤"
    #NEXT_JUMP = "⇥"
    #PREVIOUS_JUMP = "│ ←"
    #NEXT_JUMP = "→ │"
    PREVIOUS_JUMP = "⇇"
    NEXT_JUMP = "⇉"
    DEAD_END = " "
    SKIP = "→ Пропустить"
    CONTINUE = "→ Продолжить"
    UNSET = "⚪"

    # Init buttons
    BEGIN = "→ Начать"
    DO_PIN = "✓ Закреплять"
    FINISH = "→ Закончить"

    # Settings buttons
    MODE = "⛓️ Режим"
    ME_STUDENT = "🧑‍🎓 Группа"
    ME_TEACHER = "🧑‍🏫 Препод"
    GROUP = "👥 Группа"
    SHOW_NAMES = "👀 Показать имена"
    GROUP_MODE = "🔁 Режим группы"
    TEACHER_MODE = "🔁 Режим препода"
    TEACHER = "👤 Препод"
    BROADCAST = "✉️ Рассылка"
    PIN = "📌 Закреп"
    ZOOM = "🖥️ Zoom"
    TIME = "🕒 Время"
    EXECUTE_CODE = "🛠️"
    RESET = "🗑️ Сбросить всё"

    # Zoom buttons
    FROM_TEXT = "💬 Из сообщения"
    MANUALLY = "✍️ Вручную"
    ADD = "+ Добавить"
    ADD_ALL = "✓ Добавить всё"
    CONFIRM = "✓ Подтвердить"
    NULL = "✕ Обнулить"
    REMOVE = "✕ Удалить"
    REMOVE_ALL = "✕ Удалить всё"
    DUMP = "💾 Дамп"
    CLEAR = "✕ Очистить"
    DUMP_AND_REMOVE_ALL = f"{DUMP} и {REMOVE_ALL}"

    # Hub buttons
    RESEND = "✉️ Новое сообщение"
    GO_HOME = "🏠 Вернуться"
    GO_TO_HUB = "🏠 В хаб"
    SETTINGS = "⚙️ Настройки"
    SCHEDULES = "Расписания"
    MATERIALS = "Материалы"
    JOURNALS = "Журналы"

COLOR_LITERAL = Literal["gray", "blue", "green", "red"]

class Color:
    """ # Button colors only for VK """
    GRAY = "gray"
    BLUE = "blue"
    GREEN = "green"
    RED = "red"

    @staticmethod
    def from_vk(color: VkColor) -> Optional[COLOR_LITERAL]:
        mapping = {
            VkColor.SECONDARY: Color.GRAY,
            VkColor.PRIMARY: Color.BLUE,
            VkColor.POSITIVE: Color.GREEN,
            VkColor.NEGATIVE: Color.RED
        }

        return mapping.get(color)
    
    @staticmethod
    def to_vk(color: COLOR_LITERAL) -> Optional[VkColor]:
        mapping = {
            Color.GRAY: VkColor.SECONDARY,
            Color.BLUE: VkColor.PRIMARY,
            Color.GREEN: VkColor.POSITIVE,
            Color.RED: VkColor.NEGATIVE
        }

        return mapping.get(color)


class Button(BaseModel):
    """ # Represents a common button """
    text: str
    """ # Button text """
    callback: Optional[str] = None
    """ # Payload that will be sent to us on press """
    url: Optional[str] = None
    """ # Button url """
    color: Optional[COLOR_LITERAL] = None
    """ # Controls tilt angle on `Messerschmitt Me 262` """

    def only_if(self, condition: bool) -> Optional[Button]:
        """ # Return `Button` if `condition` is `True`, else return `None` """
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
    # Inline-only cross-platform keyboard
    """
    schematic: list[list[Optional[Button]]] = PydField(default_factory=list)
    """ # Keyboard itself, the 2D array of buttons """
    add_back: bool = True
    """ # If we should automatically add back to the bottom """
    next_button: Optional[Button] = None
    """ # `Next` button, will be placed next to `Back` """
    
    def __init__(
        __pydantic_self__,
        schematic: Optional[list[list[Optional[Button]]]] = None,
        **data: Any
    ) -> None:
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
                btn = Button.model_validate(button)
                parsed_row.append(btn)
            
            if not parsed_row: continue

            parsed_schematic.append(parsed_row)
            parsed_row = []
        
        return parsed_schematic

    @classmethod
    def hub_default(
        cls: Keyboard,
        is_previous_dead_end: bool = False,
        is_previous_jump_dead_end: bool = False,
        is_next_dead_end: bool = False,
        is_next_jump_dead_end: bool = False
    ) -> Keyboard:
        is_all_dead_end = all([
            is_previous_dead_end,
            is_previous_jump_dead_end,
            is_next_dead_end,
            is_next_jump_dead_end
        ])
        return cls([
            [
                # previous
                PAGE_PREVIOUS_BUTTON.only_if(
                    not is_previous_dead_end
                ),
                PAGE_PREVIOUS_DEAD_END_BUTTON.only_if(
                    is_previous_dead_end and not is_all_dead_end
                ),
                
                # previous jump
                PAGE_PREVIOUS_JUMP_BUTTON.only_if(
                    not is_previous_jump_dead_end
                ),
                PAGE_PREVIOUS_JUMP_DEAD_END_BUTTON.only_if(
                    is_previous_jump_dead_end and not is_all_dead_end
                ),
               
                # next jump
                PAGE_NEXT_JUMP_BUTTON.only_if(
                    not is_next_jump_dead_end
                ),
                PAGE_NEXT_JUMP_DEAD_END_BUTTON.only_if(
                    is_next_jump_dead_end and not is_all_dead_end
                ),
               
                # next
                PAGE_NEXT_BUTTON.only_if(
                    not is_next_dead_end
                ),
                PAGE_NEXT_DEAD_END_BUTTON.only_if(
                    is_next_dead_end and not is_all_dead_end
                )
            ],
            [RESEND_BUTTON],
            [SETTINGS_BUTTON],
            [SCHEDULES_BUTTON],
            [MATERIALS_BUTTON, JOURNALS_BUTTON],
        ], add_back=False)

    @classmethod
    def temp_identifier_hub(
        cls: Keyboard,
        is_previous_dead_end: bool = False,
        is_previous_jump_dead_end: bool = False,
        is_next_dead_end: bool = False,
        is_next_jump_dead_end: bool = False
    ) -> Keyboard:
        is_all_dead_end = all([
            is_previous_dead_end,
            is_previous_jump_dead_end,
            is_next_dead_end,
            is_next_jump_dead_end
        ])
        return cls([
            [
                # previous
                PAGE_PREVIOUS_BUTTON.only_if(
                    not is_previous_dead_end
                ),
                PAGE_PREVIOUS_DEAD_END_BUTTON.only_if(
                    is_previous_dead_end and not is_all_dead_end
                ),
                
                # previous jump
                PAGE_PREVIOUS_JUMP_BUTTON.only_if(
                    not is_previous_jump_dead_end
                ),
                PAGE_PREVIOUS_JUMP_DEAD_END_BUTTON.only_if(
                    is_previous_jump_dead_end and not is_all_dead_end
                ),
               
                # next jump
                PAGE_NEXT_JUMP_BUTTON.only_if(
                    not is_next_jump_dead_end
                ),
                PAGE_NEXT_JUMP_DEAD_END_BUTTON.only_if(
                    is_next_jump_dead_end and not is_all_dead_end
                ),
               
                # next
                PAGE_NEXT_BUTTON.only_if(
                    not is_next_dead_end
                ),
                PAGE_NEXT_DEAD_END_BUTTON.only_if(
                    is_next_dead_end and not is_all_dead_end
                )
            ],
            [GO_HOME_BUTTON],
            [SCHEDULES_BUTTON],
            [MATERIALS_BUTTON, JOURNALS_BUTTON],
        ], add_back=False)

    @classmethod
    def hub_broadcast_default(
        cls: Keyboard,
        is_previous_dead_end: bool = False,
        is_previous_jump_dead_end: bool = False,
        is_next_dead_end: bool = False,
        is_next_jump_dead_end: bool = False
    ) -> Keyboard:
        is_all_dead_end = all([
            is_previous_dead_end,
            is_previous_jump_dead_end,
            is_next_dead_end,
            is_next_jump_dead_end
        ])
        return cls([
            [
                # previous
                PAGE_PREVIOUS_BUTTON.only_if(
                    not is_previous_dead_end
                ),
                PAGE_PREVIOUS_DEAD_END_BUTTON.only_if(
                    is_previous_dead_end and not is_all_dead_end
                ),
                
                # previous jump
                PAGE_PREVIOUS_JUMP_BUTTON.only_if(
                    not is_previous_jump_dead_end
                ),
                PAGE_PREVIOUS_JUMP_DEAD_END_BUTTON.only_if(
                    is_previous_jump_dead_end and not is_all_dead_end
                ),
               
                # next jump
                PAGE_NEXT_JUMP_BUTTON.only_if(
                    not is_next_jump_dead_end
                ),
                PAGE_NEXT_JUMP_DEAD_END_BUTTON.only_if(
                    is_next_jump_dead_end and not is_all_dead_end
                ),
               
                # next
                PAGE_NEXT_BUTTON.only_if(
                    not is_next_dead_end
                ),
                PAGE_NEXT_DEAD_END_BUTTON.only_if(
                    is_next_dead_end and not is_all_dead_end
                )
            ],
            [RESEND_BUTTON],
            [SETTINGS_BUTTON],
            [SCHEDULES_BUTTON],
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

            if isinstance(value, DataField):
                value: DataField
                
                if value.has_warnings:
                    emoji = Emoji.WARN
                
                value = value.value

            elif issubclass(type(value), Repred):
                value: Repred
                value = value.__repr_name__()

            if emoji is None:
                emoji = dataclass.__emojis__.get(key) if value is not None else Text.UNSET

            translated = dataclass.__translation__.get(key) or key

            if emoji and translated and value is not None:
                text=f"{emoji} {translated}: {common.text.shorten(value)}"
            elif emoji and translated:
                text=f"{emoji} {translated}"
            else:
                text=translated

            button = Button(
                text=text,
                callback=key,
                color=Color.BLUE if value is not None else Color.GRAY
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
            schematic=schema,
            add_back=add_back,
            next_button=next_button
        )

    @classmethod
    def without_back(cls: type[Keyboard]):
        """ # Shortcut to create `Keyboard` without `Back` button """
        return cls(schematic=[], add_back=False)

    def assign_next(self, button: Optional[Button]):
        """ # Add `Next` button and return `self` """
        self.next_button = button
        return self

    def _add_footer(self) -> list[list[Optional[Button]]]:
        """ # Make a copy of `self.schema` and add a footer to it """
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
        # Filter out rows that don't contain any buttons
        - `[Button, None, None]` - not filtered out, remains
        - `[None, None, None]` - filtered out, removed
        """
        filtered: list[list[Button]] = []

        for row in filter(lambda row: any(row), schema):
            filtered.append(row)

        return filtered

    def to_vk(self) -> VkKeyboard:
        """
        # Convert this keyboard to VK keyboard
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

                color=Color.to_vk(button.color)
                
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
        # Convert this keyboard to Telegram keyboard
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
                    tg_btn = TgInlineButton(
                        text=button.text,
                        callback_data=button.callback
                    )
                elif button.url is not None:
                    tg_btn = TgInlineButton(
                        text=button.text,
                        url=button.url
                    )
                else:
                    raise ValueError("NO CALLBACK? NO URL?")
    
                current_row.append(tg_btn)
            
            tg_schema.append(current_row)

        tg_kb = TgKeyboard(inline_keyboard=tg_schema)

        return tg_kb


TRUE_BUTTON = Button(
    text=Text.TRUE,
    callback=Payload.TRUE,
    color=Color.GREEN
)
FALSE_BUTTON = Button(
    text=Text.FALSE,
    callback=Payload.FALSE,
    color=Color.RED
)
BACK_BUTTON = Button(
    text=Text.BACK,
    callback=Payload.BACK
)
FORWARD_BUTTON = Button(
    text=Text.FORWARD,
    callback=Payload.FORWARD
)
PAGE_PREVIOUS_BUTTON = Button(
    text=Text.PREVIOUS,
    callback=Payload.PAGE_PREVIOUS
)
PAGE_NEXT_BUTTON = Button(
    text=Text.NEXT,
    callback=Payload.PAGE_NEXT
)
PAGE_PREVIOUS_JUMP_BUTTON = Button(
    text=Text.PREVIOUS_JUMP,
    callback=Payload.PAGE_PREVIOUS_JUMP
)
PAGE_NEXT_JUMP_BUTTON = Button(
    text=Text.NEXT_JUMP,
    callback=Payload.PAGE_NEXT_JUMP
)
PAGE_PREVIOUS_DEAD_END_BUTTON = Button(
    text=Text.DEAD_END,
    callback=Payload.PAGE_PREVIOUS
)
PAGE_NEXT_DEAD_END_BUTTON = Button(
    text=Text.DEAD_END,
    callback=Payload.PAGE_NEXT
)
PAGE_PREVIOUS_JUMP_DEAD_END_BUTTON = Button(
    text=Text.DEAD_END,
    callback=Payload.PAGE_PREVIOUS_JUMP
)
PAGE_NEXT_JUMP_DEAD_END_BUTTON = Button(
    text=Text.DEAD_END,
    callback=Payload.PAGE_NEXT_JUMP
)
SKIP_BUTTON = Button(
    text=Text.SKIP,
    callback=Payload.SKIP
)
ADD_INIT_BUTTON = Button(
    text=Text.ADD,
    callback=Payload.ADD_INIT,
    color=Color.GREEN
)
ADD_HUB_BUTTON = Button(
    text=Text.ADD,
    callback=Payload.ADD_HUB,
    color=Color.GREEN
)
CONTINUE_BUTTON = Button(
    text=Text.CONTINUE,
    callback=Payload.CONTINUE,
    color=Color.BLUE
)
ADD_ALL_BUTTON = Button(
    text=Text.ADD_ALL,
    callback=Payload.ADD_ALL,
    color=Color.GREEN
)
CONFIRM_BUTTON = Button(
    text=Text.CONFIRM,
    callback=Payload.CONFIRM,
    color=Color.GREEN
)
NULL_BUTTON = Button(
    text=Text.NULL,
    callback=Payload.NULL,
    color=Color.RED
)
REMOVE_BUTTON = Button(
    text=Text.REMOVE,
    callback=Payload.REMOVE,
    color=Color.RED
)
REMOVE_ALL_BUTTON = Button(
    text=Text.REMOVE_ALL,
    callback=Payload.REMOVE_ALL,
    color=Color.RED
)
DUMP_BUTTON = Button(
    text=Text.DUMP,
    callback=Payload.DUMP,
    color=Color.BLUE
)
DUMP_AND_REMOVE_ALL_BUTTON = Button(
    text=Text.DUMP_AND_REMOVE_ALL,
    callback=Payload.DUMP_AND_REMOVE_ALL,
    color=Color.BLUE
)
CLEAR_BUTTON = Button(
    text=Text.CLEAR,
    callback=Payload.CLEAR,
    color=Color.RED
)


BEGIN_BUTTON = Button(
    text=Text.BEGIN,
    callback=Payload.BEGIN
)
DO_PIN_BUTTON = Button(
    text=Text.DO_PIN,
    callback=Payload.DO_PIN,
    color=Color.GREEN
)
FROM_TEXT_BUTTON = Button(
    text=Text.FROM_TEXT,
    callback=Payload.FROM_TEXT,
    color=Color.GREEN
)
MANUALLY_INIT_BUTTON = Button(
    text=Text.MANUALLY,
    callback=Payload.MANUALLY_INIT,
    color=Color.BLUE
)
MANUALLY_HUB_BUTTON = Button(
    text=Text.MANUALLY,
    callback=Payload.MANUALLY_HUB,
    color=Color.BLUE
)
NEXT_ZOOM_BUTTON = Button(
    text=Text.FORWARD,
    callback=Payload.NEXT_ZOOM
)
FINISH_BUTTON = Button(
    text=Text.FINISH,
    callback=Payload.FINISH
)


RESEND_BUTTON = Button(
    text=Text.RESEND,
    callback=Payload.RESEND,
    color=Color.BLUE
)
GO_HOME_BUTTON = Button(
    text=Text.GO_HOME,
    callback=Payload.RESEND,
    color=Color.BLUE
)
GO_TO_HUB_BUTTON = Button(
    text=Text.GO_TO_HUB,
    callback=Payload.GO_TO_HUB,
    color=Color.BLUE
)
SETTINGS_BUTTON = Button(
    text=Text.SETTINGS,
    callback=Payload.SETTINGS
)


MODE_BUTTON = Button(
    text=Text.MODE,
    callback=Payload.MODE
)
ME_STUDENT_BUTTON = Button(
    text=Text.ME_STUDENT,
    callback=Payload.ME_STUDENT
)
ME_TEACHER_BUTTON = Button(
    text=Text.ME_TEACHER,
    callback=Payload.ME_TEACHER
)
GROUP_BUTTON = Button(
    text=Text.GROUP,
    callback=Payload.GROUP,
    color=Color.BLUE
)
TEACHER_BUTTON = Button(
    text=Text.TEACHER,
    callback=Payload.TEACHER,
    color=Color.BLUE
)
SHOW_NAMES_BUTTON = Button(
    text=Text.SHOW_NAMES,
    callback=Payload.SHOW_NAMES,
    color=Color.BLUE
)
GROUP_MODE_BUTTON = Button(
    text=Text.GROUP_MODE,
    callback=Payload.GROUP_MODE,
    color=Color.BLUE
)
TEACHER_MODE_BUTTON = Button(
    text=Text.TEACHER_MODE,
    callback=Payload.TEACHER_MODE,
    color=Color.BLUE
)
BROADCAST_BUTTON = Button(
    text=Text.BROADCAST,
    callback=Payload.BROADCAST,
    color=Color.BLUE
)
PIN_BUTTON = Button(
    text=Text.PIN,
    callback=Payload.PIN,
    color=Color.BLUE
)
ZOOM_BUTTON = Button(
    text=Text.ZOOM,
    callback=Payload.ZOOM,
    color=Color.BLUE
)
TIME_BUTTON = Button(
    text=Text.TIME,
    callback=Payload.TIME,
    color=Color.BLUE
)
EXECUTE_CODE_BUTTON = Button(
    text=Text.EXECUTE_CODE,
    callback=Payload.EXECUTE_CODE,
    color=Color.BLUE
)
RESET_BUTTON = Button(
    text=Text.RESET,
    callback=Payload.RESET,
    color=Color.RED
)


SCHEDULES_BUTTON = Button(
    text=Text.SCHEDULES,
    url=defs.settings.urls.schedules
) if defs.settings.urls and defs.settings.urls.schedules else None
MATERIALS_BUTTON = Button(
    text=Text.MATERIALS,
    url=defs.settings.urls.materials
) if defs.settings.urls and defs.settings.urls.materials else None
JOURNALS_BUTTON = Button(
    text=Text.JOURNALS,
    url=defs.settings.urls.journals
) if defs.settings.urls and defs.settings.urls.journals else None
