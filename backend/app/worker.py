import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Redis URL for broker and backend
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "factcheckr_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.scraper", "app.tasks.fact_check", "app.tasks.health_check"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Mexico_City",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,  # Acknowledge tasks after completion, not before
    task_reject_on_worker_lost=True,  # Re-queue tasks if worker dies
    worker_prefetch_multiplier=1,  # Only prefetch one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks to prevent memory leaks
    
    # Retry configuration
    task_autoretry_for=(Exception,),  # Retry on any exception
    task_retry_backoff=True,  # Exponential backoff
    task_retry_backoff_max=600,  # Max 10 minutes between retries
    task_retry_jitter=True,  # Add randomness to retry delays
    task_max_retries=3,  # Max 3 retries per task
    
    # Timeout settings (increased for scraping which can take longer)
    task_time_limit=900,  # Hard limit: 15 minutes (scraping + transcription can be slow)
    task_soft_time_limit=840,  # Soft limit: 14 minutes (raises SoftTimeLimitExceeded)
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_disable_rate_limits=False,
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Periodic tasks configuration (Beats)
    beat_schedule={
        "scrape-every-hour": {
            "task": "app.tasks.scraper.scrape_all_sources",
            "schedule": 3600.0,  # 1 hour (3600 seconds)
            "options": {
                "expires": 7200,  # Task expires if not executed within 2 hours (more lenient)
            }
        },
        "health-check-every-5min": {
            "task": "app.tasks.health_check.health_check",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
    # Beat schedule persistence
    beat_schedule_filename="logs/celerybeat-schedule",
)

if __name__ == "__main__":
    celery_app.start()
