import json
from collections import Counter

from celery import current_app
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count
from redis import Redis

from app01.models import File


def _task_name(task):
    if isinstance(task, dict):
        request = task.get("request")
        if isinstance(request, dict):
            return request.get("name") or task.get("name") or "unknown"
        return task.get("name") or "unknown"
    return "unknown"


def _count_worker_tasks(tasks_by_worker):
    counts = Counter()
    total = 0
    if not tasks_by_worker:
        return {"total": 0, "by_task": {}}

    for tasks in tasks_by_worker.values():
        for task in tasks or []:
            total += 1
            counts[_task_name(task)] += 1
    return {
        "total": total,
        "by_task": dict(sorted(counts.items())),
    }


def _get_broker_queue_depths(queue_names):
    client = Redis.from_url(
        settings.CELERY_BROKER_URL,
        socket_connect_timeout=1,
        socket_timeout=1,
        decode_responses=True,
    )
    return {
        queue_name: client.llen(queue_name)
        for queue_name in queue_names
    }


class Command(BaseCommand):
    help = "Print a snapshot of RAG file index statuses and Celery worker queues."

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=float, default=1.0)
        parser.add_argument("--indent", type=int, default=2)
        parser.add_argument(
            "--skip-celery-inspect",
            action="store_true",
            help="Only read database file states; skip Celery remote inspect calls.",
        )
        parser.add_argument(
            "--skip-broker-depth",
            action="store_true",
            help="Skip Redis LLEN checks for configured Celery queues.",
        )

    def handle(self, *args, **options):
        timeout = options["timeout"]
        indent = options["indent"]
        skip_celery_inspect = options["skip_celery_inspect"]
        skip_broker_depth = options["skip_broker_depth"]

        status_counts = {
            row["INDEX_STATUS_File"]: row["count"]
            for row in (
                File.objects
                .values("INDEX_STATUS_File")
                .annotate(count=Count("id"))
                .order_by("INDEX_STATUS_File")
            )
        }
        stage_counts = {
            row["INDEX_STAGE_File"]: row["count"]
            for row in (
                File.objects
                .values("INDEX_STAGE_File")
                .annotate(count=Count("id"))
                .order_by("INDEX_STAGE_File")
            )
        }

        celery_error = None
        broker_error = None
        broker_queue_depths = {}
        stats = {}
        active = {}
        reserved = {}
        scheduled = {}
        if skip_broker_depth:
            broker_error = "skipped"
        else:
            try:
                broker_queue_depths = _get_broker_queue_depths(settings.CELERY_MONITORED_QUEUES)
            except Exception as exc:
                broker_error = str(exc)

        if skip_celery_inspect:
            celery_error = "skipped"
        else:
            try:
                inspect = current_app.control.inspect(timeout=timeout)
                stats = inspect.stats() or {}
                active = inspect.active() or {}
                reserved = inspect.reserved() or {}
                scheduled = inspect.scheduled() or {}
            except Exception as exc:
                celery_error = str(exc)

        snapshot = {
            "files": {
                "total": File.objects.count(),
                "by_index_status": status_counts,
                "by_index_stage": stage_counts,
            },
            "celery": {
                "workers_online": len(stats),
                "error": celery_error,
                "broker_error": broker_error,
                "broker_queue_depths": broker_queue_depths,
                "active": _count_worker_tasks(active),
                "reserved": _count_worker_tasks(reserved),
                "scheduled": _count_worker_tasks(scheduled),
            },
        }

        self.stdout.write(json.dumps(snapshot, ensure_ascii=False, indent=indent))
