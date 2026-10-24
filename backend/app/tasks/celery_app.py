"""
Civic Dispatch — Celery Background Worker & Periodic Beat Scheduler
Runs periodic SLA evaluation sweeps and asynchronous notifications.
"""

import os
from celery import Celery
from celery.schedules import crontab

def make_celery(app=None):
    broker = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    celery = Celery(
        "civic_dispatch",
        broker=broker,
        backend=backend,
        include=["app.tasks.celery_app"]
    )

    celery.conf.update(
        timezone="UTC",
        enable_utc=True,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        beat_schedule={
            "evaluate-slas-every-5-minutes": {
                "task": "app.tasks.celery_app.evaluate_slas_task",
                "schedule": 300.0,  # Every 5 minutes
            },
        }
    )

    if app:
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        celery.Task = ContextTask

    return celery

celery_app = make_celery()

@celery_app.task(name="app.tasks.celery_app.evaluate_slas_task", bind=True, max_retries=3)
def evaluate_slas_task(self):
    """Periodic Celery background task evaluating active complaints against SLA deadlines."""
    try:
        from app import create_app
        from app.sla.engine import SLAEngine
        flask_app = create_app()
        with flask_app.app_context():
            results = SLAEngine.run_evaluation()
            return results
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
