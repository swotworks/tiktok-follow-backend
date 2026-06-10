from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
import redis

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BROKER_URL
)

# Test Redis connection; fall back to eager (inline) execution if unavailable
try:
    r = redis.from_url(settings.CELERY_BROKER_URL, socket_timeout=1)
    r.ping()
except Exception:
    print("WARNING: Redis is not running. Enabling celery task_always_eager mode (running tasks inline).")
    celery_app.conf.task_always_eager = True

celery_app.conf.task_routes = {
    "app.worker.tasks.*": "main-queue"
}

celery_app.conf.beat_schedule = {
    "check-unfollows-daily": {
        "task": "check_unfollow_drops",
        "schedule": crontab(hour=0, minute=0),
    }
}
