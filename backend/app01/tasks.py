from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from elasticsearch import ConnectionError as ElasticsearchConnectionError
from elasticsearch import ConnectionTimeout as ElasticsearchConnectionTimeout
from elasticsearch import TransportError as ElasticsearchTransportError
from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError
from qdrant_client.http.exceptions import ApiException as QdrantApiException
from qdrant_client.http.exceptions import ResponseHandlingException as QdrantResponseHandlingException
from qdrant_client.http.exceptions import UnexpectedResponse as QdrantUnexpectedResponse
from requests import exceptions as requests_exceptions
import traceback

from app01.models import File
from app01.services.cache_service import invalidate_project_cache
from app01.services.langchain_rag_service import delete_langchain_file_vectors, index_file_to_qdrant_langchain


MAX_INDEX_ERROR_DETAIL_LENGTH = 4000


class IndexTaskCancelled(Exception):
    pass


def update_file_index_progress(file_id, **updates):
    allowed_fields = {
        'INDEX_STATUS_File',
        'INDEX_TASK_ID_File',
        'INDEX_STAGE_File',
        'INDEX_ERROR_File',
        'INDEX_ERROR_TYPE_File',
        'INDEX_ERROR_DETAIL_File',
        'INDEX_RETRY_COUNT_File',
        'INDEX_MAX_RETRIES_File',
        'INDEX_NEXT_RETRY_AT_File',
        'INDEX_RETRYABLE_File',
        'INDEX_CANCEL_REQUESTED_File',
        'INDEX_CANCELLED_AT_File',
        'INDEXED_AT_File',
    }
    filtered_updates = {
        field: value
        for field, value in updates.items()
        if field in allowed_fields
    }
    if filtered_updates:
        File.objects.filter(pk=file_id).update(**filtered_updates)
        project_id = (
            File.objects
            .filter(pk=file_id)
            .values_list('ID_Project_id', flat=True)
            .first()
        )
        if project_id is not None:
            invalidate_project_cache(project_id)


def build_index_error_detail(exc, failed_stage):
    detail = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    if len(detail) > MAX_INDEX_ERROR_DETAIL_LENGTH:
        detail = detail[-MAX_INDEX_ERROR_DETAIL_LENGTH:]
    return f'失败阶段: {failed_stage or "unknown"}\n{detail}'


def is_file_index_cancel_requested(file_id):
    return bool(
        File.objects
        .filter(pk=file_id)
        .values_list('INDEX_CANCEL_REQUESTED_File', flat=True)
        .first()
    )


def ensure_file_index_not_cancelled(file_id):
    if is_file_index_cancel_requested(file_id):
        raise IndexTaskCancelled('文件入库任务已被用户取消')


def build_stage_callback(file_id):
    def callback(stage):
        ensure_file_index_not_cancelled(file_id)
        update_file_index_progress(file_id, INDEX_STAGE_File=stage)
        ensure_file_index_not_cancelled(file_id)

    return callback


def get_file_index_stage(file_id):
    return (
        File.objects
        .filter(pk=file_id)
        .values_list('INDEX_STAGE_File', flat=True)
        .first()
    )


def get_index_retry_policy():
    return {
        'max_retries': max(0, int(getattr(settings, 'RAG_INDEX_MAX_RETRIES', 3))),
        'base_delay': max(1, int(getattr(settings, 'RAG_INDEX_RETRY_BASE_DELAY', 30))),
        'max_delay': max(1, int(getattr(settings, 'RAG_INDEX_RETRY_MAX_DELAY', 300))),
    }


def calculate_retry_countdown(retries_done, base_delay, max_delay):
    countdown = base_delay * (2 ** max(0, retries_done))
    return min(countdown, max_delay)


def get_exception_status_code(exc):
    for attr in ('status_code', 'status'):
        value = getattr(exc, attr, None)
        if value is not None:
            return value

    response = getattr(exc, 'response', None)
    if response is not None:
        return getattr(response, 'status_code', None) or getattr(response, 'status', None)

    return None


def is_retryable_index_exception(exc):
    retryable_exception_types = (
        APIConnectionError,
        APITimeoutError,
        InternalServerError,
        RateLimitError,
        QdrantResponseHandlingException,
        ElasticsearchConnectionError,
        ElasticsearchConnectionTimeout,
        requests_exceptions.ConnectionError,
        requests_exceptions.Timeout,
    )
    if isinstance(exc, retryable_exception_types):
        return True

    status_code = get_exception_status_code(exc)
    if isinstance(status_code, str) and status_code.isdigit():
        status_code = int(status_code)
    if status_code in {408, 429, 500, 502, 503, 504}:
        return True

    if isinstance(exc, (QdrantApiException, QdrantUnexpectedResponse, ElasticsearchTransportError)):
        return status_code is None or status_code >= 500 or status_code in {408, 429}

    if isinstance(exc, requests_exceptions.HTTPError):
        return status_code in {408, 429, 500, 502, 503, 504}

    return False


def schedule_file_index_retry(file_id, exc, failed_stage, retry_count, max_retries, countdown):
    update_file_index_progress(
        file_id,
        INDEX_STATUS_File='retrying',
        INDEX_STAGE_File='retry_wait',
        INDEX_ERROR_File=str(exc),
        INDEX_ERROR_TYPE_File=exc.__class__.__name__,
        INDEX_ERROR_DETAIL_File=build_index_error_detail(exc, failed_stage),
        INDEX_RETRY_COUNT_File=retry_count,
        INDEX_MAX_RETRIES_File=max_retries,
        INDEX_NEXT_RETRY_AT_File=timezone.now() + timedelta(seconds=countdown),
        INDEX_RETRYABLE_File=True,
    )


def mark_file_index_failed(file_id, exc, retryable=False, retry_count=None, max_retries=None):
    failed_stage = get_file_index_stage(file_id)
    update_file_index_progress(
        file_id,
        INDEX_STATUS_File='failed',
        INDEX_STAGE_File='failed',
        INDEX_ERROR_File=str(exc),
        INDEX_ERROR_TYPE_File=exc.__class__.__name__,
        INDEX_ERROR_DETAIL_File=build_index_error_detail(exc, failed_stage),
        INDEX_RETRY_COUNT_File=retry_count if retry_count is not None else 0,
        INDEX_MAX_RETRIES_File=max_retries if max_retries is not None else get_index_retry_policy()['max_retries'],
        INDEX_NEXT_RETRY_AT_File=None,
        INDEX_RETRYABLE_File=retryable,
    )


def mark_file_index_cancelled(file_id, exc=None, cleanup_error=None):
    detail_parts = []
    if exc:
        detail_parts.append(build_index_error_detail(exc, get_file_index_stage(file_id)))
    if cleanup_error:
        detail_parts.append('取消后清理索引失败:\n' + build_index_error_detail(cleanup_error, 'cancel_cleanup'))

    update_file_index_progress(
        file_id,
        INDEX_STATUS_File='cancelled',
        INDEX_STAGE_File='cancelled',
        INDEX_ERROR_File=str(cleanup_error or exc or '文件入库任务已取消'),
        INDEX_ERROR_TYPE_File=(cleanup_error or exc).__class__.__name__ if (cleanup_error or exc) else 'IndexTaskCancelled',
        INDEX_ERROR_DETAIL_File='\n\n'.join(detail_parts),
        INDEX_NEXT_RETRY_AT_File=None,
        INDEX_RETRYABLE_File=False,
        INDEX_CANCEL_REQUESTED_File=False,
        INDEX_CANCELLED_AT_File=timezone.now(),
        INDEXED_AT_File=None,
    )


def cleanup_cancelled_file_index(file_id):
    try:
        delete_langchain_file_vectors(file_id)
        return None
    except Exception as cleanup_error:
        return cleanup_error


@shared_task(bind=True)
def celery_health_check(self):
    return {
        'status': 'ok',
        'task_id': self.request.id,
        'message': 'Celery worker is ready.',
    }


@shared_task(bind=True)
def rag_index_file_task(self, file_id, rebuild=False):
    retry_policy = get_index_retry_policy()

    try:
        ensure_file_index_not_cancelled(file_id)
        update_file_index_progress(
            file_id,
            INDEX_STATUS_File='running',
            INDEX_TASK_ID_File=self.request.id,
            INDEX_STAGE_File='prepare',
            INDEX_ERROR_File='',
            INDEX_ERROR_TYPE_File='',
            INDEX_ERROR_DETAIL_File='',
            INDEX_RETRY_COUNT_File=self.request.retries,
            INDEX_MAX_RETRIES_File=retry_policy['max_retries'],
            INDEX_NEXT_RETRY_AT_File=None,
            INDEX_RETRYABLE_File=False,
            INDEX_CANCELLED_AT_File=None,
        )
        file_obj = File.objects.get(pk=file_id)
        result = index_file_to_qdrant_langchain(
            file_obj,
            stage_callback=build_stage_callback(file_id),
        )
        ensure_file_index_not_cancelled(file_id)

        update_file_index_progress(
            file_id,
            INDEX_STATUS_File='completed',
            INDEX_STAGE_File='completed',
            INDEX_ERROR_File='',
            INDEX_ERROR_TYPE_File='',
            INDEX_ERROR_DETAIL_File='',
            INDEX_RETRY_COUNT_File=self.request.retries,
            INDEX_MAX_RETRIES_File=retry_policy['max_retries'],
            INDEX_NEXT_RETRY_AT_File=None,
            INDEX_RETRYABLE_File=False,
            INDEX_CANCEL_REQUESTED_File=False,
            INDEX_CANCELLED_AT_File=None,
            INDEXED_AT_File=timezone.now(),
        )
        return result
    except IndexTaskCancelled as exc:
        cleanup_error = cleanup_cancelled_file_index(file_id)
        mark_file_index_cancelled(file_id, exc=exc, cleanup_error=cleanup_error)
        return {
            'file_id': file_id,
            'status': 'cancelled',
            'cleanup_error': str(cleanup_error) if cleanup_error else None,
        }
    except Exception as exc:
        if is_file_index_cancel_requested(file_id):
            cleanup_error = cleanup_cancelled_file_index(file_id)
            mark_file_index_cancelled(file_id, exc=IndexTaskCancelled(), cleanup_error=cleanup_error)
            return {
                'file_id': file_id,
                'status': 'cancelled',
                'cleanup_error': str(cleanup_error) if cleanup_error else None,
            }

        retryable = is_retryable_index_exception(exc)
        retries_done = self.request.retries
        if retryable and retries_done < retry_policy['max_retries']:
            countdown = calculate_retry_countdown(
                retries_done,
                retry_policy['base_delay'],
                retry_policy['max_delay'],
            )
            schedule_file_index_retry(
                file_id,
                exc,
                get_file_index_stage(file_id),
                retries_done + 1,
                retry_policy['max_retries'],
                countdown,
            )
            raise self.retry(
                exc=exc,
                countdown=countdown,
                max_retries=retry_policy['max_retries'],
            )

        mark_file_index_failed(
            file_id,
            exc,
            retryable=retryable,
            retry_count=retries_done,
            max_retries=retry_policy['max_retries'],
        )
        raise


@shared_task(bind=True)
def rag_delete_file_vectors_task(self, file_id):
    retry_policy = get_index_retry_policy()

    try:
        ensure_file_index_not_cancelled(file_id)
        update_file_index_progress(
            file_id,
            INDEX_STATUS_File='deleting',
            INDEX_TASK_ID_File=self.request.id,
            INDEX_STAGE_File='delete_vectors',
            INDEX_ERROR_File='',
            INDEX_ERROR_TYPE_File='',
            INDEX_ERROR_DETAIL_File='',
            INDEX_RETRY_COUNT_File=self.request.retries,
            INDEX_MAX_RETRIES_File=retry_policy['max_retries'],
            INDEX_NEXT_RETRY_AT_File=None,
            INDEX_RETRYABLE_File=False,
            INDEX_CANCELLED_AT_File=None,
        )
        file_obj = File.objects.get(pk=file_id)
        delete_result = delete_langchain_file_vectors(
            file_obj.pk,
            stage_callback=build_stage_callback(file_id),
        )
        ensure_file_index_not_cancelled(file_id)

        update_file_index_progress(
            file_id,
            INDEX_STATUS_File='not_indexed',
            INDEX_STAGE_File='idle',
            INDEX_ERROR_File='',
            INDEX_ERROR_TYPE_File='',
            INDEX_ERROR_DETAIL_File='',
            INDEX_RETRY_COUNT_File=self.request.retries,
            INDEX_MAX_RETRIES_File=retry_policy['max_retries'],
            INDEX_NEXT_RETRY_AT_File=None,
            INDEX_RETRYABLE_File=False,
            INDEX_CANCEL_REQUESTED_File=False,
            INDEX_CANCELLED_AT_File=None,
            INDEXED_AT_File=None,
        )
        return {
            'file_id': file_obj.pk,
            'delete_result': delete_result,
            'message': '文件向量和关键词索引删除成功',
        }
    except IndexTaskCancelled as exc:
        mark_file_index_cancelled(file_id, exc=exc)
        return {
            'file_id': file_id,
            'status': 'cancelled',
        }
    except Exception as exc:
        if is_file_index_cancel_requested(file_id):
            mark_file_index_cancelled(file_id, exc=IndexTaskCancelled())
            return {
                'file_id': file_id,
                'status': 'cancelled',
            }

        retryable = is_retryable_index_exception(exc)
        retries_done = self.request.retries
        if retryable and retries_done < retry_policy['max_retries']:
            countdown = calculate_retry_countdown(
                retries_done,
                retry_policy['base_delay'],
                retry_policy['max_delay'],
            )
            schedule_file_index_retry(
                file_id,
                exc,
                get_file_index_stage(file_id),
                retries_done + 1,
                retry_policy['max_retries'],
                countdown,
            )
            raise self.retry(
                exc=exc,
                countdown=countdown,
                max_retries=retry_policy['max_retries'],
            )

        mark_file_index_failed(
            file_id,
            exc,
            retryable=retryable,
            retry_count=retries_done,
            max_retries=retry_policy['max_retries'],
        )
        raise


@shared_task(bind=True)
def rag_finalize_file_index_cancel_task(self, file_id):
    file_state = (
        File.objects
        .filter(pk=file_id)
        .values('INDEX_STATUS_File', 'INDEX_CANCEL_REQUESTED_File')
        .first()
    )
    if not file_state:
        return {
            'file_id': file_id,
            'status': 'missing',
        }

    if not file_state['INDEX_CANCEL_REQUESTED_File'] or file_state['INDEX_STATUS_File'] != 'cancelling':
        return {
            'file_id': file_id,
            'status': 'skipped',
        }

    cleanup_error = cleanup_cancelled_file_index(file_id)
    mark_file_index_cancelled(
        file_id,
        exc=IndexTaskCancelled('文件入库任务已被用户取消'),
        cleanup_error=cleanup_error,
    )
    return {
        'file_id': file_id,
        'status': 'cancelled',
        'cleanup_error': str(cleanup_error) if cleanup_error else None,
    }
