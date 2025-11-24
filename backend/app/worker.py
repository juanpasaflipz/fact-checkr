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
    include=["app.tasks.scraper", "app.tasks.fact_check"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Mexico_City",
    enable_utc=True,
    # Periodic tasks configuration (Beats)
    beat_schedule={
        "scrape-every-hour": {
            "task": "app.tasks.scraper.scrape_all_sources",
            "schedule": 3600.0,  # 1 hour (3600 seconds)
        },
    },
)

if __name__ == "__main__":
    celery_app.start()
