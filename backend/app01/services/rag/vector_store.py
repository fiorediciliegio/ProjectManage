import uuid
from typing import List

from django.conf import settings
from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from openai import DefaultHttpxClient, OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, VectorParams

from app01.services.elasticsearch_service import (
    delete_file_chunks_from_elasticsearch,
    index_chunks_to_elasticsearch,
)
from app01.services.rag.loaders import load_file_as_documents, split_documents

# ———————————————————— embedding ————————————————————
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

# Qdrant collection 初始化函数
def get_langchain_qdrant_client():
    return QdrantClient(
        url=settings.QDRANT_URL,
        prefer_grpc=False,
        timeout=10,
        check_compatibility=False,
        trust_env=False,
    )

def ensure_langchain_collection():
    client = get_langchain_qdrant_client()

    collection_names = [
        collection.name
        for collection in client.get_collections().collections
    ]

    if settings.LANGCHAIN_QDRANT_COLLECTION not in collection_names:
        client.create_collection(
            collection_name=settings.LANGCHAIN_QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=settings.QDRANT_VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
    return client

# LangChain VectorStore 获取函数
def get_langchain_vector_store():
    client = ensure_langchain_collection()
    embeddings = DashScopeTextEmbeddings()

    return QdrantVectorStore(
        client=client,
        collection_name=settings.LANGCHAIN_QDRANT_COLLECTION,
        embedding=embeddings,
    )

# 删除旧向量
def delete_langchain_file_vectors(file_id, stage_callback=None):
    notify_stage(stage_callback, 'qdrant_connect')
    client = ensure_langchain_collection()

    notify_stage(stage_callback, 'delete_vectors')
    client.delete(
        collection_name=settings.LANGCHAIN_QDRANT_COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key='metadata.file_id',
                    match=MatchValue(value=file_id),
                )
            ]
        ),
    )

    notify_stage(stage_callback, 'elasticsearch_index')
    elasticsearch_result = delete_file_chunks_from_elasticsearch(file_id)
    return {
        'file_id': file_id,
        'qdrant_deleted': True,
        'elasticsearch': elasticsearch_result,
    }

# 查询是否入库
def get_indexed_file_ids(project_id):
    ensure_langchain_collection()
    client = get_langchain_qdrant_client()
    qdrant_filter = Filter(
        must=[
            FieldCondition(
                key='metadata.project_id',
                match=MatchValue(value=project_id),
            )
        ]
    )

    file_ids = set()
    offset = None

    while True:
        points, offset = client.scroll(
            collection_name=settings.LANGCHAIN_QDRANT_COLLECTION,
            scroll_filter=qdrant_filter,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            metadata = (point.payload or {}).get('metadata') or {}
            file_id = metadata.get('file_id')
            if file_id is not None:
                file_ids.add(file_id)

        if offset is None:
            break
    return file_ids

# 写入 Qdrant
def notify_stage(stage_callback, stage):
    if stage_callback:
        stage_callback(stage)


def index_file_to_qdrant_langchain(file_obj, stage_callback=None):
    notify_stage(stage_callback, 'parse')
    documents = load_file_as_documents(file_obj)

    notify_stage(stage_callback, 'split')
    chunks = split_documents(documents)

    if not chunks:
        return {
            'file_id': file_obj.pk,
            'chunks_count': 0,
            'message': '文件中没有可入库的文本内容',
        }

    notify_stage(stage_callback, 'cleanup')
    delete_langchain_file_vectors(file_obj.pk, stage_callback=stage_callback)

    notify_stage(stage_callback, 'qdrant_connect')
    vector_store = get_langchain_vector_store()

    ids = [
        str(uuid.uuid5(uuid.NAMESPACE_URL, f'file-{file_obj.pk}-chunk-{index}'))
        for index, _ in enumerate(chunks)
    ]

    upsert_batch_size = max(1, int(getattr(settings, 'VECTOR_UPSERT_BATCH_SIZE', 16)))
    for start in range(0, len(chunks), upsert_batch_size):
        notify_stage(stage_callback, 'embedding')
        vector_store.add_documents(
            documents=chunks[start:start + upsert_batch_size],
            ids=ids[start:start + upsert_batch_size],
        )
        notify_stage(stage_callback, 'qdrant_upsert')

    notify_stage(stage_callback, 'elasticsearch_index')
    elasticsearch_result = index_chunks_to_elasticsearch(file_obj, chunks)
    file_name = f'{file_obj.NAME_File}{file_obj.FORM_File or ""}'
    return {
        'file_id': file_obj.pk,
        'file_name': file_name,
        'chunks_count': len(chunks),
        'elasticsearch_chunks_count': elasticsearch_result.get('indexed_count', 0),
        'message': '文件向量和关键词索引入库成功',
    }
# ———————————————————— 混合检索 ————————————————————
# 检索函数
def search_file_chunks_langchain(question, project_id=None, limit=5):
    vector_store = get_langchain_vector_store()
    qdrant_filter = None
    if project_id is not None:
        qdrant_filter = Filter(
            must=[
                FieldCondition(
                    key='metadata.project_id',
                    match=MatchValue(value=project_id),
                )
            ]
        )

    docs_with_scores = vector_store.similarity_search_with_score(
        query=question,
        k=limit,
        filter=qdrant_filter,
    )

    results = []
    for doc, score in docs_with_scores:
        metadata = doc.metadata or {}
        results.append({
            'score': score,
            'file_id': metadata.get('file_id'),
            'project_id': metadata.get('project_id'),
            'project_name': metadata.get('project_name'),
            'file_name': metadata.get('file_name'),
            'file_extension': metadata.get('file_extension'),
            'chunk_index': metadata.get('chunk_index'),
            'block_type': metadata.get('block_type'),
            'page': metadata.get('page'),
            'sheet_name': metadata.get('sheet_name'),
            'text': doc.page_content,
        })
    return results
