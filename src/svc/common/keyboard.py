from vkbottle import (
    Keyboard as VkKeyboard, 
    Text as VkText
)
from aiogram.types import (
    InlineKeyboardMarkup as TgKeyboard, 
    KeyboardButton as TgButton,
    InlineKeyboardButton as TgInlineButton,
)
from dataclasses import dataclass
from typing import Union


@dataclass
class Button:
    """
    Represents a common button

    - `text` - button text
    """
    text: str

@dataclass
class Keyboard:
    schema: list[list[Button]]
    one_time: bool = False
    inline: bool = True

    def to_vk(self) -> VkKeyboard:
        """
        ## Convert this keyboard to VK keyboard
        """

        vk_kb = VkKeyboard(self.one_time, self.inline)
        
        for (i, row) in enumerate(self.schema):
            is_last = i == len(self.schema) - 1

            for button in row:
                vk_kb.add(VkText(button.text))
            
            if not is_last:
                vk_kb.row()
        
        return vk_kb
    
    def to_tg(self) -> TgKeyboard:
        """
        ## Convert this keyboard to Telegram keyboard
        """

        # if `self.inline` is `True`, using `TgInlineButton`, else `TgButton`
        schema: Union[list[list[TgInlineButton]], list[TgButton]] = []
        
        for row in self.schema:
            current_row: Union[list[TgInlineButton], list[TgButton]] = []

            for button in row:
                if self.inline:
                    tg_btn = TgInlineButton(text=button.text, callback_data="hui")
                else:
                    tg_btn = TgButton(text=button.text)

                current_row.append(tg_btn)
            
            schema.append(current_row)

        tg_kb = TgKeyboard(inline_keyboard=schema)

        return tg_kb
