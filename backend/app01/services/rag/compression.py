import json
import logging
import re

from django.conf import settings

from app01.services.rag.text_utils import (
    extract_query_terms,
    looks_like_table_or_figure_text,
    truncate_context_text,
)
from app01.services.rag_resilience_service import (
    is_circuit_allowed,
    record_component_failure,
    record_component_success,
)


logger = logging.getLogger("app01.rag_resilience")

CONTEXT_MAX_ITEMS = 8


def unique_values(values, max_items):
    unique_items = []
    seen = set()

    for value in values:
        value = str(value or '').strip()
        if not value or value in seen:
            continue
        unique_items.append(value)
        seen.add(value)
        if len(unique_items) >= max_items:
            break

    return unique_items


def split_context_units(text):
    text = str(text or '').replace('\r\n', '\n').replace('\r', '\n').strip()
    if not text:
        return []

    units = []
    for paragraph in re.split(r'\n+', text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if looks_like_table_or_figure_text(paragraph):
            units.append(paragraph)
            continue
        for sentence in re.split(r'(?<=[。！？!?；;])\s*', paragraph):
            sentence = sentence.strip()
            if sentence:
                units.append(sentence)
    return units


def build_contextual_query_terms(question):
    base_terms = extract_query_terms(question)
    stop_terms = {'这个', '那个', '哪些', '什么', '如何', '怎么', '是否', '进行', '一下'}
    terms = []

    for term in base_terms:
        term = str(term or '').strip()
        if not term or term in stop_terms:
            continue
        terms.append(term)
        if re.fullmatch(r'[\u4e00-\u9fff]{4,}', term):
            for size in [2, 3, 4]:
                for start in range(0, max(0, len(term) - size + 1)):
                    ngram = term[start:start + size]
                    if ngram not in stop_terms:
                        terms.append(ngram)

    return unique_values(terms, max_items=40)


def score_context_unit(unit, query_terms):
    unit = str(unit or '')
    lower_unit = unit.lower()
    score = 0.0

    for term in query_terms:
        lower_term = str(term or '').lower()
        if not lower_term:
            continue
        occurrences = lower_unit.count(lower_term)
        if occurrences <= 0:
            continue
        score += occurrences * (1.0 + min(len(lower_term), 8) / 8)

    if re.search(r'\d', unit):
        score += 0.2

    return score


def compress_table_like_context_text(text, query_terms, max_chars):
    lines = [
        line.strip()
        for line in str(text or '').splitlines()
        if line.strip()
    ]
    if not lines:
        return '', {'matched': False, 'compression_score': 0}

    selected_indexes = set()
    window = max(0, int(getattr(settings, 'RAG_CONTEXT_COMPRESSION_SENTENCE_WINDOW', 1)))
    max_sentences = max(1, int(getattr(settings, 'RAG_CONTEXT_COMPRESSION_MAX_SENTENCES', 6)))

    for index, line in enumerate(lines):
        if score_context_unit(line, query_terms) > 0:
            for neighbor_index in range(max(0, index - window), min(len(lines), index + window + 1)):
                selected_indexes.add(neighbor_index)

    if selected_indexes:
        selected_indexes.add(0)

    if not selected_indexes:
        return '', {'matched': False, 'compression_score': 0}

    selected_lines = [
        lines[index]
        for index in sorted(selected_indexes)[:max_sentences + 1]
    ]
    compressed_text = truncate_context_text('\n'.join(selected_lines), max_chars=max_chars)
    return compressed_text, {
        'matched': True,
        'compression_score': sum(score_context_unit(line, query_terms) for line in selected_lines),
    }


def compress_context_text_by_query(text, question):
    text = str(text or '').strip()
    max_chars = max(120, int(getattr(settings, 'RAG_CONTEXT_COMPRESSION_MAX_ITEM_CHARS', 900)))
    if not text:
        return '', {'matched': False, 'compressed': False, 'compression_score': 0}

    if len(text) <= max_chars:
        return text, {
            'matched': True,
            'compressed': False,
            'compression_score': 0,
            'compression_ratio': 1.0,
        }

    query_terms = build_contextual_query_terms(question)
    if not query_terms:
        compressed_text = truncate_context_text(text, max_chars=max_chars)
        return compressed_text, {
            'matched': True,
            'compressed': True,
            'compression_score': 0,
            'compression_ratio': len(compressed_text) / max(len(text), 1),
        }

    if looks_like_table_or_figure_text(text):
        compressed_text, metadata = compress_table_like_context_text(text, query_terms, max_chars)
    else:
        units = split_context_units(text)
        scored_units = [
            (index, score_context_unit(unit, query_terms))
            for index, unit in enumerate(units)
        ]
        matched_units = [
            (index, score)
            for index, score in scored_units
            if score > 0
        ]
        if not matched_units:
            return '', {
                'matched': False,
                'compressed': True,
                'compression_score': 0,
                'compression_ratio': 0,
            }

        window = max(0, int(getattr(settings, 'RAG_CONTEXT_COMPRESSION_SENTENCE_WINDOW', 1)))
        max_sentences = max(1, int(getattr(settings, 'RAG_CONTEXT_COMPRESSION_MAX_SENTENCES', 6)))
        selected_indexes = set()
        for index, _ in sorted(matched_units, key=lambda item: (-item[1], item[0]))[:max_sentences]:
            for neighbor_index in range(max(0, index - window), min(len(units), index + window + 1)):
                selected_indexes.add(neighbor_index)

        compressed_text = truncate_context_text(
            '\n'.join(units[index] for index in sorted(selected_indexes)),
            max_chars=max_chars,
        )
        metadata = {
            'matched': True,
            'compression_score': sum(score for _, score in matched_units),
        }

    if not compressed_text:
        return '', {
            **metadata,
            'compressed': True,
            'compression_ratio': 0,
        }

    return compressed_text, {
        **metadata,
        'compressed': len(compressed_text) < len(text),
        'compression_ratio': len(compressed_text) / max(len(text), 1),
    }


def rule_contextual_compress_search_results(search_results, question):
    if not getattr(settings, 'RAG_CONTEXT_COMPRESSION_ENABLED', True):
        return search_results

    candidate_limit = max(
        CONTEXT_MAX_ITEMS,
        int(getattr(settings, 'RAG_CONTEXT_COMPRESSION_CANDIDATE_LIMIT', 16)),
    )
    min_keep_items = max(0, int(getattr(settings, 'RAG_CONTEXT_COMPRESSION_MIN_KEEP_ITEMS', 6)))
    max_chars = max(120, int(getattr(settings, 'RAG_CONTEXT_COMPRESSION_MAX_ITEM_CHARS', 900)))
    drop_unmatched_after_min_keep = bool(
        getattr(settings, 'RAG_CONTEXT_COMPRESSION_DROP_UNMATCHED_AFTER_MIN_KEEP', False)
    )
    compressed_results = []

    for item in search_results[:candidate_limit]:
        original_text = str(item.get('text') or '').strip()
        if not original_text:
            continue

        compressed_text, compression_metadata = compress_context_text_by_query(
            original_text,
            question,
        )
        if not compressed_text:
            if drop_unmatched_after_min_keep and len(compressed_results) >= min_keep_items:
                continue
            compressed_text = truncate_context_text(original_text, max_chars=max_chars)
            compression_metadata = {
                **compression_metadata,
                'matched': False,
                'fallback_kept': True,
                'compressed': len(compressed_text) < len(original_text),
                'compression_ratio': len(compressed_text) / max(len(original_text), 1),
            }

        compressed_results.append({
            **item,
            'text': compressed_text,
            'original_text_chars': len(original_text),
            'contextual_compressed': bool(compression_metadata.get('compressed')),
            'contextual_compression_matched': bool(compression_metadata.get('matched')),
            'contextual_compression_score': compression_metadata.get('compression_score', 0),
            'contextual_compression_ratio': compression_metadata.get('compression_ratio', 1),
            'contextual_compression_fallback_kept': bool(compression_metadata.get('fallback_kept')),
        })

    return compressed_results or search_results[:candidate_limit]


def parse_llm_compression_response(content):
    content = str(content or '').strip()
    if not content:
        return []

    start = content.find('[')
    end = content.rfind(']')
    if start < 0 or end < start:
        return []

    try:
        data = json.loads(content[start:end + 1])
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    parsed_items = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            index = int(item.get('index'))
        except (TypeError, ValueError):
            continue
        compressed_text = str(item.get('compressed_text') or '').strip()
        keep = bool(item.get('keep', True))
        parsed_items.append({
            'index': index,
            'keep': keep,
            'compressed_text': compressed_text,
        })
    return parsed_items


def build_llm_compression_prompt(question, candidates, max_chars):
    candidate_blocks = []
    for index, item in enumerate(candidates, start=1):
        text = truncate_context_text(item.get('text') or '', max_chars=1200)
        metadata = [
            f'index: {index}',
            f"file_name: {item.get('file_name') or '未知文件'}",
            f"page: {item.get('page') or ''}",
            f"chunk_index: {item.get('chunk_index') or ''}",
            f"text: {text}",
        ]
        candidate_blocks.append('\n'.join(metadata))

    return f'''
请根据用户问题，对候选资料片段做语义级上下文压缩。

用户问题：
{question}

压缩要求：
1. 只保留能直接帮助回答用户问题的原文信息。
2. 可以删除无关句子，但不要改写、编造或补充资料中没有的信息。
3. 工程名称、时间、金额、编号、尺寸、比例、结论性表述必须保持原样。
4. 如果片段整体相关，可以保留关键段落；如果片段明显无关，keep 设为 false。
5. 每个 compressed_text 控制在 {max_chars} 字以内。
6. 只输出合法 JSON 数组，不要输出 Markdown，不要解释。

输出格式：
[
  {{"index": 1, "keep": true, "compressed_text": "压缩后的相关原文"}},
  {{"index": 2, "keep": false, "compressed_text": ""}}
]

候选资料：
{chr(10).join(candidate_blocks)}
'''.strip()


def llm_contextual_compress_search_results(search_results, question):
    if not getattr(settings, 'RAG_LLM_CONTEXT_COMPRESSION_ENABLED', True):
        return search_results
    if not settings.RAG_CHAT_API_KEY:
        return search_results
    if not is_circuit_allowed('context_compression'):
        logger.warning('rag context compression circuit open, fallback to rule compression')
        return search_results

    candidate_limit = max(0, int(getattr(settings, 'RAG_LLM_CONTEXT_COMPRESSION_CANDIDATE_LIMIT', 5)))
    min_chars = max(0, int(getattr(settings, 'RAG_LLM_CONTEXT_COMPRESSION_MIN_ITEM_CHARS', 350)))
    max_chars = max(120, int(getattr(settings, 'RAG_LLM_CONTEXT_COMPRESSION_MAX_ITEM_CHARS', 700)))
    min_keep_items = max(0, int(getattr(settings, 'RAG_CONTEXT_COMPRESSION_MIN_KEEP_ITEMS', 6)))
    model_name = getattr(settings, 'RAG_LLM_CONTEXT_COMPRESSION_MODEL', '') or settings.RAG_CHAT_MODEL

    candidate_indexes = [
        index
        for index, item in enumerate(search_results[:candidate_limit])
        if len(str(item.get('text') or '').strip()) >= min_chars
    ]
    if not candidate_indexes:
        return search_results

    candidates = [search_results[index] for index in candidate_indexes]
    prompt = build_llm_compression_prompt(question, candidates, max_chars=max_chars)

    try:
        from app01.services.langchain_rag_service import get_chat_client

        client = get_chat_client()
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    'role': 'system',
                    'content': '你是 RAG 系统的上下文压缩器，只做忠实的信息抽取和无关内容过滤。',
                },
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
            temperature=0,
        )
        record_component_success('context_compression')
    except Exception as exc:
        record_component_failure('context_compression', exc)
        logger.warning('rag llm context compression degraded model=%s error=%r', model_name, exc)
        return search_results

    parsed_items = parse_llm_compression_response(response.choices[0].message.content)
    if not parsed_items:
        return search_results

    parsed_map = {
        item['index']: item
        for item in parsed_items
    }
    compressed_results = []

    for original_index, item in enumerate(search_results):
        if original_index not in candidate_indexes:
            compressed_results.append(item)
            continue

        llm_item_index = candidate_indexes.index(original_index) + 1
        llm_item = parsed_map.get(llm_item_index)
        if not llm_item:
            compressed_results.append(item)
            continue

        compressed_text = truncate_context_text(llm_item.get('compressed_text') or '', max_chars=max_chars)
        keep_item = llm_item.get('keep', True) and bool(compressed_text)
        if not keep_item:
            if len(compressed_results) < min_keep_items:
                compressed_results.append({
                    **item,
                    'llm_contextual_compressed': False,
                    'llm_contextual_compression_model': model_name,
                    'llm_contextual_compression_fallback_kept': True,
                })
            continue

        original_text = str(item.get('text') or '')
        compressed_results.append({
            **item,
            'text': compressed_text,
            'llm_contextual_compressed': len(compressed_text) < len(original_text),
            'llm_contextual_compression_model': model_name,
            'llm_contextual_compression_ratio': len(compressed_text) / max(len(original_text), 1),
        })

    return compressed_results or search_results


def contextual_compress_search_results(search_results, question):
    rule_results = rule_contextual_compress_search_results(search_results, question)
    return llm_contextual_compress_search_results(rule_results, question)
