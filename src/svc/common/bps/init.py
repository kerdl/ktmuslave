from loguru import logger

from src import defs
from src.svc.common import CommonEverything, messages
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import Init
from src.svc.common.keyboard import Keyboard, Button, Payload
from src.svc.common.filter import StateFilter, PayloadFilter
from src.svc.common.router import r


@r.on_everything(StateFilter(Init.I_GROUP))
async def group(everything: CommonEverything):
    if everything.is_from_vk:
        footer_addition = messages.format_mention_me("@pizda")

    elif everything.is_from_tg:
        footer_addition = messages.format_reply_to_me()


    answer_text = (
        messages.Builder()
                .add(states_fmt.tree(everything.navigator.trace))
                .add(messages.format_groups(["хуй", "соси", "губой", "тряси"]))
                .add(messages.format_group_input())
                .add(footer_addition)
                .make()
    )
    answer_keyboard = Keyboard([
        [Button("← Назад", Payload.BACK)]
    ])


    if everything.is_from_event:
        event = everything.event

        await event.edit_message(
            text     = answer_text,
            keyboard = answer_keyboard
        )
    elif everything.is_from_message:
        message = everything.message

        await message.answer(
            text     = answer_text,
            keyboard = answer_keyboard
        )


@r.on_callback(StateFilter(Init.I_MAIN), PayloadFilter(Payload.BEGIN))
async def begin(everything: CommonEverything):
    everything.navigator.append(Init.I_GROUP)

    return await group(everything)


@r.on_everything(StateFilter(Init.I_MAIN))
async def main(everything: CommonEverything):
    answer_message = (
        messages.Builder()
                .add(messages.format_welcome(everything.is_group_chat))
                .add(messages.format_press_begin())
                .make()
    )
    answer_keyboard = Keyboard([
        [Button("→ Начать", Payload.BEGIN)]
    ])

    if everything.is_from_message:
        message = everything.message

        await message.answer(
            text     = answer_message,
            keyboard = answer_keyboard,
        )
    
    elif everything.is_from_event:
        event = everything.event

        await event.edit_message(
            text     = answer_message,
            keyboard = answer_keyboard,
        )


async def unknown_group(everything: CommonEverything):
    ...


async def schedule_broadcast(everything: CommonEverything):
    ...


async def should_pin(everything: CommonEverything):
    ...


async def finish(everything: CommonEverything):
    ...


STATE_MAP = {
    Init.I_MAIN: main,
    Init.I_GROUP: group,
    Init.II_UNKNOWN_GROUP: unknown_group,
    Init.I_SCHEDULE_BROADCAST: schedule_broadcast,
    Init.I_SHOULD_PIN: should_pin,
    Init.I_FINISH: finish
}