from pydantic import BaseModel
from datetime import datetime

class MessageSchema(BaseModel):
    chat_id: int
    msg_id: int
    sender_id: int | None = None
    text: str
    date: datetime
    is_read: bool = False

    class Config:
        from_attributes = True
