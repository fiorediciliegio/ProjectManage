import logging
import re

from django.conf import settings

from app01.services.rag_resilience_service import (
    is_circuit_allowed,
    record_component_failure,
    record_component_success,
)


logger = logging.getLogger("app01.rag_resilience")


def make_search_result_key(item):
    return (
        item.get('file_id'),
        item.get('chunk_index'),
    )


def clean_multi_query_line(line):
    line = str(line or '').strip()
    line = re.sub(r'^\s*[-*•]\s*', '', line)
    line = re.sub(r'^\s*\d+[\.\)、)]\s*', '', line)
    line = line.strip(' "\'“”‘’')
    max_chars = max(20, int(getattr(settings, 'RAG_MULTI_QUERY_MAX_QUERY_CHARS', 180)))
    return line[:max_chars].strip()


def unique_queries(queries, max_queries):
    seen = set()
    results = []
    for query in queries:
        cleaned = clean_multi_query_line(query)
        if not cleaned:
            continue
        key = re.sub(r'\s+', '', cleaned).lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(cleaned)
        if len(results) >= max_queries:
            break
    return results


def generate_multi_search_queries(question):
    question = str(question or '').strip()
    if not question:
        return []

    enabled = bool(getattr(settings, 'RAG_MULTI_QUERY_ENABLED', True))
    generated_count = max(0, int(getattr(settings, 'RAG_MULTI_QUERY_COUNT', 3)))
    max_queries = generated_count + 1
    if not enabled or generated_count <= 0:
        return [clean_multi_query_line(question)]

    if not settings.RAG_CHAT_API_KEY:
        return [clean_multi_query_line(question)]

    if not is_circuit_allowed('chat_model'):
        logger.warning('rag chat model circuit open, skip multi-query generation')
        return [clean_multi_query_line(question)]

    prompt = f'''
请围绕下面的项目文档检索问题，生成 {generated_count} 个不同角度的检索查询。

要求：
1. 每个查询都要忠实保留原问题意图，不要引入没有依据的新对象。
2. 查询之间要尽量覆盖不同表达方式、同义词、实体名称、工程管理术语。
3. 适合用于向量检索和 BM25 关键词检索。
4. 每行只输出一个查询，不要编号，不要解释。

原始检索问题：
{question}

多路检索查询：
'''.strip()

    try:
        from app01.services.langchain_rag_service import get_chat_client

        client = get_chat_client()
        response = client.chat.completions.create(
            model=settings.RAG_CHAT_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': '你是项目文档 RAG 系统的 Multi-Query 检索改写器，只输出检索查询。',
                },
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
            temperature=0.2,
            max_tokens=getattr(settings, 'RAG_MULTI_QUERY_MAX_TOKENS', 384),
        )
        record_component_success('chat_model')
    except Exception as exc:
        record_component_failure('chat_model', exc)
        logger.warning('rag multi-query generation degraded error=%r', exc)
        return [clean_multi_query_line(question)]

    content = response.choices[0].message.content or ''
    generated_queries = [
        line
        for line in content.splitlines()
        if clean_multi_query_line(line)
    ]
    return unique_queries([question, *generated_queries], max_queries=max_queries) or [clean_multi_query_line(question)]


def attach_query_metadata(results, query, query_index):
    return [
        {
            **item,
            'retrieval_query': query,
            'retrieval_query_index': query_index,
        }
        for item in results
    ]


def reciprocal_rank_fusion(result_groups, rrf_k=60, top_k=8):
    fused_map = {}

    for group_name, results in result_groups:
        for rank, item in enumerate(results, start=1):
            key = make_search_result_key(item)

            if key in [(None, None), None]:
                continue

            if key not in fused_map:
                fused_map[key] = {
                    **item,
                    'rrf_score': 0,
                    'retrieval_sources': [],
                }

            fused_map[key]['rrf_score'] += 1 / (rrf_k + rank)
            retrieval_source = {
                'source': group_name,
                'rank': rank,
                'score': item.get('score'),
            }
            if item.get('retrieval_query'):
                retrieval_source['query'] = item.get('retrieval_query')
            if item.get('retrieval_query_index') is not None:
                retrieval_source['query_index'] = item.get('retrieval_query_index')
            fused_map[key]['retrieval_sources'].append(retrieval_source)

            if len(str(item.get('text') or '')) > len(str(fused_map[key].get('text') or '')):
                fused_map[key]['text'] = item.get('text')

    fused_results = list(fused_map.values())

    fused_results.sort(
        key=lambda item: item.get('rrf_score', 0),
        reverse=True,
    )

    return fused_results[:top_k]
