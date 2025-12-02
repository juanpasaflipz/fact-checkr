"""
Quota Management Router

Endpoints for monitoring Twitter API quota usage.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.quota_manager import quota_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quota", tags=["quota"])


@router.get("/twitter")
async def get_twitter_quota_status(db: Session = Depends(get_db)):
    """Get Twitter API quota status"""
    status = quota_manager.get_quota_status(db)
    return status


@router.get("/twitter/usage")
async def get_twitter_usage(db: Session = Depends(get_db)):
    """Get current month's Twitter usage"""
    used = quota_manager.get_current_month_usage(db)
    remaining = quota_manager.get_remaining_quota(db)
    percentage = quota_manager.get_quota_percentage(db)
    
    return {
        "used": used,
        "remaining": remaining,
        "percentage_used": round(percentage, 2),
        "monthly_quota": quota_manager.monthly_quota,
        "posts_per_run": quota_manager.posts_per_run
    }

