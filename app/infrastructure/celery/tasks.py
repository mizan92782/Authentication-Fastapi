from celery import shared_task
from app.core.logging import get_logger

logger = get_logger(__name__)


@shared_task(
    bind=True,
    name="app.tasks.order_tasks.send_order_confirmation",
    max_retries=3,
    default_retry_delay=60,
)
def send_order_confirmation(self, order_id: str, user_id: str) -> dict:
    try:
        logger.info("sending_order_confirmation", order_id=order_id, user_id=user_id)
        # Email sending logic here (SMTP / SES)
        return {"status": "sent", "order_id": order_id}
    except Exception as exc:
        logger.error("order_confirmation_failed", order_id=order_id, error=str(exc))
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="app.tasks.order_tasks.update_inventory",
    max_retries=3,
    default_retry_delay=30,
)
def update_inventory(self, order_id: str) -> dict:
    try:
        logger.info("updating_inventory", order_id=order_id)
        # Inventory sync logic (warehouse, ERP, etc.)
        return {"status": "updated", "order_id": order_id}
    except Exception as exc:
        logger.error("inventory_update_failed", order_id=order_id, error=str(exc))
        raise self.retry(exc=exc)
