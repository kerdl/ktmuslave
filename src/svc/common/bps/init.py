from loguru import logger

from src import defs
from svc.common import CommonMessage, CommonEvent, Source, messages
from svc.common.states.formatter import format_tree
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
            ctx = message.vk_ctx

            last_bot_message = await vk_message.answer(
                message=answer_message, 
                keyboard=answer_keyboard.to_vk().get_json(), 
                dont_parse_links=True
            )

            ctx.last_bot_message = last_bot_message
        case Source.TG:
            tg_message = message.tg

            await tg_message.answer(
                text=answer_message, 
                reply_markup=answer_keyboard.to_tg()
            )

async def begin(event: CommonEvent):
    answer_message = messages.format_group(
        groups=["1КДД10", "1КДД12", "1КДД14", "1КДД16"]
    )

    match event.src:
        case Source.VK:
            evt = event.vk
            evt_object = evt["object"]

            ctx = event.vk_ctx
            ctx.navigator.append(Init.I_GROUP)

            tree = format_tree(ctx.navigator.trace)

            answer_message = f"{tree}\n\n{answer_message}"

            await defs.vk_bot.api.messages.edit(
                peer_id=evt_object["peer_id"],
                message=answer_message,
                conversation_message_id=evt_object["conversation_message_id"]
            )

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