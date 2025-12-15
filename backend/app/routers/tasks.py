from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from typing import Optional
import os
import logging
from datetime import datetime

# Import task functions
# We import them inside functions or use string references if we want to avoid circular imports,
# but for this router, direct imports are usually fine if the tasks don't import this router.
from app.tasks import (
    scraper,
    fact_check,
    health_check,
    credit_topup,
    market_notifications,
    market_intelligence,
    blog_generation
)

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)

# Security dependency
async def verify_task_secret(x_task_secret: Optional[str] = Header(None)):
    """
    Verify that the request comes from a trusted source (Cloud Scheduler)
    """
    expected_secret = os.getenv("TASK_SECRET")
    if not expected_secret:
        # If no secret is configured, we warn but might allow for dev (or deny for safety)
        # For production, we MUST have a secret.
        logger.warning("TASK_SECRET not set! Task endpoint is insecure.")
        if os.getenv("ENVIRONMENT") == "production":
             raise HTTPException(status_code=500, detail="Server misconfiguration: TASK_SECRET not set")
        return
        
    if x_task_secret != expected_secret:
        logger.warning(f"Invalid task secret provided: {x_task_secret}")
        raise HTTPException(status_code=403, detail="Invalid task secret")

# --- Scraper Tasks ---

@router.post("/scrape-twitter-6am", dependencies=[Depends(verify_task_secret)])
async def task_scrape_twitter_6am(background_tasks: BackgroundTasks):
    """Trigger the 6AM scrape of all sources"""
    logger.info("Triggering scrape-twitter-6am")
    # Run in background to reply quickly to Cloud Scheduler (avoids timeout if < 60 mins)
    background_tasks.add_task(scraper.scrape_all_sources)
    return {"status": "triggered", "task": "scrape_all_sources", "timestamp": datetime.utcnow().isoformat()}

@router.post("/scrape-twitter-12pm", dependencies=[Depends(verify_task_secret)])
async def task_scrape_twitter_12pm(background_tasks: BackgroundTasks):
    logger.info("Triggering scrape-twitter-12pm")
    background_tasks.add_task(scraper.scrape_all_sources)
    return {"status": "triggered", "task": "scrape_all_sources"}

@router.post("/scrape-twitter-6pm", dependencies=[Depends(verify_task_secret)])
async def task_scrape_twitter_6pm(background_tasks: BackgroundTasks):
    logger.info("Triggering scrape-twitter-6pm")
    background_tasks.add_task(scraper.scrape_all_sources)
    return {"status": "triggered", "task": "scrape_all_sources"}

@router.post("/scrape-twitter-midnight", dependencies=[Depends(verify_task_secret)])
async def task_scrape_twitter_midnight(background_tasks: BackgroundTasks):
    logger.info("Triggering scrape-twitter-midnight")
    background_tasks.add_task(scraper.scrape_all_sources)
    return {"status": "triggered", "task": "scrape_all_sources"}

@router.post("/detect-trending-topics", dependencies=[Depends(verify_task_secret)])
async def task_detect_trending_topics(background_tasks: BackgroundTasks):
    logger.info("Triggering detect-trending-topics")
    background_tasks.add_task(scraper.detect_and_prioritize_topics)
    return {"status": "triggered", "task": "detect_and_prioritize_topics"}

@router.post("/scrape-prioritized-topics", dependencies=[Depends(verify_task_secret)])
async def task_scrape_prioritized_topics(background_tasks: BackgroundTasks):
    logger.info("Triggering scrape-prioritized-topics")
    background_tasks.add_task(scraper.scrape_prioritized_topics)
    return {"status": "triggered", "task": "scrape_prioritized_topics"}

# --- Market Tasks ---

@router.post("/check-market-probability-changes", dependencies=[Depends(verify_task_secret)])
async def task_check_market_prob(background_tasks: BackgroundTasks):
    logger.info("Triggering check-market-probability-changes")
    background_tasks.add_task(market_notifications.check_market_probability_changes)
    return {"status": "triggered", "task": "check_market_probability_changes"}

@router.post("/notify-new-markets", dependencies=[Depends(verify_task_secret)])
async def task_notify_new_markets(background_tasks: BackgroundTasks):
    logger.info("Triggering notify-new-markets")
    background_tasks.add_task(market_notifications.notify_new_markets)
    return {"status": "triggered", "task": "notify_new_markets"}

@router.post("/seed-new-markets", dependencies=[Depends(verify_task_secret)])
async def task_seed_new_markets(background_tasks: BackgroundTasks):
    logger.info("Triggering seed-new-markets")
    background_tasks.add_task(market_intelligence.seed_new_markets)
    return {"status": "triggered", "task": "seed_new_markets"}

@router.post("/reassess-inactive-markets", dependencies=[Depends(verify_task_secret)])
async def task_reassess_inactive(background_tasks: BackgroundTasks):
    logger.info("Triggering reassess-inactive-markets")
    background_tasks.add_task(market_intelligence.reassess_inactive_markets)
    return {"status": "triggered", "task": "reassess_inactive_markets"}

@router.post("/tier1-lightweight-update", dependencies=[Depends(verify_task_secret)])
async def task_tier1_update(background_tasks: BackgroundTasks):
    logger.info("Triggering tier1-lightweight-update")
    background_tasks.add_task(market_intelligence.tier1_lightweight_update)
    return {"status": "triggered", "task": "tier1_lightweight_update"}

@router.post("/tier2-daily-analysis", dependencies=[Depends(verify_task_secret)])
async def task_tier2_analysis(background_tasks: BackgroundTasks):
    logger.info("Triggering tier2-daily-analysis")
    background_tasks.add_task(market_intelligence.tier2_daily_analysis)
    return {"status": "triggered", "task": "tier2_daily_analysis"}

# --- Blog Tasks ---

@router.post("/generate-morning-blog", dependencies=[Depends(verify_task_secret)])
async def task_morning_blog(background_tasks: BackgroundTasks):
    logger.info("Triggering generate-morning-blog")
    background_tasks.add_task(blog_generation.generate_morning_blog_article)
    return {"status": "triggered", "task": "generate_morning_blog_article"}

@router.post("/generate-afternoon-blog", dependencies=[Depends(verify_task_secret)])
async def task_afternoon_blog(background_tasks: BackgroundTasks):
    logger.info("Triggering generate-afternoon-blog")
    background_tasks.add_task(blog_generation.generate_afternoon_blog_article)
    return {"status": "triggered", "task": "generate_afternoon_blog_article"}

@router.post("/generate-evening-blog", dependencies=[Depends(verify_task_secret)])
async def task_evening_blog(background_tasks: BackgroundTasks):
    logger.info("Triggering generate-evening-blog")
    background_tasks.add_task(blog_generation.generate_evening_blog_article)
    return {"status": "triggered", "task": "generate_evening_blog_article"}

@router.post("/generate-breaking-blog", dependencies=[Depends(verify_task_secret)])
async def task_breaking_blog(background_tasks: BackgroundTasks):
    logger.info("Triggering generate-breaking-blog")
    background_tasks.add_task(blog_generation.generate_breaking_blog_article)
    return {"status": "triggered", "task": "generate_breaking_blog_article"}

# --- Maintenance Tasks ---

@router.post("/health-check", dependencies=[Depends(verify_task_secret)])
async def task_health_check(background_tasks: BackgroundTasks):
    logger.info("Triggering health-check")
    background_tasks.add_task(health_check.health_check)
    return {"status": "triggered", "task": "health_check"}

@router.post("/monthly-credit-topup", dependencies=[Depends(verify_task_secret)])
async def task_credit_topup(background_tasks: BackgroundTasks):
    logger.info("Triggering monthly-credit-topup")
    background_tasks.add_task(credit_topup.monthly_credit_topup)
    return {"status": "triggered", "task": "monthly_credit_topup"}
