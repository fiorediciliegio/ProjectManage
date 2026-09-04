from typing import List

from django.conf import settings
from langchain_core.embeddings import Embeddings
from openai import DefaultHttpxClient, OpenAI


class DashScopeTextEmbeddings(Embeddings):
    def __init__(self):
        if not settings.EMBEDDING_API_KEY:
            raise RuntimeError('EMBEDDING_API_KEY or DASHSCOPE_API_KEY is required for DashScope embeddings.')

        self.client = OpenAI(
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL,
            http_client=DefaultHttpxClient(trust_env=False),
            timeout=getattr(settings, 'EMBEDDING_TIMEOUT', 60),
            max_retries=getattr(settings, 'EMBEDDING_MAX_RETRIES', 2),
        )
        self.model = settings.EMBEDDING_MODEL
        self.dimensions = int(getattr(settings, 'EMBEDDING_DIMENSIONS', settings.QDRANT_VECTOR_SIZE))

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        cleaned_texts = [
            self._clean_text(text) or ' '
            for text in texts
        ]

        if not cleaned_texts:
            return []

        batch_size = max(1, int(getattr(settings, 'EMBEDDING_BATCH_SIZE', 8)))
        vectors = []

        for start in range(0, len(cleaned_texts), batch_size):
            batch = cleaned_texts[start:start + batch_size]
            response = self.client.embeddings.create(
                model=self.model,
                input=batch,
                dimensions=self.dimensions,
            )
            vectors.extend(item.embedding for item in response.data)

        return vectors

    def embed_query(self, text: str) -> List[float]:
        vectors = self.embed_documents([text])
        if not vectors:
            return []
        return vectors[0]

    @staticmethod
    def _clean_text(text):
        return (text or '').replace('\n', ' ').strip()
