"""
Quota Management Router

Endpoints for monitoring Twitter API quota usage and user verification quotas.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.quota_manager import quota_manager
from app.auth import get_current_user, get_optional_user
from app.database.models import User
from app.utils import get_user_tier, get_current_usage, check_user_limit, TIER_LIMITS, get_tier_limit
from app.database.models import SubscriptionTier
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


@router.get("/check")
async def check_verification_quota(
    db: Session = Depends(get_db),
    user: User = Depends(get_optional_user)
):
    """Check user's verification quota status"""
    if not user:
        # For anonymous users, return free tier limits
        tier_limits = TIER_LIMITS.get(SubscriptionTier.FREE, {})
        return {
            "tier": "free",
            "limit": tier_limits.get("verifications_per_day", 10),
            "used": 0,
            "remaining": tier_limits.get("verifications_per_day", 10),
            "is_unlimited": False,
            "is_authenticated": False
        }
    
    tier = get_user_tier(db, user.id)
    limit_type = "verifications_per_day"
    limit = get_tier_limit(tier, limit_type)
    used = get_current_usage(db, user.id, limit_type)
    
    is_unlimited = limit is None
    
    return {
        "tier": tier.value,
        "limit": limit,
        "used": used,
        "remaining": None if is_unlimited else max(0, limit - used),
        "is_unlimited": is_unlimited,
        "is_authenticated": True
    }

