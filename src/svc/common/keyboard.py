from vkbottle import (
    Keyboard as VkKeyboard, 
    Callback as VkCallback
)
from aiogram.types import (
    InlineKeyboardMarkup as TgKeyboard, 
    InlineKeyboardButton as TgInlineButton,
)
from dataclasses import dataclass

class Payload:
    BACK = "back"
    BEGIN = "begin"

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

@dataclass
class Keyboard:
    """
    ## Inline-only cross-platform keyboard
    """
    schema: list[list[Button]]
    one_time: bool = False

    def to_vk(self) -> VkKeyboard:
        """
        ## Convert this keyboard to VK keyboard
        """

        vk_kb = VkKeyboard(self.one_time, inline=True)
        
        for (i, row) in enumerate(self.schema):
            is_last = i == len(self.schema) - 1

            for button in row:
                vk_kb.add(VkCallback(button.text, {"cmd": button.callback}))
            
            if not is_last:
                vk_kb.row()
        
        return vk_kb
    
    def to_tg(self) -> TgKeyboard:
        """
        ## Convert this keyboard to Telegram keyboard
        """

        schema: list[list[TgInlineButton]] = []
        
        for row in self.schema:
            current_row: list[TgInlineButton] = []

            for button in row:
                tg_btn = TgInlineButton(text=button.text, callback_data=button.callback)
                current_row.append(tg_btn)
            
            schema.append(current_row)

        tg_kb = TgKeyboard(inline_keyboard=schema)

        return tg_kb
