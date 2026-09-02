import logging

from django.conf import settings
from django.core.cache import cache

from app01.response import success_response


logger = logging.getLogger("app01.cache")

CACHE_MISS = object()
PROJECTS_VERSION_KEY = "api-cache:version:projects"
PROJECT_VERSION_KEY_TEMPLATE = "api-cache:version:project:{project_id}"


def api_cache_enabled():
    return bool(getattr(settings, "API_CACHE_ENABLED", False))


def get_api_cache_timeout(name, default):
    return int(getattr(settings, name, default))


def _safe_cache_get(key, default=None):
    try:
        return cache.get(key, default)
    except Exception as exc:
        logger.warning("cache get failed key=%s error=%s", key, exc)
        return default


def _safe_cache_set(key, value, timeout):
    try:
        cache.set(key, value, timeout=timeout)
        return True
    except Exception as exc:
        logger.warning("cache set failed key=%s error=%s", key, exc)
        return False


def _safe_cache_add(key, value, timeout=None):
    try:
        cache.add(key, value, timeout=timeout)
        return True
    except Exception as exc:
        logger.warning("cache add failed key=%s error=%s", key, exc)
        return False


def _safe_cache_incr(key):
    try:
        return cache.incr(key)
    except Exception as exc:
        logger.warning("cache incr failed key=%s error=%s", key, exc)
        return None


def _version_key_for_project(project_id):
    return PROJECT_VERSION_KEY_TEMPLATE.format(project_id=project_id)


def _get_cache_version(version_key):
    version = _safe_cache_get(version_key)
    if version is None:
        _safe_cache_add(version_key, 1)
        return 1
    return version


def _bump_cache_version(version_key):
    _safe_cache_add(version_key, 1)
    bumped = _safe_cache_incr(version_key)
    if bumped is None:
        _safe_cache_set(version_key, 2, timeout=None)


def _request_scope(request):
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return f"user:{user.pk}"
    return "anonymous"


def build_project_cache_key(request, resource, project_id=None, *parts):
    global_version = _get_cache_version(PROJECTS_VERSION_KEY)
    project_version = "none"
    if project_id is not None:
        project_version = _get_cache_version(_version_key_for_project(project_id))

    safe_parts = ":".join(str(part) for part in parts if part is not None)
    return (
        f"api-cache:v1:{resource}:global:{global_version}:"
        f"project:{project_id or 'all'}:{project_version}:"
        f"scope:{_request_scope(request)}:{safe_parts}"
    )


def cached_success_response(request, cache_key, producer, message, timeout, status_code=200):
    if not api_cache_enabled() or request.method != "GET":
        return success_response(
            data=producer(),
            message=message,
            status_code=status_code,
        )

    cached_data = _safe_cache_get(cache_key, CACHE_MISS)
    if cached_data is not CACHE_MISS:
        response = success_response(
            data=cached_data,
            message=message,
            status_code=status_code,
        )
        response["X-API-Cache"] = "HIT"
        return response

    data = producer()
    _safe_cache_set(cache_key, data, timeout)
    response = success_response(
        data=data,
        message=message,
        status_code=status_code,
    )
    response["X-API-Cache"] = "MISS"
    return response


def invalidate_project_cache(project_id=None, include_global=False):
    if not api_cache_enabled():
        return

    if include_global:
        _bump_cache_version(PROJECTS_VERSION_KEY)
    if project_id is not None:
        _bump_cache_version(_version_key_for_project(project_id))
