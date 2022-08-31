from svc.common import CommonMessage, MessageSource


async def test(message: CommonMessage):
    match message.src:
        case MessageSource.VK:
            m = message.vk
            await m.answer("vk ebat")

        case MessageSource.TG:
            m = message.tg
            await m.answer("tg ebat")