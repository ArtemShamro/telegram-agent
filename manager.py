import os
from dotenv import load_dotenv
from langchain_gigachat import GigaChat
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage

from docsearch.docsearch_chat_agent import DocSearchAgent
from telegram.telegram_chat_agent import TelegramChatAgent
from websearch.web_chat_agent import WebSearchAgent

from typing import List
from langchain.tools.base import BaseTool


class ManagerAgent:
    def __init__(self, temperature: float = 0.5):
        self.llm = GigaChat(
            temperature=temperature,
            verify_ssl_certs=False,
            scope="GIGACHAT_API_PERS",
            credentials=os.getenv("GIGACHAT_API_KEY"),
        )
        
        self.manager_prompt = (
            """
            Ты - менеджер агентов. У тебя есть два инструмента:
            1. TelegramAgent - для любых задач, связанных с моими чатами в Telegram.
            2. WebAgent - для поиска информации в интернете.
            3. DocSearchAgent - для поиска по локальным файлам.

            ВСЕГДА выбирай TelegramAgent для работы с чатами. 
            Никогда не используй WebAgent для этого.

            Можно использовать более одного инструмента, если для ответа на вопрос могут быть полезны несколько.

            Вопрос: {input}
            """
        )

        web_agent = WebSearchAgent()
        telegram_agent = TelegramChatAgent()
        docsearch_agent = DocSearchAgent()

        # Описываем subagents как tools
        tools: List[BaseTool] = [
        Tool(
            name="TelegramAgent",
            func=telegram_agent.run,
            description=(
                "Единственный инструмент для работы с моими чатами в Telegram. "
                "Используй его ВСЕГДА, если вопрос касается: моих чатов, сообщений, новых событий, "
                "обсуждений, участников или анализа переписки. "
                "НЕ используй WebAgent для таких вопросов."
            ),
        ),
        Tool(
            name="WebAgent",
            func=web_agent.run,
            description=(
                "Используй только для поиска информации в интернете (новости, сайты, статьи, факты). "
                "НИКОГДА не используй для вопросов про мои чаты Telegram."
            ),
        ),
        Tool(
            name="DocSearchAgent",
            func=docsearch_agent.run,
            description=(
                "Инструмент для поиска информации в локальных файлах. "
                "Он возвращает информацию, которая может быть полезна для ответа со ссылками на источники"
                "Используй его для поиска информации в учебных конспектах, статьях, презентациях. "
            )
    ),
    ]

        # Собираем планировщик и исполнитель в одного менеджера
        self.manager = initialize_agent(
            tools,
            self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # прямой выбор по описанию
            verbose=True,
            agent_kwargs={
                "system_message": SystemMessage(content=self.manager_prompt)
            }
        )

    def run(self, query: str) -> str:
        return self.manager.run(query)
