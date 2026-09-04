import logging
import math
import uuid

from django.conf import settings
from langchain_core.documents import Document

from app01.services.rag.embeddings import DashScopeTextEmbeddings


logger = logging.getLogger(__name__)


TABLE_BLOCK_TYPES = {'table', 'sheet_table', 'pdf_table'}
HEADING_BLOCK_TYPES = {'title', 'pdf_title'}


def semantic_chunking_enabled():
    return bool(getattr(settings, 'RAG_SEMANTIC_CHUNKING_ENABLED', False))


def cosine_similarity(left, right):
    if not left or not right or len(left) != len(right):
        return 0

    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))

    if not left_norm or not right_norm:
        return 0
    return dot / (left_norm * right_norm)


def get_block_type(doc):
    return str((doc.metadata or {}).get('block_type') or '')


def is_table_document(doc):
    return get_block_type(doc) in TABLE_BLOCK_TYPES or 'table' in get_block_type(doc)


def is_heading_document(doc):
    return get_block_type(doc) in HEADING_BLOCK_TYPES


def is_mergeable_document(doc):
    return not is_table_document(doc) and not is_heading_document(doc)


def document_chars(doc):
    return len((doc.page_content or '').strip())


def semantic_text(doc):
    text = (doc.page_content or '').strip()
    max_chars = int(getattr(settings, 'RAG_SEMANTIC_CHUNKING_EMBED_TEXT_CHARS', 900))
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def same_semantic_scope(left, right):
    left_metadata = left.metadata or {}
    right_metadata = right.metadata or {}
    return (
        left_metadata.get('file_id') == right_metadata.get('file_id')
        and tuple(left_metadata.get('section_path') or left_metadata.get('title_path') or [])
        == tuple(right_metadata.get('section_path') or right_metadata.get('title_path') or [])
        and left_metadata.get('sheet_name') == right_metadata.get('sheet_name')
    )


def annotate_document(doc, group_id, split_reason, score=None, source_count=1):
    metadata = doc.metadata or {}
    metadata.update({
        'semantic_group_id': group_id,
        'semantic_score': round(float(score), 4) if score is not None else None,
        'semantic_split_reason': split_reason,
        'source_block_count': source_count,
    })
    doc.metadata = metadata
    return doc


def merge_document_group(group, group_id, split_reason, scores):
    if not group:
        return None

    if len(group) == 1:
        score = scores[0] if scores else None
        return annotate_document(group[0], group_id, split_reason, score=score, source_count=1)

    first = group[0]
    metadata = dict(first.metadata or {})
    metadata.update({
        'semantic_group_id': group_id,
        'semantic_score': round(sum(scores) / len(scores), 4) if scores else None,
        'semantic_split_reason': split_reason,
        'source_block_count': len(group),
        'merged_source_orders': [
            (doc.metadata or {}).get('order')
            for doc in group
            if (doc.metadata or {}).get('order') is not None
        ],
        'merged_pages': sorted({
            (doc.metadata or {}).get('page')
            for doc in group
            if (doc.metadata or {}).get('page') is not None
        }),
    })

    content = '\n'.join((doc.page_content or '').strip() for doc in group if (doc.page_content or '').strip())
    return Document(page_content=content, metadata=metadata)


def build_group_id(doc, index):
    metadata = doc.metadata or {}
    raw = f"{metadata.get('file_id')}:{metadata.get('order')}:{index}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def should_merge_by_length(buffer_chars, next_chars, similarity):
    min_chars = int(getattr(settings, 'RAG_SEMANTIC_CHUNKING_MIN_BLOCK_CHARS', 80))
    max_chars = int(getattr(settings, 'RAG_SEMANTIC_CHUNKING_MAX_CHUNK_CHARS', 1400))
    min_similarity = float(getattr(settings, 'RAG_SEMANTIC_CHUNKING_SHORT_MERGE_MIN_SIMILARITY', 0.5))
    return (
        buffer_chars < min_chars
        and buffer_chars + next_chars <= max_chars
        and similarity >= min_similarity
    )


def semantic_merge_documents(documents, embeddings=None):
    if not semantic_chunking_enabled() or len(documents) <= 1:
        return documents

    if not getattr(settings, 'EMBEDDING_API_KEY', ''):
        logger.warning('Semantic chunking skipped because embedding API key is not configured.')
        return documents

    mergeable_items = [
        (index, semantic_text(doc))
        for index, doc in enumerate(documents)
        if is_mergeable_document(doc)
    ]
    vectors_by_index = {}
    if mergeable_items:
        try:
            embedding_client = embeddings or DashScopeTextEmbeddings()
            vectors = embedding_client.embed_documents([text for _, text in mergeable_items])
            vectors_by_index = {
                index: vector
                for (index, _), vector in zip(mergeable_items, vectors)
            }
        except Exception as exc:
            logger.warning(
                'Semantic chunking failed and fell back to rule-based chunks. error_type=%s error=%s',
                exc.__class__.__name__,
                exc,
            )
            return documents

    max_chars = int(getattr(settings, 'RAG_SEMANTIC_CHUNKING_MAX_CHUNK_CHARS', 1400))
    target_chars = int(getattr(settings, 'RAG_SEMANTIC_CHUNKING_TARGET_CHARS', 900))
    threshold = float(getattr(settings, 'RAG_SEMANTIC_CHUNKING_SIMILARITY_THRESHOLD', 0.62))

    merged_documents = []
    buffer = []
    buffer_indexes = []
    buffer_scores = []
    buffer_chars = 0
    group_index = 0

    def flush(reason):
        nonlocal buffer, buffer_indexes, buffer_scores, buffer_chars, group_index
        if not buffer:
            return
        group_id = build_group_id(buffer[0], group_index)
        merged = merge_document_group(buffer, group_id, reason, buffer_scores)
        if merged is not None:
            merged_documents.append(merged)
        buffer = []
        buffer_indexes = []
        buffer_scores = []
        buffer_chars = 0
        group_index += 1

    for index, doc in enumerate(documents):
        doc_chars = document_chars(doc)

        if not is_mergeable_document(doc):
            flush('heading' if is_heading_document(doc) else 'table')
            group_id = build_group_id(doc, group_index)
            reason = 'heading' if is_heading_document(doc) else 'table'
            merged_documents.append(annotate_document(doc, group_id, reason, source_count=1))
            group_index += 1
            continue

        if not buffer:
            buffer = [doc]
            buffer_indexes = [index]
            buffer_chars = doc_chars
            continue

        previous_doc = buffer[-1]
        previous_index = buffer_indexes[-1]
        next_similarity = cosine_similarity(vectors_by_index.get(previous_index), vectors_by_index.get(index))
        would_exceed_max = buffer_chars + doc_chars > max_chars
        scope_changed = not same_semantic_scope(previous_doc, doc)
        low_similarity = next_similarity < threshold

        if scope_changed:
            flush('section_changed')
        elif would_exceed_max:
            flush('max_chars')
        elif low_similarity and not should_merge_by_length(buffer_chars, doc_chars, next_similarity):
            flush('low_similarity')

        if not buffer:
            buffer = [doc]
            buffer_indexes = [index]
            buffer_chars = doc_chars
            continue

        buffer.append(doc)
        buffer_indexes.append(index)
        buffer_scores.append(next_similarity)
        buffer_chars += doc_chars

        if buffer_chars >= target_chars:
            flush('target_chars')

    flush('end')
    return merged_documents
