import logging
import random
import re
import time

from django.conf import settings
from django.db import connection


logger = logging.getLogger("app01.performance")


def _compact_sql(sql, max_length=240):
    compacted = re.sub(r"\s+", " ", sql or "").strip()
    if len(compacted) <= max_length:
        return compacted
    return f"{compacted[:max_length]}..."


def _query_time_ms(query):
    try:
        return float(query.get("time", 0)) * 1000
    except (TypeError, ValueError):
        return 0


def _clear_query_log():
    queries_log = getattr(connection, "queries_log", None)
    if queries_log is not None:
        queries_log.clear()


class PerformanceLogMiddleware:
    """Log request latency and SQL query cost for selected hot API paths."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = bool(getattr(settings, "PERF_LOG_ENABLED", False))
        self.slow_request_ms = int(getattr(settings, "PERF_SLOW_REQUEST_MS", 500))
        self.slow_query_ms = int(getattr(settings, "PERF_SLOW_QUERY_MS", 100))
        self.query_warn_count = int(getattr(settings, "PERF_QUERY_WARN_COUNT", 30))
        self.sample_rate = float(getattr(settings, "PERF_LOG_SAMPLE_RATE", 1.0))
        self.path_prefixes = tuple(getattr(settings, "PERF_LOG_PATH_PREFIXES", ()))

    def __call__(self, request):
        if not self._should_log(request):
            return self.get_response(request)

        old_force_debug_cursor = connection.force_debug_cursor
        connection.force_debug_cursor = True
        _clear_query_log()

        started_at = time.perf_counter()
        response = None
        error = None
        try:
            response = self.get_response(request)
            return response
        except Exception as exc:
            error = exc
            raise
        finally:
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            queries = list(connection.queries)
            connection.force_debug_cursor = old_force_debug_cursor
            self._emit_log(request, response, error, duration_ms, queries)

    def _should_log(self, request):
        if not self.enabled:
            return False
        if self.path_prefixes and not request.path.startswith(self.path_prefixes):
            return False
        if self.sample_rate >= 1:
            return True
        return random.random() < self.sample_rate

    def _emit_log(self, request, response, error, duration_ms, queries):
        status_code = getattr(response, "status_code", 500)
        query_count = len(queries)
        total_query_ms = int(sum(_query_time_ms(query) for query in queries))
        slow_queries = [
            query
            for query in queries
            if _query_time_ms(query) >= self.slow_query_ms
        ]

        should_warn = (
            error is not None
            or duration_ms >= self.slow_request_ms
            or query_count >= self.query_warn_count
            or bool(slow_queries)
        )
        log_method = logger.warning if should_warn else logger.info
        log_method(
            "request method=%s path=%s status=%s duration_ms=%s db_queries=%s db_time_ms=%s slow_queries=%s user=%s",
            request.method,
            request.path,
            status_code,
            duration_ms,
            query_count,
            total_query_ms,
            len(slow_queries),
            getattr(getattr(request, "user", None), "username", "anonymous"),
        )

        for index, query in enumerate(slow_queries[:3], start=1):
            logger.warning(
                "slow_sql rank=%s path=%s time_ms=%s sql=%s",
                index,
                request.path,
                int(_query_time_ms(query)),
                _compact_sql(query.get("sql")),
            )
