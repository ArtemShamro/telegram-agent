from datetime import datetime, timedelta, timezone
from typing import List, Optional
from telegram.msg_db.db_operator import MessageOperator
from .schemas import MessageSchema
from .models import MessageORM
import logging

logger = logging.getLogger(__name__)

class MessageService:
    def __init__(self):
        self.repo = MessageOperator()
        logger.info("Сервис сообщений инициализирован.")

    def save_message(self, msg: MessageSchema):
        """Сохранить одно сообщение"""
        logger.debug(f"Сохраняем сообщение: {msg}")
        return self.repo.add_message(msg)

    def save_messages_bulk(self, msgs: List[MessageSchema]):
        """Сохранить список сообщений"""
        logger.debug(f"Сохраняем список сообщений: {len(msgs)} шт.")
        return self.repo.add_messages_bulk(msgs)

    def get_recent_messages(self, chat_id: int, hours: int = 24) -> List[MessageSchema]:
        """
        Достаём сообщения за последние N часов.
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        logger.debug(f"Получаем новые сообщения для чата {chat_id} за {hours} часов")
        msgs = self.repo.get_messages(chat_id, since)

        logger.info(f"Получено новых сообщений: {len(msgs)}")
        return msgs

    def get_last_message_date(self, chat_id: int) -> Optional[datetime]:
        """Вернуть дату последнего сообщения в чате"""
        logger.debug(f"Запрос даты последнего сообщения для чата {chat_id}")
        return self.repo.get_last_message_date(chat_id)
