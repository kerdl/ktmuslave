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
    InlineKeyboardButton as TgInlineButton,
    ForceReply as TgForceReply
)
from dataclasses import dataclass

from src.svc import common
from src.data import Emojized, Repred, Translated, Field, Emoji, format as fmt
from src.svc.vk.keyboard import CMD


class Payload:
    # common buttons
    TRUE       = "true"
    FALSE      = "false"
    BACK       = "back"
    NEXT       = "next"
    SKIP       = "skip"
    PAGE_BACK  = "page_back"
    PAGE_NEXT  = "page_next"

    # Init buttons
    BEGIN      = "begin"
    DO_PIN     = "do_pin"
    FINISH     = "finish"

    # Settings buttons
    GROUP      = "group"
    BROADCAST  = "broadcast"
    PIN        = "pin"
    ZOOM       = "zoom"

    # Zoom buttons
    FROM_TEXT  = "from_text"
    MANUALLY   = "manually"
    ADD        = "add"
    ADD_ALL    = "add_all"
    CONFIRM    = "confirm"
    NULL       = "null"
    REMOVE     = "remove"
    REMOVE_ALL = "remove_all"
    CLEAR      = "clear"
    NEXT_ZOOM  = "next_zoom"

    NAME       = "name"
    URL        = "url"
    ID         = "id"
    PWD        = "pwd"

    # Hub buttons
    RESEND     = "resend"
    WEEKLY     = "weekly"
    DAILY      = "daily"
    FOLD       = "fold"
    UNFOLD     = "unfold"
    UPDATE     = "update"
    SETTINGS   = "settings"

class Text:
    # common buttons
    TRUE       = "✓ ПизДА!"
    FALSE      = "✕ МиНЕТ..."
    BACK       = "← Назад"
    NEXT       = "→ Далее"
    SKIP       = "→ Пропустить"

    # Init buttons
    BEGIN      = "→ Начать"
    DO_PIN     = "✓ Закреплять"
    FINISH     = "→ Закончить"

    # Settings buttons
    GROUP      = "👥 Группа"
    BROADCAST  = "✉️ Рассылка"
    PIN        = "📌 Закрепление"
    ZOOM       = "🖥️ Zoom"

    # Zoom buttons
    FROM_TEXT  = "💬 Из сообщения"
    MANUALLY   = "✍️ Вручную"
    ADD        = "+ Добавить"
    ADD_ALL    = "✓ Добавить всё"
    CONFIRM    = "✓ Подтвердить"
    NULL       = "✕ Обнулить"
    REMOVE     = "✕ Удалить"
    REMOVE_ALL = "✕ Удалить всё"
    CLEAR      = "✕ Очистить"

    # Hub buttons
    RESEND     = "✉️ Новое сообщение"
    WEEKLY     = "⇋ Недельное"
    DAILY      = "⇋ Дневное"
    FOLD       = "⮟ Свернуть"
    UNFOLD     = "⮝ Развернуть"
    UPDATE     = "↻ Обновить"
    SETTINGS   = "⚙️ Настройки"

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


@dataclass
class Button:
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

@dataclass
class Keyboard:
    """
    ## Inline-only cross-platform keyboard
    """
    schema: list[list[Optional[Button]]]
    """ ## Keyboard itself, the 2D array of buttons """
    add_back: bool = True
    """ ## If we should automatically add back to the bottom """
    next_button: Optional[Button] = None
    """ ## `Next` button, will be placed to the right of `Back` """

    @classmethod
    def default(cls: type[Keyboard]) -> Keyboard:
        return cls(schema=[])
    
    @classmethod
    def from_dataclass(
        cls: type[Keyboard],
        dataclass: Union[Translated, Emojized, Repred], 
        footer: list[list[Button]] = [[]],
        add_back: bool = True, 
        next_button: Optional[Button] = None,
    ) -> Keyboard:
        schema: list[Button] = []

        for (key, value) in dataclass.__dict__.items():
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

            schema.append([button])
        
        for row in footer:
            if not row:
                continue
            
            schema.append(row)

        return cls(
            schema      = schema,
            add_back    = add_back,
            next_button = next_button
        )

    @classmethod
    def without_back(cls: type[Keyboard]):
        """ ## Shortcut to create `Keyboard` without `Back` button """
        return cls(schema=[], add_back=False)

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

        schema = deepcopy(self.schema)
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


TRUE_BUTTON       = Button(text = Text.TRUE,       callback = Payload.TRUE,       color = Color.GREEN)
FALSE_BUTTON      = Button(text = Text.FALSE,      callback = Payload.FALSE,      color = Color.RED)
BACK_BUTTON       = Button(text = Text.BACK,       callback = Payload.BACK)
NEXT_BUTTON       = Button(text = Text.NEXT,       callback = Payload.NEXT)
SKIP_BUTTON       = Button(text = Text.SKIP,       callback = Payload.SKIP)
ADD_BUTTON        = Button(text = Text.ADD,        callback = Payload.ADD,        color = Color.GREEN)
ADD_ALL_BUTTON    = Button(text = Text.ADD_ALL,    callback = Payload.ADD_ALL,    color = Color.GREEN)
CONFIRM_BUTTON    = Button(text = Text.CONFIRM,    callback = Payload.CONFIRM,    color = Color.GREEN)
NULL_BUTTON       = Button(text = Text.NULL,       callback = Payload.NULL,       color = Color.RED)
REMOVE_BUTTON     = Button(text = Text.REMOVE,     callback = Payload.REMOVE,     color = Color.RED)
REMOVE_ALL_BUTTON = Button(text = Text.REMOVE_ALL, callback = Payload.REMOVE_ALL, color = Color.RED)
CLEAR_BUTTON      = Button(text = Text.CLEAR,      callback = Payload.CLEAR,      color = Color.RED)

BEGIN_BUTTON      = Button(text = Text.BEGIN,      callback = Payload.BEGIN)
DO_PIN_BUTTON     = Button(text = Text.DO_PIN,     callback = Payload.DO_PIN,     color = Color.GREEN)
FROM_TEXT_BUTTON  = Button(text = Text.FROM_TEXT,  callback = Payload.FROM_TEXT,  color = Color.GREEN)
MANUALLY_BUTTON   = Button(text = Text.MANUALLY,   callback = Payload.MANUALLY,   color = Color.BLUE)
NEXT_ZOOM_BUTTON  = Button(text = Text.NEXT,       callback = Payload.NEXT_ZOOM)
FINISH_BUTTON     = Button(text = Text.FINISH,     callback = Payload.FINISH)

RESEND_BUTTON     = Button(text = Text.RESEND,     callback = Payload.RESEND,     color = Color.BLUE)
WEEKLY_BUTTON     = Button(text = Text.WEEKLY,     callback = Payload.WEEKLY,     color = Color.BLUE)
DAILY_BUTTON      = Button(text = Text.DAILY,      callback = Payload.DAILY,      color = Color.BLUE)
FOLD_BUTTON       = Button(text = Text.FOLD,       callback = Payload.FOLD,       color = Color.BLUE)
UNFOLD_BUTTON     = Button(text = Text.UNFOLD,     callback = Payload.UNFOLD,     color = Color.BLUE)
UPDATE_BUTTON     = Button(text = Text.UPDATE,     callback = Payload.UPDATE,     color = Color.BLUE)
SETTINGS_BUTTON   = Button(text = Text.SETTINGS,   callback = Payload.SETTINGS)

GROUP_BUTTON      = Button(text = Text.GROUP,      callback = Payload.GROUP,      color = Color.BLUE)
BROADCAST_BUTTON  = Button(text = Text.BROADCAST,  callback = Payload.BROADCAST,  color = Color.BLUE)
PIN_BUTTON        = Button(text = Text.PIN,        callback = Payload.PIN,        color = Color.BLUE)
ZOOM_BUTTON       = Button(text = Text.ZOOM,       callback = Payload.ZOOM,       color = Color.BLUE)