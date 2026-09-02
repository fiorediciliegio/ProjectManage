from django.conf import settings
from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

from app01.services.rag.rerank import is_explanation_question
from app01.services.rag.text_utils import (
    looks_like_table_or_figure_text,
    truncate_context_text,
)


CONTEXT_MAX_CHARS = 9000
CONTEXT_MAX_ITEMS = 8
CONTEXT_MAX_ITEMS_PER_FILE = 5
CONTEXT_MIN_ITEM_CHARS = 80


def qdrant_point_to_search_result(point, score=None):
    payload = point.payload or {}
    metadata = payload.get('metadata') or {}
    text = (
        payload.get('page_content')
        or payload.get('content')
        or payload.get('text')
        or ''
    )

    return {
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
        'text': text,
    }


def fetch_neighbor_chunks_from_qdrant(file_id, chunk_index, neighbor_size=1):
    if file_id is None or chunk_index is None:
        return []

    try:
        chunk_index = int(chunk_index)
    except (TypeError, ValueError):
        return []

    neighbor_indices = list(
        range(
            max(0, chunk_index - neighbor_size),
            chunk_index + neighbor_size + 1,
        )
    )

    from app01.services.langchain_rag_service import ensure_langchain_collection

    client = ensure_langchain_collection()
    qdrant_filter = Filter(
        must=[
            FieldCondition(
                key='metadata.file_id',
                match=MatchValue(value=file_id),
            ),
            FieldCondition(
                key='metadata.chunk_index',
                match=MatchAny(any=neighbor_indices),
            ),
        ]
    )

    points, _ = client.scroll(
        collection_name=settings.LANGCHAIN_QDRANT_COLLECTION,
        scroll_filter=qdrant_filter,
        limit=len(neighbor_indices),
        with_payload=True,
        with_vectors=False,
    )

    results = [qdrant_point_to_search_result(point) for point in points]
    results.sort(key=lambda item: item.get('chunk_index') or 0)
    return results


def expand_search_results_with_neighbors(search_results, neighbor_size=1, allowed_extensions=None):
    expanded_results = []
    seen = set()

    for item in search_results:
        file_extension = item.get('file_extension')

        if allowed_extensions and file_extension not in allowed_extensions:
            neighbor_items = [item]
        else:
            neighbor_items = fetch_neighbor_chunks_from_qdrant(
                file_id=item.get('file_id'),
                chunk_index=item.get('chunk_index'),
                neighbor_size=neighbor_size,
            )

            if not neighbor_items:
                neighbor_items = [item]

        for neighbor in neighbor_items:
            key = (
                neighbor.get('file_id'),
                neighbor.get('chunk_index'),
                neighbor.get('text'),
            )
            if key in seen:
                continue

            seen.add(key)
            expanded_results.append(neighbor)

    return expanded_results


def make_context_item_key(item):
    return (
        item.get('file_id'),
        item.get('chunk_index'),
    )


def get_context_rank_score(item):
    for key in [
        'model_rule_combined_score',
        'model_rerank_score',
        'rule_rerank_score',
        'rrf_score',
        'score',
    ]:
        value = item.get(key)
        if value is not None:
            return float(value)
    return 0


def get_context_display_score(item):
    for key in [
        'model_rule_combined_score',
        'model_rerank_score',
        'normalized_rule_rerank_score',
        'rule_rerank_score',
        'rrf_score',
        'context_rank_score',
        'score',
    ]:
        value = item.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return None


def is_low_priority_context_item(item, question):
    if not is_explanation_question(question):
        return False
    block_type = str(item.get('block_type') or '').lower()
    text = str(item.get('text') or '')
    if 'table' in block_type:
        return True
    if 'figure' in block_type or 'caption' in block_type:
        return True
    if looks_like_table_or_figure_text(text):
        return True
    return False


def deduplicate_context_items(search_results):
    item_map = {}

    for item in search_results:
        key = make_context_item_key(item)
        if key in [(None, None), None]:
            continue
        current_score = get_context_rank_score(item)
        if key not in item_map:
            item_map[key] = item
            continue
        old_score = get_context_rank_score(item_map[key])
        if current_score > old_score:
            item_map[key] = item

    deduplicated_items = list(item_map.values())
    deduplicated_items.sort(
        key=get_context_rank_score,
        reverse=True,
    )
    return deduplicated_items


def limit_context_items_per_file(items):
    file_count_map = {}
    limited_items = []

    for item in items:
        file_id = item.get('file_id')
        current_count = file_count_map.get(file_id, 0)

        if current_count >= CONTEXT_MAX_ITEMS_PER_FILE:
            continue

        limited_items.append(item)
        file_count_map[file_id] = current_count + 1

    return limited_items


def format_context_item(item, index):
    file_name = item.get('file_name') or '未知文件'
    page = item.get('page')
    title_path = item.get('title_path')
    block_type = item.get('block_type')
    score = get_context_display_score(item)
    chunk_indexes = item.get('merged_chunk_indexes') or [item.get('chunk_index')]

    metadata_lines = [
        f'[资料{index}]',
        f'文件：{file_name}',
        f'片段：{", ".join(str(chunk) for chunk in chunk_indexes if chunk is not None)}',
    ]

    if page:
        metadata_lines.append(f'页码：第 {page} 页')
    if title_path:
        metadata_lines.append(f'章节：{title_path}')
    if block_type:
        metadata_lines.append(f'内容类型：{block_type}')
    if score is not None:
        metadata_lines.append(f'相关性分数：{float(score):.4f}')
    if item.get('contextual_compressed'):
        ratio = item.get('contextual_compression_ratio')
        if ratio is not None:
            metadata_lines.append(f'规则上下文压缩：已压缩，保留比例 {float(ratio):.2f}')
        else:
            metadata_lines.append('规则上下文压缩：已压缩')
    if item.get('llm_contextual_compressed'):
        ratio = item.get('llm_contextual_compression_ratio')
        model_name = item.get('llm_contextual_compression_model')
        if ratio is not None:
            metadata_lines.append(f'LLM 上下文压缩：已压缩，保留比例 {float(ratio):.2f}')
        else:
            metadata_lines.append('LLM 上下文压缩：已压缩')
        if model_name:
            metadata_lines.append(f'LLM 压缩模型：{model_name}')
    text = truncate_context_text(item.get('text'))
    return '\n'.join(metadata_lines) + '\n内容：\n' + text


def pack_rag_context(search_results, question=None):
    deduplicated_items = deduplicate_context_items(search_results)

    high_priority_items = []
    low_priority_items = []

    for item in deduplicated_items:
        text = str(item.get('text') or '').strip()

        if len(text) < CONTEXT_MIN_ITEM_CHARS:
            continue

        if is_low_priority_context_item(item, question):
            low_priority_items.append(item)
        else:
            high_priority_items.append(item)

    packed_candidates = high_priority_items + low_priority_items
    limited_items = limit_context_items_per_file(packed_candidates)

    packed_parts = []
    selected_items = []
    current_chars = 0

    for item in limited_items:
        formatted_text = format_context_item(
            item,
            index=len(selected_items) + 1,
        )

        if current_chars + len(formatted_text) > CONTEXT_MAX_CHARS:
            continue

        packed_parts.append(formatted_text)
        selected_items.append(item)
        current_chars += len(formatted_text)

        if len(selected_items) >= CONTEXT_MAX_ITEMS:
            break

    context = '\n\n---\n\n'.join(packed_parts)
    return context, selected_items


def build_rag_sources(packed_results, cited_indexes=None, include_uncited=False):
    sources = []
    seen = set()

    for source_index, item in enumerate(packed_results, start=1):
        if cited_indexes is not None and source_index not in cited_indexes and not include_uncited:
            continue

        key = (
            item.get('file_id'),
            tuple(item.get('merged_chunk_indexes') or [item.get('chunk_index')]),
        )
        if key in seen:
            continue
        seen.add(key)

        sources.append({
            'source_index': source_index,
            'file_id': item.get('file_id'),
            'file_name': item.get('file_name'),
            'score': get_context_display_score(item),
            'chunk_index': item.get('chunk_index'),
            'merged_chunk_indexes': item.get('merged_chunk_indexes'),
            'page': item.get('page'),
            'sheet_name': item.get('sheet_name'),
        })

    return sources
