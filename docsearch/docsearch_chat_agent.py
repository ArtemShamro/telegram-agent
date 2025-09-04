# docsearch/agent.py
import os
from dotenv import load_dotenv
from langchain_gigachat import GigaChat
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPowerPointLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from telegram.embeds import DummyEmbeddings

class DocSearchAgent:
    def __init__(self, docs_path: str = "./data/docs", vector_store_path="./data/doc_db", temperature=0.3):
        self.docs_path = docs_path
        self.vector_store_path = vector_store_path

        self.llm = GigaChat(
            temperature=temperature,
            verify_ssl_certs=False,
            scope="GIGACHAT_API_PERS",
            credentials=os.getenv("GIGACHAT_API_KEY"),
        )

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-MiniLM-L3-v2",
            model_kwargs={"device": "cuda"}
        )
        # self.embeddings = DummyEmbeddings()
        self.vector_store = None
        self.qa_chain = None
        self.prompt = PromptTemplate.from_template(
            """
            Ты — агент, который отвечает на вопросы, используя только мои локальные материалы (PDF и PPTX).
            У тебя есть доступ к документам через систему поиска (RAG).

            Правила:
            1. Отвечай только по содержимому найденных документов.
            2. Обязательно указывай источник (файл и страница/слайд), из которого взята информация.
            3. Если информации нет - скажи прямо: "В материалах нет ответа на этот вопрос".
            4. Если полученная информация из источников не содержит ответа на вопрос или вообще не относится к теме -
                отвечай "В материалах нет информации по запросу"
            5. Не выдумывай факты и не обращайся к внешним источникам.
            6. Форматируй ответ так:
            - Краткий ответ (2–4 предложения).
            - Список источников которые оказались полезны (каждый с новой строки).
            
            Вопрос пользователя:
            {question}

            Информация из найденных документов:
            {context}
            """
        )

        self._prepare_db()

    def _prepare_db(self):
        docs = []
        for file in os.listdir(self.docs_path):
            path = os.path.join(self.docs_path, file)
            print(path)
            if file.endswith(".pdf"):
                loader = PyPDFLoader(path)
                print("file loaded")
                docs.extend(loader.load())
            elif file.endswith(".pptx"):
                loader = UnstructuredPowerPointLoader(path)
                docs.extend(loader.load())

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(docs)

        self.vector_store = Chroma.from_documents(
            documents=docs,
            embedding=self.embeddings,
            persist_directory=self.vector_store_path
        )
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt}
        )

    def run(self, query: str) -> str:
        if self.qa_chain is not None:
            result = self.qa_chain.invoke({"query": query})
            answer = result["result"]

            # собираем ссылки на источники
            sources = []
            for doc in result["source_documents"]:
                meta = doc.metadata
                source = f"{meta.get('source', '')}, page {meta.get('page', '?')}"
                sources.append(source)

            sources_text = "\n".join(set(sources)) if sources else "Источники не найдены"
            return f"{answer}\n\nИсточники:\n{sources_text}"
        else:
            return "База данных не инициализирована"