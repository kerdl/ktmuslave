from svc.common import CommonMessage, MessageSource, messages
from svc.common.context import VkCtx, TgCtx
from svc.common.keyboard import Keyboard, Button


async def main(message: CommonMessage):

    answer_message = messages.format_welcome(message.is_group_chat)
    answer_keyboard = Keyboard([
        [Button("→ Начать", "begin")]
    ])

    match message.src:
        case MessageSource.VK:
            m = message.vk

            await m.answer(f"{answer_message}", keyboard=answer_keyboard.to_vk().get_json(), dont_parse_links=True)
        case MessageSource.TG:
            m = message.tg

            await m.answer(f"{answer_message}", reply_markup=answer_keyboard.to_tg())

async def group(message: CommonMessage):
    ...

async def unknown_group(message: CommonMessage):
    ...

async def schedule_broadcast(message: CommonMessage):
    ...

async def should_pin(message: CommonMessage):
    ...

async def finish(message: CommonMessage):
    ...