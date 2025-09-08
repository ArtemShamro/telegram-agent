<br />
<p align="center">
  <!-- <a href="https://github.com/catiaspsilva/README-template">
    <img src="images/gators.jpg" alt="Logo" width="150" height="150">
  </a> -->

  <h3 align="center">TELEGRAM AGENT 
    <br> 
    <span style="font-weight: normal; font-size: 0.8em;">
    multiagent system
    </span>
  </h3>

  <!-- <p align="center">
    A README template to jumpstart your projects!
    <br />
    <a href="https://github.com/catiaspsilva/README-template/blob/main/images/docs.txt"><strong>Explore the docs »</strong></a>
    <br /> 
    <br />
    <a href="#usage">View Demo</a>
    ·
    <a href="https://github.com/catiaspsilva/README-template/issues">Report Bug</a>
    ·
    <a href="https://github.com/catiaspsilva/README-template/issues">Request Feature</a>
  </p> -->
</p>

## О проекте

Проект представляет собой мультиагентную систему на базе фреймворка `LangChain`, которая позволяет искать и анализировать информацию из различных источников — Telegram-чатов, веб-страниц, локальных документов (PDF, PPTX). Для пользователя предусмотрена единая точка входа через менеджера-агента, который автоматически выбирает оптимальные инструменты и агентов для решения задачи, используя современные методы обработки текста, базы данных и векторные хранилища.

## 🛠 Технологии

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.49.1-FF4B4B?style=flat&logo=streamlit)
![LangChain](https://img.shields.io/badge/LangChain-0.3.27-1C3C3C?style=flat)
![GigaChat](https://img.shields.io/badge/GigaChat-0.1.42.post2-2E86C1?style=flat)
![Telethon](https://img.shields.io/badge/Telethon-1.41.0-F3A223?style=flat)
![Chroma](https://img.shields.io/badge/Chroma-latest-6E57E0?style=flat)
![SQLite](https://img.shields.io/badge/SQLite-latest-003B57?style=flat&logo=sqlite)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.43-D71F00?style=flat)
![Pydantic](https://img.shields.io/badge/Pydantic-2.11.7-E92063?style=flat)
![BeautifulSoup4](https://img.shields.io/badge/BeautifulSoup4-0.0.2-4E9A06?style=flat)

## Схема системы

![img](src/scheme.png)

## Описание системы
* Менеджер-агент (manager.py):
Центральный компонент, который принимает запрос пользователя и распределяет его между специализированными агентами (Telegram, Web, DocSearch) в зависимости от типа задачи.

* Агент Telegram (telegram/telegram_chat_agent.py):
Отвечает за обработку пользовательских запросов, связанных с Telegram-чатами. Определяет, какие чаты и за какой период нужно анализировать, извлекает сообщения, формирует ответы, поддерживает суммаризацию и семантический поиск по переписке.

* Оператор работы с Telegram и базой данных (telegram/telegram_scrapper.py):
Выполняет сбор новых сообщений из Telegram-чатов с помощью Telethon, сохраняет их в базу данных, обеспечивает синхронизацию, обработку и обновление статусов сообщений. 

* Агент веб-поиска (websearch/web_chat_agent.py, ):
Позволяет искать факты и информацию в интернете.
Использует DuckDuckGo для поиска ссылок и собственный скраппер для извлечения данных с найденных страниц.

* WebScrapper (websearch/web_scrapper.py)
Инструмент для извлечения фактической информации с веб-страниц. Получает ссылки от агента веб-поиска, скачивает и парсит содержимое страниц, возвращает структурированные данные для формирования ответа пользователю.

* Агент поиска по PDF-файлам (docsearch/docsearch_chat_agent.py):
Осуществляет поиск и ответы на вопросы по локальным документам (PDF, PPTX).
Индексирует документы во векторное хранилище и отвечает на вопросы с указанием источников.

* Векторные базы данных
Хранят эмбеддинги сообщений и документов для семантического поиска.

* Файлы конфигурации (config/tgChats.yaml, .env):
Содержит список Telegram-чатов, с которыми работает система в формате YAML. 

