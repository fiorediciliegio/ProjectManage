import logging
import time
from dataclasses import dataclass, field

from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger("app01.rag_resilience")


@dataclass
class RagAdmission:
    allowed: bool
    status_code: int = 200
    message: str = ""
    retry_after: int = 0
    acquired_keys: list[str] = field(default_factory=list)


def _cache_get(key, default=None):
    try:
        return cache.get(key, default)
    except Exception as exc:
        logger.warning("rag resilience cache get failed key=%s error=%s", key, exc)
        return default


def _cache_set(key, value, timeout):
    try:
        cache.set(key, value, timeout=timeout)
        return True
    except Exception as exc:
        logger.warning("rag resilience cache set failed key=%s error=%s", key, exc)
        return False


def _cache_add(key, value, timeout):
    try:
        return cache.add(key, value, timeout=timeout)
    except Exception as exc:
        logger.warning("rag resilience cache add failed key=%s error=%s", key, exc)
        return False


def _cache_incr(key, delta=1):
    try:
        return cache.incr(key, delta)
    except ValueError:
        if _cache_add(key, 0, timeout=60):
            return _cache_incr(key, delta)
    except Exception as exc:
        logger.warning("rag resilience cache incr failed key=%s error=%s", key, exc)
    return None


def _cache_decr(key, delta=1):
    try:
        return cache.decr(key, delta)
    except ValueError:
        return None
    except Exception as exc:
        logger.warning("rag resilience cache decr failed key=%s error=%s", key, exc)
        return None


def _fixed_window_limit(scope, identity, limit, window_seconds):
    if limit <= 0:
        return True, 0

    now = int(time.time())
    window_id = now // window_seconds
    key = f"rag:rate:{scope}:{identity}:{window_id}"
    _cache_add(key, 0, timeout=window_seconds + 5)
    current = _cache_incr(key)
    retry_after = window_seconds - (now % window_seconds)

    if current is None:
        return True, 0
    if current > limit:
        return False, retry_after
    return True, 0


def _acquire_slot(key, limit, ttl):
    if limit <= 0:
        return True

    _cache_add(key, 0, timeout=ttl)
    current = _cache_incr(key)
    if current is None:
        return True
    if current > limit:
        _cache_decr(key)
        return False
    return True


def _release_slot(key):
    _cache_decr(key)


def check_rag_chat_admission(user_id, project_id):
    if not getattr(settings, "RAG_CHAT_RATE_LIMIT_ENABLED", True):
        return RagAdmission(allowed=True)

    window_seconds = int(getattr(settings, "RAG_CHAT_RATE_WINDOW_SECONDS", 60))
    user_limit = int(getattr(settings, "RAG_CHAT_USER_RATE_LIMIT_PER_MINUTE", 12))
    project_limit = int(getattr(settings, "RAG_CHAT_PROJECT_RATE_LIMIT_PER_MINUTE", 60))
    global_limit = int(getattr(settings, "RAG_CHAT_GLOBAL_RATE_LIMIT_PER_MINUTE", 120))

    checks = [
        ("global", "all", global_limit),
        ("project", project_id, project_limit),
        ("user", user_id, user_limit),
    ]
    for scope, identity, limit in checks:
        allowed, retry_after = _fixed_window_limit(scope, identity, limit, window_seconds)
        if not allowed:
            return RagAdmission(
                allowed=False,
                status_code=429,
                message="RAG 问答请求过于频繁，请稍后再试",
                retry_after=retry_after,
            )

    slot_ttl = int(getattr(settings, "RAG_CHAT_IN_FLIGHT_TTL", 300))
    global_in_flight_key = "rag:inflight:global"
    user_in_flight_key = f"rag:inflight:user:{user_id}"
    global_in_flight_limit = int(getattr(settings, "RAG_CHAT_GLOBAL_MAX_IN_FLIGHT", 8))
    user_in_flight_limit = int(getattr(settings, "RAG_CHAT_USER_MAX_IN_FLIGHT", 2))

    acquired_keys = []
    if not _acquire_slot(global_in_flight_key, global_in_flight_limit, slot_ttl):
        return RagAdmission(
            allowed=False,
            status_code=429,
            message="当前 RAG 问答并发较高，请稍后再试",
            retry_after=10,
        )
    acquired_keys.append(global_in_flight_key)

    if not _acquire_slot(user_in_flight_key, user_in_flight_limit, slot_ttl):
        for key in acquired_keys:
            _release_slot(key)
        return RagAdmission(
            allowed=False,
            status_code=429,
            message="你当前已有较多 RAG 问答正在进行，请等待上一个回答完成",
            retry_after=10,
        )
    acquired_keys.append(user_in_flight_key)

    return RagAdmission(allowed=True, acquired_keys=acquired_keys)


def release_rag_chat_admission(admission):
    for key in getattr(admission, "acquired_keys", []) or []:
        _release_slot(key)


def _component_settings(component):
    prefix = f"RAG_{component.upper()}_CIRCUIT"
    return {
        "threshold": int(getattr(settings, f"{prefix}_FAILURE_THRESHOLD", 3)),
        "open_seconds": int(getattr(settings, f"{prefix}_OPEN_SECONDS", 60)),
        "half_open_seconds": int(getattr(settings, f"{prefix}_HALF_OPEN_SECONDS", 15)),
    }


def is_circuit_allowed(component):
    if not getattr(settings, "RAG_CIRCUIT_BREAKER_ENABLED", True):
        return True

    opened_until = float(_cache_get(f"rag:circuit:{component}:opened_until", 0) or 0)
    now = time.time()
    if opened_until <= now:
        return True
    return False


def record_component_success(component):
    if not getattr(settings, "RAG_CIRCUIT_BREAKER_ENABLED", True):
        return

    _cache_set(f"rag:circuit:{component}:failure_count", 0, timeout=3600)
    _cache_set(f"rag:circuit:{component}:opened_until", 0, timeout=3600)


def record_component_failure(component, exc=None):
    if not getattr(settings, "RAG_CIRCUIT_BREAKER_ENABLED", True):
        return

    options = _component_settings(component)
    failure_key = f"rag:circuit:{component}:failure_count"
    _cache_add(failure_key, 0, timeout=3600)
    failures = _cache_incr(failure_key) or 1

    logger.warning(
        "rag component failure component=%s failures=%s error_type=%s error=%s",
        component,
        failures,
        exc.__class__.__name__ if exc else "",
        exc,
    )

    if failures >= options["threshold"]:
        opened_until = time.time() + options["open_seconds"]
        _cache_set(f"rag:circuit:{component}:opened_until", opened_until, timeout=options["open_seconds"])
        logger.warning(
            "rag circuit opened component=%s open_seconds=%s",
            component,
            options["open_seconds"],
        )
