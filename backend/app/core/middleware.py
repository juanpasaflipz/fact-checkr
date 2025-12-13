"""Middleware for tier-based access control and usage tracking"""
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Callable
from functools import wraps

from app.database.connection import get_db
from app.database.models import User, SubscriptionTier
from sqlalchemy.orm import Session
from app.core.utils import (
    get_user_tier,
    check_user_limit,
    track_usage,
    is_limit_unlimited,
    get_tier_limit,
)
from app.core.auth import get_optional_user as get_optional_user_dep

class TierChecker:
    """Middleware for checking tier-based limits"""
    
    @staticmethod
    def require_tier(*allowed_tiers: SubscriptionTier):
        """Decorator to require specific subscription tiers"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract user and db from kwargs (FastAPI dependency injection)
                user = None
                db = None
                
                for arg in args:
                    if isinstance(arg, User):
                        user = arg
                    elif isinstance(arg, Session):
                        db = arg
                
                for key, value in kwargs.items():
                    if isinstance(value, User):
                        user = value
                    elif isinstance(value, Session):
                        db = value
                
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if not db:
                    db = next(get_db())
                
                tier = get_user_tier(db, user.id)
                
                if tier not in allowed_tiers:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"This feature requires one of these tiers: {', '.join([t.value for t in allowed_tiers])}. Your current tier: {tier.value}"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def check_limit(limit_type: str, count: int = 1, track: bool = True):
        """Decorator to check usage limits before executing function"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract user and db from kwargs (FastAPI dependency injection)
                user = None
                db = None
                
                for arg in args:
                    if isinstance(arg, User):
                        user = arg
                    elif isinstance(arg, Session):
                        db = arg
                
                for key, value in kwargs.items():
                    if isinstance(value, User):
                        user = value
                    elif isinstance(value, Session):
                        db = value
                
                if not db:
                    db = next(get_db())
                
                if user:
                    # Check limit for authenticated user
                    is_allowed, current_usage, limit = check_user_limit(
                        db, user.id, limit_type, count
                    )
                    
                    if not is_allowed:
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=f"Usage limit exceeded. Current usage: {current_usage}/{limit}. Upgrade to Pro for higher limits."
                        )
                    
                    # Track usage
                    if track:
                        track_usage(db, user.id, limit_type)
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator

def check_historical_data_access(request: Request, db: Session, user: Optional[User]) -> bool:
    """Check if user can access historical data beyond free tier limit"""
    if not user:
        return False
    
    tier = get_user_tier(db, user.id)
    historical_days = get_tier_limit(tier, "historical_days")
    
    # Unlimited or None means all-time access
    if historical_days is None:
        return True
    
    # Free tier: 7 days
    return historical_days >= 7

def check_export_access(request: Request, db: Session, user: Optional[User]) -> bool:
    """Check if user can export data"""
    if not user:
        return False
    
    tier = get_user_tier(db, user.id)
    exports_limit = get_tier_limit(tier, "exports_per_month")
    
    # None means unlimited
    return exports_limit is None

def check_api_access(request: Request, db: Session, user: Optional[User]) -> bool:
    """Check if user can access API"""
    if not user:
        return False
    
    tier = get_user_tier(db, user.id)
    # Only Pro and above can access API
    return tier in [SubscriptionTier.PRO, SubscriptionTier.TEAM, SubscriptionTier.ENTERPRISE]

