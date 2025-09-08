from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from .models import MessageORM
from .schemas import MessageSchema
from .database import Database
import logging

logger = logging.getLogger(__name__)

class MessageOperator:
    def __init__(self):
        self.db = Database()
        self.db.init_db()
        logger.info("Инициализирован оператор сообщений.")

    def add_message(self, msg: MessageSchema) -> MessageORM:
        logger.debug(f"Добавление сообщения: {msg}")
        with self.db.get_session() as session:
            db_msg = MessageORM(**msg.dict())
            session.add(db_msg)
            session.commit()
            session.refresh(db_msg)
            logger.info(f"Сообщение добавлено в БД: {db_msg.id}")
            return db_msg

    def add_messages_bulk(self, msgs: List[MessageSchema]) -> List[MessageORM]:
        logger.debug(f"Массовое добавление сообщений: {len(msgs)} шт.")
        with self.db.get_session() as session:
            db_msgs = [MessageORM(**m.dict()) for m in msgs]
            session.add_all(db_msgs)
            session.commit()
            logger.info(f"Добавлено сообщений в БД: {len(db_msgs)}")
            return db_msgs

    def get_messages(self, chat_id: int, since: Optional[datetime] = None) -> List[MessageSchema]:
        logger.debug(f"Запрос сообщений для чата {chat_id} с {since}")
        with self.db.get_session() as session:
            query = session.query(MessageORM).filter(MessageORM.chat_id == chat_id)

            if since:
                query = query.filter(MessageORM.date >= since)

            msgs = query.order_by(MessageORM.date.asc()).all()

            if msgs:
                ids = [m.id for m in msgs]
                session.query(MessageORM).filter(MessageORM.id.in_(ids)).update(
                    {"is_read": True}, synchronize_session=False
                )
                session.commit()
                logger.info(f"Помечено как прочитанные: {len(ids)} сообщений")

            logger.debug(f"Получено сообщений: {len(msgs)}")
            return [MessageSchema.model_validate(m) for m in msgs]

    def get_last_message_date(self, chat_id: int) -> Optional[datetime]:
        logger.debug(f"Получение даты последнего сообщения для чата {chat_id}")
        with self.db.get_session() as session:
            last_msg = (
                session.query(MessageORM)
                .filter(MessageORM.chat_id == chat_id)
                .order_by(MessageORM.date.desc())
                .first()
            )
            logger.info(f"Последняя дата сообщения: {last_msg.date if last_msg else 'Нет сообщений'}")
            return last_msg.date if last_msg else None #type:ignore
