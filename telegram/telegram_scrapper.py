from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.tl.types import User, Channel

# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from telegram.embeds import DummyEmbeddings

# from telethon.tl.functions.messages import GetDialogsRequest
# from telethon.tl.types import InputPeerEmpty
from telethon.tl.types import PeerChannel

class TelegramAgent:
    def __init__(self, telegram_api_id, telegram_api_hash, session_file="session.session", vector_store_path="chroma_db"):
        self.client = TelegramClient(
            session_file, 
            api_id=telegram_api_id, 
            api_hash=telegram_api_hash,
            device_model="iPhone 55 Pro", 
            system_version="IOS 100.1"
        )
        
        # Векторное хранилище для поиска по сообщениям
        embeddings = DummyEmbeddings(dim=384)
        # embeddings = HuggingFaceEmbeddings(
        #     model_name="sentence-transformers/all-MiniLM-L6-v2",
        #     model_kwargs={"device": "cuda"}
        # )
        self.vector_store = Chroma(persist_directory=vector_store_path, embedding_function=embeddings)

    @staticmethod
    def _get_user_name(sender):
        if isinstance(sender, User):
            return " ".join(filter(None, [sender.first_name, sender.last_name])) or "<unknown>"
        elif isinstance(sender, Channel):
            return sender.title
        return "<unknown>"

    @staticmethod
    def _get_datetime_from(lookback_period):
        return (datetime.now(timezone.utc) - timedelta(seconds=lookback_period)).replace(tzinfo=timezone.utc)

    async def load_messages(self, chat_id, short=False, lookback_period=86400):
        await self.client.connect()

        history = []
        datetime_from = self._get_datetime_from(lookback_period)
        channel = PeerChannel(channel_id=chat_id)
        async for message in self.client.iter_messages(channel, limit=500):
            if message.date < datetime_from:
                break
            if not message.text:
                continue
            
            if short:
                data = message.text
            else:
                data = {
                    "id": message.id,
                    "datetime": str(message.date),
                    "text": message.text,
                    "sender_user_id": message.sender_id,
                    "is_reply": message.is_reply
                }
                if message.is_reply:
                    data["reply_to_message_id"] = message.reply_to.reply_to_msg_id
                
                # Сохраняем в векторное хранилище
                self.vector_store.add_texts(
                    texts=[message.text],
                    metadatas=[{"chat_id": chat_id, "msg_id": message.id, "date": str(message.date)}],
                    ids=[f"{chat_id}_{message.id}"]
                )
            
            history.append(data)
        
        if len(history) == 0:
            return []
        
        return list(reversed([f"{h["datetime"][:19]} {h["sender_user_id"]}: {h["text"]}" for h in history]))
    
    async def aclose(self) -> None:
        if self.client.is_connected():
            await self.client.disconnect()  # type: ignore

    # def search(self, query, top_k=5):
    #     """Семантический поиск по истории сообщений"""
    #     return self.vector_store.similarity_search(query, k=top_k)
    
    # async def get_chats(self):
    #     await self.client.connect()
    #     chats = []
    #     last_date = None
    #     chunk_size = 200
    #     groups=[]

    #     result = await self.client(GetDialogsRequest(
    #                 offset_date=last_date,
    #                 offset_id=0,
    #                 offset_peer=InputPeerEmpty(),
    #                 limit=chunk_size,
    #                 hash = 0
    #             ))
    #     chats.extend(result.chats)

    #     for chat in chats:
    #         print(chat.id, chat.title)


