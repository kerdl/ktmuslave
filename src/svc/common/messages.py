from __future__ import annotations


class Builder:
    def __init__(self, separator: str = "\n\n") -> None:
        self.separator = separator
        self.components: list[str] = []
    
    def add(self, text: str) -> Builder:
        if text == "":
            return self

        self.components.append(text)
        return self
    
    def make(self) -> str:
        return self.separator.join(self.components)


#### Common footers and headers ####

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


if __name__ == "__main__":
    #print(format_group(groups="mommy", should_mention=True, mention="@mommy", should_reply=False))
    print(format_invalid_group("mommy"))