from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ecommerce",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.order_tasks",
        "app.tasks.notification_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_max_retries=3,
    task_default_retry_delay=60,
    beat_schedule={
        "cleanup-expired-tokens": {
            "task": "app.tasks.notification_tasks.cleanup_expired_sessions",
            "schedule": 3600.0,
        },
    },
)
