from typing import Optional


WELCOME =  (
    "Аааа я негр аааааааааааааааа, "
    "теперь мне придётся мне пиздить "
    "расписание с ktmu-sutd.ru "
    "как пиздят все негры 😔"
    "\n\n"
    "Но в качестве ЖеСтА дОбРоЙ вОлИ "
    "я поделюсь с {count}..."
    "\n\n"
    "Нажми ниже \"→ Начать\"..."
)

def format_welcome(is_group_chat: bool):
    if is_group_chat:
        return WELCOME.format(count="вами")
    else:
        return WELCOME.format(count="тобой")

GROUP = (
    "{groups}"
    "\n\n"
    "Напиши пальчиками (1000-7 REFERENCE????) свою группу\n"
    "   • Формат: 1кдд69, 1-кдд-69, 1КДД69, 1-КДД-69\n"
    "   • Можешь указать ту, которой пока нет в списке"
)

def format_group(groups: str, should_mention: bool, mention: Optional[str], should_reply: bool):
    assert not (should_mention and should_reply), "tf?? you want to mention AND reply?"

    formatted = GROUP.format(groups=groups)

    if should_mention and mention:
        formatted += f"\n\n😮 Ещё упомяни меня: {mention}, иначе не увижу 😮"
    elif should_mention and not mention:
        formatted += f"\n\n😮 Ещё упомяни меня, иначе не увижу 😮"
    elif should_reply:
        formatted += "\n\n😮 Пиши, отвечая на это сообщение, иначе не увижу 😮"
    
    return formatted

UNKNOWN_GROUP = (
    "{group} пока нет, всё равно поставить?"
)

def format_unknown_group(group: str):
    return UNKNOWN_GROUP.format(group=group)


if __name__ == "__main__":
    print(format_group(groups="mommy", should_mention=True, mention="@mommy", should_reply=False))