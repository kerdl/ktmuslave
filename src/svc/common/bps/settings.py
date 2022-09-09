from svc.common import CommonMessage, MessageSource
from svc.common.keyboard import Keyboard, Button
from svc.common import messages as msg

from loguru import logger
from aiogram.types import ChatType


async def test(message: CommonMessage):

    kb = Keyboard([
        [Button("→ Начать")]
    ])

    logger.info(message.ctx)

    match message.src:
        case MessageSource.VK:
            m = message.vk

            is_group_chat = m.peer_id != m.from_id

            await m.answer(
                msg.format_welcome(is_group_chat), 
                keyboard=kb.to_vk().get_json(), 
                dont_parse_links=True
            )

        case MessageSource.TG:
            m = message.tg

            is_group_chat = m.chat.type in [ChatType.GROUP, ChatType.CHANNEL]

            await m.answer(msg.format_welcome(is_group_chat), reply_markup=kb.to_tg())