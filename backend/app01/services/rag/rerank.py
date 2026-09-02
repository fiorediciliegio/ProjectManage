import logging

import requests
from django.conf import settings

from app01.services.rag.text_utils import extract_query_terms
from app01.services.rag_resilience_service import (
    is_circuit_allowed,
    record_component_failure,
    record_component_success,
)


logger = logging.getLogger("app01.rag_resilience")

RERANK_CANDIDATE_LIMIT = int(getattr(settings, 'RAG_RERANK_CANDIDATE_LIMIT', 32))
RERANK_FINAL_LIMIT = 8
RERANK_DOUBLE_HIT_BONUS = 1.20
RERANK_TITLE_MATCH_BONUS = 1.15
RERANK_GOOD_LENGTH_BONUS = 1.10
RERANK_SHORT_TEXT_PENALTY = 0.60
RERANK_LONG_TEXT_PENALTY = 0.90
RERANK_REFERENCE_PENALTY = 0.50
RERANK_TABLE_QUERY_BONUS = 1.18
RERANK_TABLE_MISMATCH_PENALTY = 0.90

MODEL_RERANK_CANDIDATE_LIMIT = int(getattr(settings, 'RAG_MODEL_RERANK_CANDIDATE_LIMIT', 24))
MODEL_RERANK_WEIGHT = 0.60
RULE_RERANK_WEIGHT = 0.40


def is_explanation_question(question):
    keywords = ['是什么', '为什么', '原理', '机制', '作用', '原因', '说明', '解释']
    text = str(question or '')
    return any(keyword in text for keyword in keywords)


def is_table_or_data_question(question):
    keywords = ['表', '参数', '数值', '编号', '型号', '尺寸', '金额', '日期', '数量', '对比', '统计', '比例', '强度', '荷载']
    text = str(question or '')
    return any(keyword in text for keyword in keywords)


def is_reference_like_chunk(item):
    title_path = str(item.get('title_path') or '')
    text = str(item.get('text') or '')
    reference_markers = ['参考文献', 'References', '[J]', '[D]', '[S]', '出版社', '学报', '期刊']
    return any(marker in title_path or marker in text[:200] for marker in reference_markers)


def get_retrieval_source_names(item):
    return {
        source.get('source')
        for source in item.get('retrieval_sources', [])
        if source.get('source')
    }


def calculate_rule_rerank_score(item, question):
    score = float(item.get('rrf_score') or item.get('score') or 0)
    if score <= 0:
        score = 0.0001

    text = str(item.get('text') or '')
    title_path = str(item.get('title_path') or '')
    block_type = str(item.get('block_type') or '')
    sources = get_retrieval_source_names(item)
    query_terms = extract_query_terms(question)

    reasons = []

    if {'vector', 'keyword'}.issubset(sources):
        score *= RERANK_DOUBLE_HIT_BONUS
        reasons.append('向量和关键词双命中')

    if title_path and any(term in title_path for term in query_terms):
        score *= RERANK_TITLE_MATCH_BONUS
        reasons.append('标题路径命中问题关键词')

    text_length = len(text)
    if 300 <= text_length <= 1500:
        score *= RERANK_GOOD_LENGTH_BONUS
        reasons.append('片段长度适中')
    elif text_length < 120:
        score *= RERANK_SHORT_TEXT_PENALTY
        reasons.append('片段过短降权')
    elif text_length > 2200:
        score *= RERANK_LONG_TEXT_PENALTY
        reasons.append('片段过长降权')

    if block_type in ['pdf_title', 'title']:
        score *= 0.70
        reasons.append('标题块不能直接回答问题，降权')

    if is_reference_like_chunk(item):
        score *= RERANK_REFERENCE_PENALTY
        reasons.append('参考文献类内容降权')

    if is_explanation_question(question):
        if text.strip().startswith('图') or text.strip().startswith('表'):
            score *= 0.75
            reasons.append('解释型问题图表类内容降权')

    if is_table_or_data_question(question):
        if 'table' in block_type:
            score *= RERANK_TABLE_QUERY_BONUS
            reasons.append('数据型问题优先表格')
    else:
        if 'table' in block_type:
            score *= RERANK_TABLE_MISMATCH_PENALTY
            reasons.append('非数据型问题表格轻微降权')

    return {**item, 'rule_rerank_score': score, 'rule_rerank_reasons': reasons}


def rule_rerank_search_results(search_results, question, top_k=RERANK_FINAL_LIMIT):
    reranked_results = [
        calculate_rule_rerank_score(item, question)
        for item in search_results
    ]
    reranked_results.sort(
        key=lambda item: item.get('rule_rerank_score', 0),
        reverse=True,
    )
    return reranked_results[:top_k]


def truncate_rerank_document_text(text, max_chars=3000):
    text = str(text or '').strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def normalize_item_scores(items, score_key):
    scores = [
        float(item.get(score_key) or 0)
        for item in items
    ]

    if not scores:
        return {}

    min_score = min(scores)
    max_score = max(scores)
    normalized_scores = {}

    for index, item in enumerate(items):
        score = float(item.get(score_key) or 0)

        if max_score == min_score:
            normalized_scores[index] = 1.0
        else:
            normalized_scores[index] = (score - min_score) / (max_score - min_score)

    return normalized_scores


def rerank_search_results_with_model(question, search_results, top_k=8):
    if not search_results:
        return []

    api_key = getattr(settings, 'RAG_RERANK_API_KEY', '')
    if not api_key:
        return search_results[:top_k]
    if not is_circuit_allowed('rerank'):
        logger.warning('rag rerank circuit open, fallback to rule rerank results')
        return search_results[:top_k]

    candidate_limit = max(
        top_k,
        int(getattr(settings, 'RAG_MODEL_RERANK_CANDIDATE_LIMIT', MODEL_RERANK_CANDIDATE_LIMIT)),
    )
    candidate_results = search_results[:candidate_limit]
    documents = [
        truncate_rerank_document_text(item.get('text') or '')
        for item in candidate_results
    ]

    model_name = getattr(settings, 'RAG_RERANK_MODEL', 'gte-rerank-v2')

    payload = {
        'model': model_name,
        'input': {
            'query': str(question or ''),
            'documents': documents,
        },
        'parameters': {
            'top_n': min(top_k, len(documents)),
            'return_documents': False,
        },
    }

    url = getattr(settings, 'RAG_RERANK_BASE_URL').rstrip('/')

    try:
        response = requests.post(
            url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=getattr(settings, 'RAG_RERANK_TIMEOUT', 30),
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        record_component_failure('rerank', e)
        logger.warning('rag rerank degraded model=%s error=%r', model_name, e)
        return search_results[:top_k]

    record_component_success('rerank')

    results_data = data.get('output', {}).get('results', [])
    model_score_map = {}

    for result in results_data:
        index = result.get('index')
        if index is None or index >= len(candidate_results):
            continue

        model_score_map[index] = float(result.get('relevance_score') or 0)

    if not model_score_map:
        return search_results[:top_k]

    normalized_rule_scores = normalize_item_scores(
        candidate_results,
        'rule_rerank_score',
    )

    reranked_results = []

    for index, item in enumerate(candidate_results):
        if index not in model_score_map:
            continue

        model_score = model_score_map[index]
        rule_score = normalized_rule_scores.get(index, 0)

        combined_score = (
            model_score * MODEL_RERANK_WEIGHT
            + rule_score * RULE_RERANK_WEIGHT
        )

        reranked_results.append({
            **item,
            'model_rerank_score': model_score,
            'normalized_rule_rerank_score': rule_score,
            'model_rule_combined_score': combined_score,
            'model_rerank_model': model_name,
        })

    reranked_results.sort(
        key=lambda item: item.get('model_rule_combined_score', 0),
        reverse=True,
    )

    return reranked_results[:top_k]
