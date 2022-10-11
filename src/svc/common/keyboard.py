from __future__ import annotations
from copy import deepcopy
from typing import Optional
from typing import Literal
from vkbottle import (
    Keyboard as VkKeyboard, 
    Callback as VkCallback,
    KeyboardButtonColor as VkColor
)
from aiogram.types import (
    InlineKeyboardMarkup as TgKeyboard, 
    InlineKeyboardButton as TgInlineButton,
    ForceReply as TgForceReply
)
from dataclasses import dataclass
from src.svc import common

from src.svc.vk.keyboard import CMD


class Payload:
    TRUE  = "true"
    FALSE = "false"
    BACK  = "back"
    NEXT  = "next"
    SKIP  = "skip"
    ADD   = "add"

    PAGE_BACK = "page_back"
    PAGE_NEXT = "page_next"

    BEGIN     = "begin"
    DO_PIN    = "do_pin"
    FROM_TEXT = "from_text"
    MANUALLY  = "manually"
    FINISH    = "finish"

class Text:
    TRUE  = "✓ ПизДА!"
    FALSE = "✕ МиНЕТ..."
    BACK  = "← Назад"
    NEXT  = "→ Далее"
    SKIP  = "→ Пропустить"
    ADD   = "✓ Добавить"

    BEGIN     = "→ Начать"
    DO_PIN    = "✓ Закреплять"
    FROM_TEXT = "❞ Из сообщения"
    MANUALLY  = "• Вручную"
    FINISH    = "→ Закончить"

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
    """
    Represents a common button

    - `text` - button text
    - `callback` - payload that will be sent
    on press
    """
    text: str
    callback: str
    color: Optional[COLOR_LITERAL] = None

    def only_if(self, condition: bool) -> Optional[Button]:
        """ ## Return `Button` if `condition` is `True`, else return `None` """
        if condition is True:
            return self
        else:
            return None

@dataclass
class Keyboard:
    """
    ## Inline-only cross-platform keyboard
    """
    schema: list[list[Optional[Button]]]
    add_back: bool = True
    next_button: Optional[Button] = None

    @classmethod
    def default(cls: type[Keyboard]):
        return cls(schema=[])
    
    @classmethod
    def without_back(cls: type[Keyboard]):
        return cls(schema=[], add_back=False)

    def assign_next(self, button: Optional[Button]):
        self.next_button = button
        return self

    def add_footer(self) -> list[list[Optional[Button]]]:
        footer = [
            BACK_BUTTON.only_if(self.add_back),
            self.next_button
        ]

        schema = deepcopy(self.schema)
        schema.append(footer)

        return schema

    @staticmethod
    def filter_schema(schema: list[Button]) -> list[list[Button]]:
        filtered: list[list[Button]] = []

        for row in filter(lambda row: any(row), schema):
            filtered.append(row)

        return filtered

    def to_vk(self) -> VkKeyboard:
        """
        ## Convert this keyboard to VK keyboard
        """

        schema = self.add_footer()
        filtered_schema = self.filter_schema(schema)

        vk_kb = VkKeyboard(inline=True)

        for (i, row) in enumerate(filtered_schema):
            is_last = i == len(filtered_schema) - 1

            for button in row:

                if button is None:
                    continue

                color = Color.to_vk(button.color)
                vk_kb.add(VkCallback(button.text, {CMD: button.callback}), color=color)
            
            if not is_last:
                vk_kb.row()
        
        return vk_kb
    
    def to_tg(self) -> TgKeyboard:
        """
        ## Convert this keyboard to Telegram keyboard
        """

        schema = self.add_footer()
        filtered_schema = self.filter_schema(schema)

        tg_schema: list[list[TgInlineButton]] = []
        
        for row in filtered_schema:
            current_row: list[TgInlineButton] = []

            for button in row:

                if button is None:
                    continue

                tg_btn = TgInlineButton(text=button.text, callback_data=button.callback)
                current_row.append(tg_btn)
            
            tg_schema.append(current_row)

        tg_kb = TgKeyboard(inline_keyboard=tg_schema)

        return tg_kb


TRUE_BUTTON   = Button(Text.TRUE, Payload.TRUE, Color.GREEN)
FALSE_BUTTON  = Button(Text.FALSE, Payload.FALSE, Color.RED)
BACK_BUTTON   = Button(Text.BACK, Payload.BACK)
NEXT_BUTTON   = Button(Text.NEXT, Payload.NEXT)
SKIP_BUTTON   = Button(Text.SKIP, Payload.SKIP)
ADD_BUTTON    = Button(Text.ADD, Payload.ADD)

BEGIN_BUTTON     = Button(Text.BEGIN, Payload.BEGIN)
DO_PIN_BUTTON    = Button(Text.DO_PIN, Payload.DO_PIN, Color.GREEN)
FROM_TEXT_BUTTON = Button(Text.FROM_TEXT, Payload.FROM_TEXT, Color.GREEN)
MANUALLY_BUTTON  = Button(Text.MANUALLY, Payload.MANUALLY, Color.BLUE)
FINISH_BUTTON    = Button(Text.FINISH, Payload.FINISH)