from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.tl.types import User, Channel

# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from telegram.embeds import DummyEmbeddings

# from telethon.tl.functions.messages import GetDialogsRequest
# from telethon.tl.types import InputPeerEmpty
from telethon.tl.types import PeerChannel
import os
import asyncio
import yaml
from datetime import datetime, timezone
from telethon.tl.types import PeerChannel

from telegram.msg_db.msg_service import MessageService
from telegram.msg_db.schemas import MessageSchema
import logging

logger = logging.getLogger(__name__)

class TelegramAgent:
    def __init__(self, config_file="config/tgChats.yaml", vector_store_path="chroma_db"):
        self.client = TelegramClient(
            "session.session", 
            api_id=os.getenv("TELEGRAM_API_ID"),  # type: ignore
            api_hash=os.getenv("TELEGRAM_API_HASH", ""),
            device_model="iPhone 55 Pro", 
            system_version="IOS 100.1"
        )
       
        self.service = MessageService()
        self.config_file = config_file
        self.chat_ids = self._load_chat_ids()

        embeddings = DummyEmbeddings(dim=384)
        # embeddings = HuggingFaceEmbeddings(
        #     model_name="sentence-transformers/all-MiniLM-L6-v2",
        #     model_kwargs={"device": "cuda"}
        # )
        self.vector_store = Chroma(persist_directory=vector_store_path, embedding_function=embeddings)

        logger.info("Агент Telegram инициализирован.")
        logger.info(f"Загружено чатов: {len(self.chat_ids)}")

        # # запускаем первый sync при старте
        # asyncio.create_task(self.sync_all_chats())

        # планировщик каждые 30 минут
        asyncio.create_task(self._periodic_sync(interval=1800))

    def _load_chat_ids(self):
        logger.debug(f"Загрузка конфигурации чатов из {self.config_file}")
        with open(self.config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        chat_ids = []
        for group_name, group_data in data.get("groups", {}).items():
            chat_ids.extend([c["id"] for c in group_data.get("chats", [])])
            
        logger.info(f"Загружено chat_id: {chat_ids}")
        return chat_ids
    
    async def sync_all_chats(self):
        """Синхронизируем все чаты: грузим новые сообщения после последнего сохранённого"""
        logger.info("Запуск синхронизации всех чатов...")
        await self.client.connect()
        for chat_id in self.chat_ids:
            last_date = self.service.get_last_message_date(chat_id)

            if last_date is None:
                # если сообщений в базе нет — берём месяц назад
                last_date = datetime.now(timezone.utc) - timedelta(days=30)
                logger.debug(f"Для чата {chat_id} нет сообщений, берём дату месяц назад.")

            await self._fetch_new_messages(chat_id, last_date)
        
        await self.client.disconnect() #type:ignore
        logger.info("Синхронизация завершена.")
    
    async def _fetch_new_messages(self, chat_id: int, last_date: datetime | None):
        """Выгрузить только новые сообщения из телеги и сохранить в БД"""
        logger.debug(f"Выгрузка новых сообщений для чата {chat_id} после {last_date}")
        channel = PeerChannel(channel_id=chat_id)
        history = []
        async for message in self.client.iter_messages(channel, limit=500):
            if not message.text:
                continue
            
            if last_date and message.date.astimezone(timezone.utc) <= last_date:
                break  # дальше старые, не нужны

            msg = MessageSchema(
                msg_id=message.id,
                chat_id=chat_id,
                date=message.date.astimezone(timezone.utc),
                sender_id=message.sender_id,
                text=message.text,
                is_read=False,
            )

            history.append(msg)

        if history:
            self.service.save_messages_bulk(history)
            logger.info(f"[SYNC] {chat_id}: добавлено {len(history)} новых сообщений")

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

    async def load_messages(self, chat_id: int, short: bool = False, hours: int = 24):
        """
        Загружаем сообщения из локальной базы, а не из Telegram.
        При этом автоматически помечаем их как прочитанные.
        """
        logger.debug(f"Загрузка сообщений из БД для чата {chat_id} за период {hours} часов.")

        msgs = self.service.get_recent_messages(chat_id=chat_id, hours=hours)

        if not msgs:
            logger.info(f"Нет новых сообщений в БД для чата {chat_id}")
            return []

        logger.info(f"Загружено сообщений из БД: {len(msgs)} для чата {chat_id}")

        history = []
        for m in msgs:
            if short:
                history.append(m.text)
            else:
                history.append(f"{m.date.strftime('%Y-%m-%d %H:%M:%S')} {m.sender_id}: {m.text}")

        return history
    
    # async def load_messages(self, chat_id, short=False, lookback_period=86400):
    #     logger.debug(f"Загрузка сообщений для чата {chat_id} за период {lookback_period} сек.")
    #     await self.client.connect()

    #     history = []
    #     datetime_from = self._get_datetime_from(lookback_period)
    #     channel = PeerChannel(channel_id=chat_id)
    #     async for message in self.client.iter_messages(channel, limit=500):
    #         if message.date < datetime_from:
    #             break
    #         if not message.text:
    #             continue
            
    #         if short:
    #             data = message.text
    #         else:
    #             data = {
    #                 "id": message.id,
    #                 "datetime": str(message.date),
    #                 "text": message.text,
    #                 "sender_user_id": message.sender_id,
    #                 "is_reply": message.is_reply
    #             }
    #             if message.is_reply:
    #                 data["reply_to_message_id"] = message.reply_to.reply_to_msg_id
                
    #             # Сохраняем в векторное хранилище
    #             self.vector_store.add_texts(
    #                 texts=[message.text],
    #                 metadatas=[{"chat_id": chat_id, "msg_id": message.id, "date": str(message.date)}],
    #                 ids=[f"{chat_id}_{message.id}"]
    #             )
            
    #         history.append(data)
        
    #     if len(history) == 0:
    #         logger.info(f"Нет новых сообщений для чата {chat_id}")
    #         return []
        
    #     logger.info(f"Загружено сообщений: {len(history)} для чата {chat_id}")
    #     return list(reversed([f"{h["datetime"][:19]} {h["sender_user_id"]}: {h["text"]}" for h in history]))
    
    async def aclose(self) -> None:
        if self.client.is_connected():
            await self.client.disconnect()  # type: ignore
            logger.info("Telegram клиент отключён.")

    async def _periodic_sync(self, interval: int):
        """Фоновая синхронизация каждые interval секунд"""
        while True:
            try:
                logger.info(f"[SYNC] Запуск плановой синхронизации...")
                await self.sync_all_chats()
            except Exception as e:
                logger.error(f"[SYNC ERROR]: {e}")
            await asyncio.sleep(interval)


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


