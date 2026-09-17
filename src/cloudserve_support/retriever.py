import numpy as np

from .chunker import chunk_documents
from .document_loader import load_documents
from .embedder import Embedder


DEFAULT_RELEVANCE_THRESHOLD = 0.28


class Retriever:
    def __init__(
        self,
        documents,
        embedder=None,
        relevance_threshold=DEFAULT_RELEVANCE_THRESHOLD,
    ):
        self.documents = documents
        self.embedder = embedder or Embedder()
        self.relevance_threshold = relevance_threshold
        self.chunks = chunk_documents(documents)

        texts = [chunk.content for chunk in self.chunks]
        self.embeddings = np.array(self.embedder.embed(texts))

    def search(self, query: str, top_k: int = 5):
        query_vector = np.array(self.embedder.embed([query])[0])

        scores = self.embeddings @ query_vector
        indices = np.argsort(scores)[::-1][:top_k]

        return [
            (self.chunks[index], float(scores[index]))
            for index in indices
            if scores[index] >= self.relevance_threshold
        ]

