from loguru import logger

from svc.common import CommonMessage, CommonEvent, Source, messages
from svc.common.states.tree import Init
from svc.common.keyboard import Keyboard, Button


async def main(message: CommonMessage):
    answer_message = messages.format_welcome(message.is_group_chat)
    answer_keyboard = Keyboard([
        [Button("→ Начать", "begin")]
    ])

    match message.src:
        case Source.VK:
            vk_message = message.vk

            await vk_message.answer(f"{answer_message}", keyboard=answer_keyboard.to_vk().get_json(), dont_parse_links=True)
        case Source.TG:
            tg_message = message.tg

            await tg_message.answer(f"{answer_message}", reply_markup=answer_keyboard.to_tg())

async def begin(event: CommonEvent):
    match event.src:
        case Source.VK:
            ctx = event.vk_ctx

            ctx.navigator.append(Init.I_GROUP)

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