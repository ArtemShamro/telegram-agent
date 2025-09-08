from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from .database import Base

class MessageORM(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, index=True, nullable=False)
    msg_id = Column(Integer, nullable=False)   # ID сообщения внутри чата
    sender_id = Column(Integer, nullable=True)
    text = Column(Text, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False, index=True)

    is_read = Column(Boolean, default=False, index=True)  # False = новое, True = прочитано
