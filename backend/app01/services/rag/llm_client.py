from django.conf import settings
from openai import OpenAI

from app01.services.rag.http_clients import build_no_proxy_openai_http_client


def get_chat_client():
    if not settings.RAG_CHAT_API_KEY:
        raise ValueError('缺少 RAG_CHAT_API_KEY 配置')

    return OpenAI(
        api_key=settings.RAG_CHAT_API_KEY,
        base_url=settings.RAG_CHAT_BASE_URL,
        timeout=getattr(settings, 'RAG_CHAT_TIMEOUT', 45),
        http_client=build_no_proxy_openai_http_client(),
    )
