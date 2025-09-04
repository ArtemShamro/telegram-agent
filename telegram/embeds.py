from langchain.embeddings.base import Embeddings
import numpy as np

class DummyEmbeddings(Embeddings):
    """Заглушка для Embeddings, возвращает случайные векторы фиксированной размерности."""

    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed_documents(self, texts):
        # возвращаем numpy массив векторов
        return [np.random.rand(self.dim).tolist() for _ in texts]

    def embed_query(self, text):
        # один вектор для запроса
        return np.random.rand(self.dim).tolist()