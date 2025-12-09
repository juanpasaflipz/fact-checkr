import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from app.utils import get_redis_url

load_dotenv()

# Redis URL for broker and backend
# Prefers private endpoints (RAILWAY_PRIVATE_DOMAIN) to avoid egress fees
REDIS_URL = get_redis_url()

celery_app = Celery(
    "factcheckr_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.scraper", "app.tasks.fact_check", "app.tasks.health_check", "app.tasks.credit_topup", "app.tasks.market_notifications", "app.tasks.market_intelligence", "app.tasks.blog_generation"]
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
    # Using crontab-style scheduling for specific times
    beat_schedule={
        # Twitter scraping: 4 times per day at 6 AM, 12 PM, 6 PM, and midnight (Mexico City time)
        "scrape-twitter-6am": {
            "task": "app.tasks.scraper.scrape_all_sources",
            "schedule": crontab(hour=6, minute=0),  # 6:00 AM
            "options": {
                "expires": 21600,  # Expires after 6 hours
            }
        },
        "scrape-twitter-12pm": {
            "task": "app.tasks.scraper.scrape_all_sources",
            "schedule": crontab(hour=12, minute=0),  # 12:00 PM (noon)
            "options": {
                "expires": 21600,  # Expires after 6 hours
            }
        },
        "scrape-twitter-6pm": {
            "task": "app.tasks.scraper.scrape_all_sources",
            "schedule": crontab(hour=18, minute=0),  # 6:00 PM
            "options": {
                "expires": 21600,  # Expires after 6 hours
            }
        },
        "scrape-twitter-midnight": {
            "task": "app.tasks.scraper.scrape_all_sources",
            "schedule": crontab(hour=0, minute=0),  # 12:00 AM (midnight)
            "options": {
                "expires": 21600,  # Expires after 6 hours
            }
        },
        "health-check-every-5min": {
            "task": "app.tasks.health_check.health_check",
            "schedule": 300.0,  # Every 5 minutes
        },
        "monthly-credit-topup": {
            "task": "app.tasks.credit_topup.monthly_credit_topup",
            "schedule": crontab(day_of_month=1, hour=0, minute=0),  # 1st of month at midnight
            "options": {
                "expires": 86400,  # Expires after 24 hours
            }
        },
        "check-market-probability-changes": {
            "task": "app.tasks.market_notifications.check_market_probability_changes",
            "schedule": 3600.0,  # Every hour
        },
        "notify-new-markets": {
            "task": "app.tasks.market_notifications.notify_new_markets",
            "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM
        },
        "seed-new-markets": {
            "task": "app.tasks.market_intelligence.seed_new_markets",
            "schedule": 300.0,  # Every 5 minutes
        },
        "reassess-inactive-markets": {
            "task": "app.tasks.market_intelligence.reassess_inactive_markets",
            "schedule": 3600.0,  # Every hour
        },
        # Tier 1: Lightweight update every 2 hours (no LLM, just sentiment/news tracking)
        "tier1-lightweight-update": {
            "task": "app.tasks.market_intelligence.tier1_lightweight_update",
            "schedule": 7200.0,  # Every 2 hours
            "options": {
                "expires": 10800,  # Expires after 3 hours
            }
        },
        # Tier 2: Daily full analysis for all open markets
        "tier2-daily-analysis": {
            "task": "app.tasks.market_intelligence.tier2_daily_analysis",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
            "options": {
                "expires": 86400,  # Expires after 24 hours
            }
        },
        # Trending topic detection: Every 2 hours
        "detect-trending-topics": {
            "task": "app.tasks.scraper.detect_and_prioritize_topics",
            "schedule": crontab(minute=0, hour="*/2"),  # Every 2 hours
            "options": {
                "expires": 3600,  # 1 hour
            }
        },
        # Scrape prioritized topics: Every 30 minutes
        "scrape-prioritized-topics": {
            "task": "app.tasks.scraper.scrape_prioritized_topics",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
            "options": {
                "expires": 1800,  # 30 minutes
            }
        },
        # Blog article generation: 3-4 times daily
        "generate-morning-blog": {
            "task": "app.tasks.blog_generation.generate_morning_blog_article",
            "schedule": crontab(hour=9, minute=0),  # 9:00 AM
            "options": {
                "expires": 21600,  # 6 hours
            }
        },
        "generate-afternoon-blog": {
            "task": "app.tasks.blog_generation.generate_afternoon_blog_article",
            "schedule": crontab(hour=15, minute=0),  # 3:00 PM
            "options": {
                "expires": 21600,  # 6 hours
            }
        },
        "generate-evening-blog": {
            "task": "app.tasks.blog_generation.generate_evening_blog_article",
            "schedule": crontab(hour=21, minute=0),  # 9:00 PM
            "options": {
                "expires": 21600,  # 6 hours
            }
        },
        "generate-breaking-blog": {
            "task": "app.tasks.blog_generation.generate_breaking_blog_article",
            "schedule": crontab(hour=23, minute=30),  # 11:30 PM
            "options": {
                "expires": 21600,  # 6 hours
            }
        },
    },
    # Beat schedule persistence
    beat_schedule_filename="logs/celerybeat-schedule",
)

if __name__ == "__main__":
    celery_app.start()
