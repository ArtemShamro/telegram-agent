# websearch/agent.py
import os
import warnings
from dotenv import load_dotenv
from langchain_community.chat_models.gigachat import GigaChat
from langchain.agents import Tool, initialize_agent, AgentType

from langchain_community.tools import DuckDuckGoSearchRun
from websearch.web_scrapper import EnchancedWebScrapperTool

warnings.filterwarnings("ignore")


class WebSearchAgent:
    def __init__(self, model_name="GigaChat", temperature=0.5, max_iterations=5):
        load_dotenv()
        self.api_key = os.getenv("GIGACHAT_API_KEY")
        self.model_name = model_name
        self.temperature = temperature
        self.max_iterations = max_iterations

        self.agent = self._initialize_agent()

    def _initialize_agent(self):
        llm = GigaChat(
            temperature=self.temperature,
            verify_ssl_certs=False,
            scope="GIGACHAT_API_PERS",
            credentials=self.api_key,
        )
        agent_type = AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION

        system_prompt = (
            """
            Ты — веб-ассистент для поиска фактов.  
            У тебя есть два инструмента:

            1. WebSearch — используй его, чтобы найти подходящие ссылки по запросу.  
            2. WebScraper — используй его сразу после WebSearch, чтобы извлечь нужную информацию из найденной страницы.  

            ⚠️ Никогда не отвечай пользователю, используя только WebSearch.  
            ВСЕГДА используй WebScraper, чтобы получить данные с конкретной страницы.  

            ---

            ⚠️ Ты обязан следовать строго этому формату:

            Thought: {твои рассуждения на любом языке}  
            Action: {название инструмента}  
            Action Input: {аргументы для инструмента}  

            Если у тебя есть финальный ответ пользователю:  
            Final Answer: {текст ответа}  

            ---

            Правила:  
            - НИКОГДА не используй 'action:' или 'thought:' с маленькой буквы.  
            - НИКОГДА не пиши JSON, только указанный формат.  
            - Если ты отвечаешь напрямую, всегда используй 'Final Answer:'.  
            - Твои ответы должны быть краткими и содержать только фактическую информацию.  
            - Если запрос про курс валюты, погоду, дату или число — верни именно число/факт.  
            - Если информации нет, скажи прямо: «Не удалось найти актуальные данные».  
            """
        )
        
        
        search_tool = DuckDuckGoSearchRun()
        web_scraper_tool = EnchancedWebScrapperTool()

        tools = [
            Tool(
                name="WebSearch",
                func=search_tool.run,
                description=(
                    "Найди релевантные ссылки по запросу. "
                    "Никогда не отвечай пользователю напрямую после WebSearch. "
                    "Определи наиболее подходящие ссылки для получения запрошенной информации. "
                    "ВСЕГДА используй WebScraper для просмотра от 2 до 5 страниц, чтобы извлечь данные."
                )
            ),
            Tool(
                name="WebScraper",
                func=web_scraper_tool.run,
                description=(
                    "Извлеки только ключевую информацию с указанной веб-страницы. "
                    "Например: курс валюты, число, факт. "
                    "Избегай длинных описаний — верни фактические данные."
                )
            ),
        ]

        return initialize_agent(
            tools=tools,
            llm=llm,
            agent=agent_type,
            verbose=True,
            max_iterations=self.max_iterations,
            handle_parsing_errors=True,
            early_stopping_method="generate",
            agent_kwargs={"system_message": system_prompt}
        )

    def run(self, query: str) -> str:
        return self.agent.run(query)
