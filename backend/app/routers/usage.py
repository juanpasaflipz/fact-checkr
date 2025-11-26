"""Usage tracking routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.database.models import User
from app.auth import get_current_user
from app.utils import get_current_usage, get_user_tier, get_tier_limit, TIER_LIMITS
from app.database.models import SubscriptionTier

router = APIRouter(prefix="/usage", tags=["usage"])

class UsageResponse(BaseModel):
    usage_type: str
    current_usage: int
    limit: Optional[int]
    is_unlimited: bool
    remaining: Optional[int]

class UsageSummaryResponse(BaseModel):
    tier: str
    usage: list[UsageResponse]
    limits: dict

@router.get("/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's usage summary"""
    tier = get_user_tier(db, user.id)
    limits = TIER_LIMITS.get(tier, TIER_LIMITS[SubscriptionTier.FREE])
    
    usage_types = [
        "verifications_per_month",
        "api_calls_per_day",
        "search_queries_per_day",
        "exports_per_month",
    ]
    
    usage_list = []
    for usage_type in usage_types:
        limit = get_tier_limit(tier, usage_type)
        current = get_current_usage(db, user.id, usage_type)
        is_unlimited = limit is None
        
        usage_list.append(UsageResponse(
            usage_type=usage_type,
            current_usage=current,
            limit=limit,
            is_unlimited=is_unlimited,
            remaining=None if is_unlimited else max(0, limit - current)
        ))
    
    return UsageSummaryResponse(
        tier=tier.value,
        usage=usage_list,
        limits=limits
    )

