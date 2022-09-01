from svc.common import CommonMessage, MessageSource
from svc.common.keyboard import Keyboard, Button


async def test(message: CommonMessage):

    kb = Keyboard([
        [Button("piska"), Button("jopa")],
        [Button("Pizda")]
    ])

    match message.src:
        case MessageSource.VK:
            m = message.vk
            await m.answer("vk ebat", keyboard=kb.to_vk().get_json())

        case MessageSource.TG:
            m = message.tg
            await m.answer("tg ebat", reply_markup=kb.to_tg())