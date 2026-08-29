from celery import shared_task


@shared_task(bind=True)
def celery_health_check(self):
    return {
        'status': 'ok',
        'task_id': self.request.id,
        'message': 'Celery worker is ready.',
    }
