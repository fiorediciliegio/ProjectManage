import logging
import re

from django.conf import settings

from app01.services.rag.compression import contextual_compress_search_results
from app01.services.rag.context import (
    build_rag_sources,
    expand_search_results_with_neighbors,
    pack_rag_context,
)
from app01.services.rag.memory import (
    normalize_chat_history,
    rewrite_question_with_history,
    truncate_rag_memory_summary,
)
from app01.services.rag_resilience_service import (
    is_circuit_allowed,
    record_component_failure,
    record_component_success,
)


logger = logging.getLogger("app01.rag_resilience")


def should_hide_sources_for_answer(answer):
    no_answer_markers = [
        '资料中没有找到相关信息',
        '没有在项目文件中检索到相关内容',
    ]
    answer_text = answer or ''
    return any(marker in answer_text for marker in no_answer_markers)


def extract_cited_source_indexes(answer):
    cited_indexes = re.findall(r'\[资料\s*(\d+)]', answer or '')
    return {
        int(index)
        for index in cited_indexes
        if str(index).isdigit()
    }


def build_retrieval_fallback_answer(packed_results, max_items=5):
    if not packed_results:
        return '模型服务暂时不可用，并且没有检索到可用于降级回答的项目资料。'

    lines = [
        '模型服务暂时不可用，系统已降级为检索结果摘要。以下内容仅基于召回片段，建议恢复模型后重新提问：'
    ]
    for index, item in enumerate(packed_results[:max_items], start=1):
        text = re.sub(r'\s+', ' ', item.get('text') or '').strip()
        if len(text) > 220:
            text = text[:220] + '...'
        file_name = item.get('file_name') or '未知文件'
        page = item.get('page')
        location = f'，页码：{page}' if page else ''
        lines.append(f'{index}. {file_name}{location}：{text}')

    return '\n'.join(lines)


def yield_retrieval_fallback(reason, packed_results):
    logger.warning('rag chat degraded reason=%s', reason)
    yield {
        'type': 'notice',
        'code': 'rag_degraded',
        'message': reason,
    }
    yield {
        'type': 'delta',
        'content': build_retrieval_fallback_answer(packed_results),
    }
    yield {
        'type': 'done',
        'sources': build_rag_sources(packed_results, include_uncited=True),
        'degraded': True,
        'degrade_reason': reason,
    }


def answer_question_with_rag(question, project_id=None, limit=8, history=None, history_summary=''):
    from app01.services.langchain_rag_service import get_chat_client, hybrid_search_file_chunks

    standalone_question = rewrite_question_with_history(question, history, history_summary)
    compression_candidate_limit = max(
        limit,
        int(getattr(settings, 'RAG_CONTEXT_COMPRESSION_CANDIDATE_LIMIT', 16)),
    )
    search_results = hybrid_search_file_chunks(
        question=standalone_question,
        project_id=project_id,
        final_limit=compression_candidate_limit,
    )
    search_results = expand_search_results_with_neighbors(
        search_results,
        neighbor_size=1,
        allowed_extensions={'.pdf'},
    )
    search_results = contextual_compress_search_results(search_results, question=standalone_question)

    context, packed_results = pack_rag_context(search_results, question=standalone_question)

    if not context:
        yield {
            'type': 'delta',
            'content': '没有在项目文件中检索到相关内容。',
        }
        yield {
            'type': 'done',
            'sources': [],
        }
        return

    recent_history = normalize_chat_history(history)
    memory_summary = truncate_rag_memory_summary(history_summary)
    recent_history_text = '\n'.join(
        f"{'用户' if item['role'] == 'user' else '助手'}：{item['content']}"
        for item in recent_history
    )
    conversation_memory = f'''
    长期摘要：
    {memory_summary or '无'}

    最近对话：
    {recent_history_text or '无'}
    '''.strip()

    prompt = f'''
    你是一个严谨的项目文档问答助手。请只根据下面提供的参考资料回答用户问题。

    回答要求：
    1. 只能根据参考资料回答，不要使用资料外知识。
    2. 每个关键结论后必须标注来源编号，例如：[资料1]、[资料2]。
    3. 如果参考资料无法支持答案，请只回答“资料中没有找到相关信息”。
    4. 不要引用没有实际使用的资料编号。
    5. 回答要清晰、简洁，优先使用中文。
    6. 对话记忆只能用于理解当前问题指代，不可作为项目事实依据。

    用户原始问题：
    {question}

    用于检索的独立问题：
    {standalone_question}

    对话记忆：
    {conversation_memory}

    参考资料：
    {context}
    '''.strip()

    if not is_circuit_allowed('chat_model'):
        yield from yield_retrieval_fallback('回答模型熔断中，已降级为检索结果摘要', packed_results)
        return

    try:
        client = get_chat_client()

        stream = client.chat.completions.create(
            model=settings.RAG_CHAT_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': '你是一个严谨的项目文档问答助手，只能基于给定资料回答。',
                },
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
            temperature=0.2,
            max_tokens=getattr(settings, 'RAG_CHAT_MAX_TOKENS', 2400),
            stream=True,
        )
    except Exception as exc:
        record_component_failure('chat_model', exc)
        yield from yield_retrieval_fallback('回答模型请求失败，已降级为检索结果摘要', packed_results)
        return

    answer_parts = []

    try:
        for chunk in stream:
            choices = getattr(chunk, 'choices', None) or []
            if not choices:
                continue

            delta = getattr(choices[0], 'delta', None)
            content = getattr(delta, 'content', None)
            if content:
                answer_parts.append(content)
                yield {
                    'type': 'delta',
                    'content': content,
                }
    except Exception as exc:
        record_component_failure('chat_model', exc)
        yield from yield_retrieval_fallback('回答模型流式输出中断，已降级为检索结果摘要', packed_results)
        return

    record_component_success('chat_model')

    if should_hide_sources_for_answer(''.join(answer_parts)):
        packed_results = []

    answer_text = ''.join(answer_parts)

    if should_hide_sources_for_answer(answer_text):
        packed_results = []

    cited_indexes = extract_cited_source_indexes(answer_text)

    yield {
        'type': 'done',
        'sources': build_rag_sources(packed_results, cited_indexes=cited_indexes),
    }
