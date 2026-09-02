import logging
import re

from django.conf import settings

from app01.services.rag_resilience_service import (
    is_circuit_allowed,
    record_component_failure,
    record_component_success,
)


logger = logging.getLogger("app01.rag_resilience")


def normalize_chat_history(history, max_rounds=5, max_message_chars=300):
    if not isinstance(history, list):
        return []

    valid_messages = []

    for message in history:
        if not isinstance(message, dict):
            continue

        role = message.get('role')
        content = str(message.get('content') or '').strip()

        if role not in ['user', 'assistant']:
            continue

        if not content:
            continue

        valid_messages.append({
            'role': role,
            'content': content[:max_message_chars],
        })

    return valid_messages[-max_rounds * 2:]


def truncate_rag_memory_summary(summary, max_chars=None):
    max_chars = max(0, int(max_chars or getattr(settings, 'RAG_CHAT_SUMMARY_MAX_CHARS', 2500)))
    summary = str(summary or '').strip()
    if not summary or max_chars <= 0:
        return ''
    return summary[:max_chars]


def build_extractive_chat_summary(history):
    history = normalize_chat_history(
        history,
        max_rounds=35,
        max_message_chars=getattr(settings, 'RAG_CHAT_SUMMARY_SOURCE_MESSAGE_CHARS', 500),
    )
    if not history:
        return ''

    lines = ['以下是较早多轮对话的压缩摘要，用于理解用户后续追问的上下文：']
    for index, item in enumerate(history, start=1):
        speaker = '用户' if item['role'] == 'user' else '助手'
        content = re.sub(r'\s+', ' ', item['content']).strip()
        lines.append(f'{index}. {speaker}：{content}')

    return truncate_rag_memory_summary('\n'.join(lines))


def summarize_chat_history_for_memory(history, previous_summary=''):
    history = normalize_chat_history(
        history,
        max_rounds=35,
        max_message_chars=getattr(settings, 'RAG_CHAT_SUMMARY_SOURCE_MESSAGE_CHARS', 500),
    )
    if not history:
        return truncate_rag_memory_summary(previous_summary)

    history_text = '\n'.join(
        f"{'用户' if item['role'] == 'user' else '助手'}：{item['content']}"
        for item in history
    )
    previous_summary = truncate_rag_memory_summary(previous_summary)

    if not settings.RAG_CHAT_API_KEY:
        return build_extractive_chat_summary(history)

    if not is_circuit_allowed('chat_model'):
        logger.warning('rag chat model circuit open, use extractive memory summary')
        return build_extractive_chat_summary(history)

    prompt = f'''
请把下面较早的项目文档问答历史压缩成长期记忆摘要，供后续多轮 RAG 问答理解上下文。

要求：
1. 保留用户长期关注的对象、问题、约束、结论、待确认事项。
2. 不要编造历史中没有的信息。
3. 去掉寒暄、重复表达和无关细节。
4. 用中文输出，控制在 {getattr(settings, 'RAG_CHAT_SUMMARY_MAX_CHARS', 2500)} 字以内。
5. 输出摘要正文即可，不要添加标题。

已有摘要：
{previous_summary or '无'}

较早对话原文：
{history_text}

长期记忆摘要：
'''.strip()

    try:
        from app01.services.langchain_rag_service import get_chat_client

        client = get_chat_client()
        response = client.chat.completions.create(
            model=settings.RAG_CHAT_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': '你是项目文档问答系统的长对话记忆压缩器，只负责忠实摘要历史对话。',
                },
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
            temperature=0,
        )
        record_component_success('chat_model')
    except Exception as exc:
        record_component_failure('chat_model', exc)
        logger.warning('rag memory summary degraded error=%r', exc)
        return build_extractive_chat_summary(history)

    summary = response.choices[0].message.content.strip()
    if not summary:
        return build_extractive_chat_summary(history)

    return truncate_rag_memory_summary(summary)


def rewrite_question_with_history(question, history=None, history_summary=''):
    history = normalize_chat_history(history)
    history_summary = truncate_rag_memory_summary(history_summary)

    if not history and not history_summary:
        return question
    if not is_circuit_allowed('chat_model'):
        logger.warning('rag chat model circuit open, skip query rewrite')
        return question

    history_text = '\n'.join(
        f"{'用户' if item['role'] == 'user' else '助手'}：{item['content']}"
        for item in history
    )

    prompt = f'''
请根据长期摘要和最近对话，把用户当前问题改写成一个完整、独立、适合项目文档检索的问题。

要求：
1. 只改写问题，不要回答问题。
2. 保留用户当前问题的真实意图。
3. 如果当前问题中有“它”“这个方法”“上面那个”等指代，请根据历史对话补全。
4. 不要添加历史对话中没有依据的新结论。
5. 输出一句改写后的问题。

长期摘要：
{history_summary or '无'}

最近对话：
{history_text or '无'}

用户当前问题：
{question}

改写后的独立问题：
'''.strip()

    try:
        from app01.services.langchain_rag_service import get_chat_client

        client = get_chat_client()
        response = client.chat.completions.create(
            model=settings.RAG_CHAT_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': '你是一个项目文档问答系统中的查询改写助手，只负责改写检索问题。',
                },
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
            temperature=0,
        )
        record_component_success('chat_model')
    except Exception as exc:
        record_component_failure('chat_model', exc)
        logger.warning('rag query rewrite degraded error=%r', exc)
        return question

    rewritten = response.choices[0].message.content.strip()

    if not rewritten:
        return question

    return rewritten
