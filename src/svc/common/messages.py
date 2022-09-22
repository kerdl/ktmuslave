from __future__ import annotations
from typing import Optional

from src.svc.common import MESSENGER_SOURCE, CommonEverything, Source, error
from src.svc.common.states import State


DEBUGGING = True


class Builder:
    def __init__(
        self, 
        separator: str = "\n\n", 
        everything: Optional[CommonEverything] = None
    ) -> None:
        self.separator = separator
        self.components: list[str] = []
        self.everything = everything


        if DEBUGGING and everything is None:
            raise error.NoEverythingWithDebugOn((
                "debug is on, but there's no way "
                "of displaying debug info without "
                "CommonEverything"
            ))
    
    def add(self, text: str) -> Builder:
        if text == "":
            return self

        self.components.append(text)
        return self
    
    def debug(self, everything: CommonEverything):
        """
        ## Generate debug info
        """

        trace = everything.navigator.trace
        debug_info = format_debug(trace)

        return debug_info

    def make(self) -> str:
        if DEBUGGING:
            self.components = [self.debug(self.everything)] + self.components

        return self.separator.join(self.components)


#### Common footers and headers ####

DEBUG = (
    "c==3 trace:\n"
    "{trace}"
)
def format_debug(trace: list[State]):
    trace_str = "\n".join([state.anchor for state in trace])

    return DEBUG.format(trace=trace_str)


PRESS_BEGIN = (
    "👇 Нажимай \"Начать\", хуле"
)
def format_press_begin():
    return PRESS_BEGIN


GROUPS = (
    "🖕 | Группы в расписании:\n"
    "   ╰ {groups}"
)
def format_groups(groups: list[str]):
    groups_str = ", ".join(groups)
    return GROUPS.format(groups=groups_str)


MENTION_ME = (
    "😮 Пиши, упоминая меня: {mention}, иначе не увижу 😮"
)
def format_mention_me(mention: str):
    return MENTION_ME.format(mention=mention)


REPLY_TO_ME = (
    "😮 Пиши, отвечая на это сообщение, иначе не увижу 😮"
)
def format_reply_to_me():
    return REPLY_TO_ME


CHAT_WILL_MIGRATE = (
    "🤔 Из-за этого, эта группа станет супергруппой 🤔\n"
    "Читай подробнее здесь: https://teleme.io/articles/turn_a_telegram_group_into_a_supergroup?hl=ru"
)
def format_chat_will_migrate():
    return CHAT_WILL_MIGRATE


#### Full messages for specific states ####

WELCOME =  (
    "😵😵😵 Аааа я негр 👨🏿👨🏿 аааааааааааааааа, "
    "теперь мне придётся пиздить "
    "расписание с 🌐 ktmu-sutd.ru 🌐 "
    "чтобы делиться с {count} 😔..."
)
def format_welcome(is_group_chat: bool):
    if is_group_chat:
        return WELCOME.format(count="вами")
    else:
        return WELCOME.format(count="тобой")


GROUP_INPUT = (
    "💅 | Напиши свою группу\n"
    "   ╰ Формат: 1кдд69, 1-кдд-69, 1КДД69, 1-КДД-69\n"
    "   ╰ Можешь написать ту, которой нет в списке"
)
def format_group_input():
    return GROUP_INPUT


UNKNOWN_GROUP = (
    "❓ | {group} пока нет, всё равно поставить?"
)
def format_unknown_group(group: str):
    return UNKNOWN_GROUP.format(group=group)


INVALID_GROUP = (
    "❌ | Эта хуйня не подходит под формат: 1кдд69, 1-кдд-69, 1КДД69, 1-КДД-69\n"
    "Напиши ещё раз по формату"
)
def format_invalid_group():
    return INVALID_GROUP


SCHEDULE_BROADCAST = (
    "🔔 | Хочешь получать здесь обновления расписания?"
)
def format_schedule_broadcast():
    return SCHEDULE_BROADCAST


DO_PIN = (
    "📌 | В таком случае, хочешь шоб я закреплял эти обновления?"
)
def format_do_pin():
    return DO_PIN


RECOMMEND_PIN = (
    "📌 | В таком случае, я могу закреплять эти обновления, "
    "но сейчас у меня нет прав"
)
def format_recommend_pin():
    return RECOMMEND_PIN


PERMIT_PIN_VK = (
    "🚽 | Если хочешь заркеп, назначь меня админом, "
    "либо пропусти если поебать"
)
PERMIT_PIN_TG = (
    "🚽 | Если хочешь закреп, назначь меня админом с правом "
    "\"Закрепление сообщений\", либо пропусти если поебать"
)
def format_permit_pin(src: MESSENGER_SOURCE):
    if src == Source.VK:
        return PERMIT_PIN_VK
    if src == Source.TG:
        return PERMIT_PIN_TG


CANT_PIN_VK = (
    "Нет у меня нихуя, перепроверь мою админку"
)
CANT_PIN_TG = (
    "Нет у меня нихуя, перепроверь моё право \"Закрепление сообщений\""
)
def format_cant_pin(src: MESSENGER_SOURCE):
    if src == Source.VK:
        return CANT_PIN_VK
    if src == Source.TG:
        return CANT_PIN_TG


FINISH = (
    "Фпринципи фсё, можешь перепроверить или нажать \"Закончить\""
)
def format_finish():
    return FINISH


if __name__ == "__main__":
    #print(format_group(groups="mommy", should_mention=True, mention="@mommy", should_reply=False))
    print(format_invalid_group("mommy"))