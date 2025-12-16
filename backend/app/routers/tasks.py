from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks, Request
from typing import Optional, Literal
from pydantic import BaseModel
import logging
import json
import uuid
import pytz
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings


# Database and Models
from app.database import SessionLocal
from app.database.models import JobStatus

# Task functions
from app.tasks import (
    scraper,
    market_notifications,
    market_intelligence,
    blog_generation,
    health_check,
    credit_topup
)

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)

# --- Models ---

class ScrapePayload(BaseModel):
    mode: Literal["all", "prioritized", "trending"] = "all"
    options: Optional[dict] = {}

class TrendingPayload(BaseModel):
    window_minutes: int = 15
    limit: int = 20

class BlogPayload(BaseModel):
    type: Literal["scheduled", "breaking", "morning", "afternoon", "evening"] = "scheduled"
    topic_id: Optional[int] = None

# --- Dependencies ---

async def verify_task_secret(x_task_secret: Optional[str] = Header(None)):
    """
    Verify that the request comes from a trusted source (Cloud Scheduler)
    """
    expected_secret = settings.TASK_SECRET
    if not expected_secret:
        if settings.ENVIRONMENT == "production":
             raise HTTPException(status_code=500, detail="Server misconfiguration: TASK_SECRET not set")
        logger.warning("TASK_SECRET not set! Task endpoint is insecure.")
        return
        
    if x_task_secret != expected_secret:
        logger.warning(f"Invalid task secret provided: {x_task_secret}")
        raise HTTPException(status_code=403, detail="Invalid task secret")

# --- Helpers ---

def track_job_start(db: Session, job_type: str, params: dict) -> str:
    """Create a new job status record"""
    job_id = str(uuid.uuid4())
    job = JobStatus(
        id=job_id,
        job_type=job_type,
        status="running",
        params=params,
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    return job_id

def update_job_status(job_id: str, status: str, result: dict = None, error: str = None):
    """Update job status (to be called inside the background task)"""
    db = SessionLocal()
    try:
        job = db.query(JobStatus).filter(JobStatus.id == job_id).first()
        if job:
            job.status = status
            job.result = result
            job.error_message = error
            if status in ["completed", "failed"]:
                job.completed_at = datetime.utcnow()
                if job.started_at:
                    job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
            db.commit()
    except Exception as e:
        logger.error(f"Failed to update job status for {job_id}: {e}")
    finally:
        db.close()

# --- Wrappers for Background Tasks ---

async def run_scrape_task(job_id: str, mode: str, options: dict):
    try:
        result = None
        if mode == "all":
            count = await scraper.scrape_all_sources()
            result = {"new_sources": count}
        elif mode == "prioritized":
            count = await scraper.scrape_prioritized_topics()
            result = {"new_sources": count}
        elif mode == "trending":
             # This might be redundant if we have a separate trending dispatch, 
             # but keeping it for flexibility
            count = await scraper.detect_and_prioritize_topics()
            result = {"topics_prioritized": count}
            
        update_job_status(job_id, "completed", result=result)
    except Exception as e:
        logger.error(f"Scrape task failed: {e}", exc_info=True)
        update_job_status(job_id, "failed", error=str(e))

async def run_trending_task(job_id: str, window_minutes: int):
    try:
        # Detect trending topics
        count = await scraper.detect_and_prioritize_topics()
        update_job_status(job_id, "completed", result={"topics_detected": count})
    except Exception as e:
        logger.error(f"Trending task failed: {e}", exc_info=True)
        update_job_status(job_id, "failed", error=str(e))

async def run_blog_task(job_id: str, edition: str):
    try:
        result = None
        if edition == "morning":
            result = await blog_generation.generate_morning_blog_article()
        elif edition == "afternoon":
            result = await blog_generation.generate_afternoon_blog_article()
        elif edition == "evening":
            result = await blog_generation.generate_evening_blog_article()
        elif edition == "breaking":
             # Breaking news logic is slightly different, usually triggered manually or by alert
             # For now we'll call the generic breaking generator
             result = await blog_generation.generate_breaking_blog_article()
             
        update_job_status(job_id, "completed", result={"article": result})
    except Exception as e:
        logger.error(f"Blog task failed: {e}", exc_info=True)
        update_job_status(job_id, "failed", error=str(e))

# --- Dispatch Endpoints ---

from app.infra.cloud_tasks import enqueue_task

# ...

@router.post("/scrape_dispatch", dependencies=[Depends(verify_task_secret)])
async def dispatch_scrape(payload: ScrapePayload):
    """
    Central dispatcher for scraping tasks.
    Enqueues Cloud Task.
    """
    # Map payload to Cloud Task
    task_id = enqueue_task(
        task_name="ingest_sources", 
        payload={
            "task_type": "ingest_sources",
            "platforms": ["twitter", "google_news"] # Default
        }
    )
    return {"status": "queued", "task_id": task_id, "mode": payload.mode}

@router.post("/trending_dispatch", dependencies=[Depends(verify_task_secret)])
async def dispatch_trending(payload: TrendingPayload):
    """
    Dispatcher for trending topic detection.
    """
    task_id = enqueue_task(
        task_name="detect_trending",
        payload={"task_type": "detect_trending", "limit": payload.limit}
    )
    return {"status": "queued", "task_id": task_id}

@router.post("/blog_dispatch", dependencies=[Depends(verify_task_secret)])
async def dispatch_blog(payload: BlogPayload):
    """
    Dispatcher for blog generation.
    """
    edition = payload.type
    
    # Smart scheduling logic
    if edition == "scheduled":
        tz = pytz.timezone("America/Mexico_City")
        now = datetime.now(tz)
        hour = now.hour
        
        if 5 <= hour < 12:
            edition = "morning"
        elif 12 <= hour < 18:
            edition = "afternoon"
        else:
            edition = "evening"
    
    task_id = enqueue_task(
        task_name="generate_blog",
        payload={
            "task_type": "generate_blog", 
            "edition": edition
        }
    )
    return {"status": "queued", "task_id": task_id, "edition": edition}

# --- Legacy/Maintenance Endpoints ---

@router.post("/health-check", dependencies=[Depends(verify_task_secret)])
async def task_health_check():
    # health_check task not yet exposed in cloud_tasks.py but we can run it locally or ignore
    # For now, just return ok
    return {"status": "ignored"}

@router.post("/monthly-credit-topup", dependencies=[Depends(verify_task_secret)])
async def task_credit_topup():
    return {"status": "ignored"}

