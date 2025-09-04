import os
import yaml
from langchain_gigachat import GigaChat
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from telegram.telegram_scrapper import TelegramAgent
import asyncio
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from pydantic import BaseModel, Field

class ChatSelection(BaseModel):
    chat_ids: list[int] = Field(description="ID выбранных чатов")
    hours: int = Field(description="Количество часов, за которые нужно получить сообщения")

class TelegramChatAgent:
    def __init__(self):

        # Загружаем список чатов
        with open(os.getenv("TELEGRAM_CHATS_FILE", "chats.yaml"), "r", encoding="utf-8") as f:
            self.chats_config = yaml.safe_load(f)
        # Словарь для быстрого доступа
        self.chat_id2name = {
            chat["id"]: chat["name"]
            for group, chats in self.chats_config.get("groups", {}).items()
            for chat in chats
        }

        self.telegram_agent = TelegramAgent(
            telegram_api_id=os.getenv("TELEGRAM_API_ID"),
            telegram_api_hash=os.getenv("TELEGRAM_API_HASH")
        )
    
        self.llm = GigaChat(
            verify_ssl_certs=False, 
            scope="GIGACHAT_API_PERS", 
            credentials=os.getenv("GIGACHAT_API_KEY")
        )

        # Модель данных для парсинга


        # Парсер
        self.base_parser = PydanticOutputParser(pydantic_object=ChatSelection)
        self.parser = OutputFixingParser.from_llm(parser=self.base_parser, llm=self.llm)
    
        # Шаблон для суммаризации
        self.select_prompt = ChatPromptTemplate.from_template(
            """
            У тебя есть список чатов:

            {chat_list}

            Вопрос пользователя: {question}

            Определи, какие чаты лучше всего подходит для ответа (может быть несколько). 
            Также оцени, за сколько последних часов нужно взять сообщения, 
            чтобы корректно ответить (обычно от 6 до 72 часов).

            Верни результат строго в формате JSON:
            {format_instructions}
            """
        ).partial(format_instructions=self.parser.get_format_instructions())

        self.summarize_prompt = ChatPromptTemplate.from_template(
            """
            Ты — помощник студента, который анализирует чат.

            Тебе даётся список сообщений чатов за определённый период. 
            Твоя задача для каждого чата отдельно:
            1. Определи основные темы обсуждений (короткие заголовки).  
            2. Суммаризируй ключевые диалоги по каждой теме (без дословных цитат).  
            3. Отметь домашние задания, информацию о расписании, важные факты, договорённости, решения или вопросы.  
            4. Игнорируй оффтоп, флуд, шутки, смайлики и повторяющиеся реплики.  
            5. Итоговый ответ оформи структурировано.

            Формат ответа для каждого чата:

            ### Название чата: чат 1

            ### Основные темы:
            - тема 1
            - тема 2

            ### Краткое содержание:
            - по теме 1: ...
            - по теме 2: ...

            Список сообщений из чатов:
            {messages}

            Ответь кратко и по делу. Не упусти самое важное - выдачу домашних заданий и изменения в расписании.
            """
        )
    def _format_chat_list(self):
        """Форматируем список чатов для промпта"""
        lines = []
        for group, chats in self.chats_config.get("groups", {}).items():
            lines.append(f"\n### {group.upper()}")
            for chat in chats:
                lines.append(f"- ID: {chat['id']}, {chat['name']} — {chat['description']}")
        return "\n".join(lines)
    
    async def _run_async(self, question, top_k=10):
        try:
            # 1. Получаем список чатов для промпта
            chat_list = self._format_chat_list()

            # 2. LLM выбирает чат и период
            selection_chain = self.select_prompt | self.llm | self.parser
            selection = await selection_chain.ainvoke({"chat_list": chat_list, "question": question})
            print(selection)
            # теперь selection — это Python-объект ChatSelection
            chat_ids = selection.chat_ids
            lookback_period = selection.hours * 3600

            # 3. Загружаем сообщения
            all_contexts = []

            for chat_id in chat_ids:
                chat_name = self.get_chat_name(chat_id)
                all_contexts.append(f"Сообщения из чата {chat_name} :")
                messages = await self.telegram_agent.load_messages(chat_id=chat_id, lookback_period=lookback_period)
                if not messages:
                    return f"В чате {chat_name} нет новых сообщений за последние {selection.hours}ч."
            
                context = "\n".join(messages)
                all_contexts.append(context)

            full_context = "\n".join(all_contexts) if all_contexts else "Нет новых сообщений"

            # 4. Суммаризировать
            summarize_chain = self.summarize_prompt | self.llm
            response = await summarize_chain.ainvoke({"messages": full_context})
            print("QUESTION", question)
            print("CONTEXT", full_context)
        finally:
            await self.telegram_agent.aclose()

        return response.content
    
    def run(self, question, top_k=10):
        return asyncio.run(self._run_async(question, top_k))
    
    def get_chat_name(self, chat_id: int) -> str:
        return self.chat_id2name.get(chat_id, f"Chat {chat_id}")
