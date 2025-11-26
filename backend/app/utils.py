"""Utility functions for authentication, subscriptions, and usage tracking"""
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.database.models import User, Subscription, SubscriptionTier, UsageTracking

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_subscription(db: Session, user_id: int) -> Optional[Subscription]:
    """Get user's subscription"""
    return db.query(Subscription).filter(Subscription.user_id == user_id).first()

def get_user_tier(db: Session, user_id: int) -> SubscriptionTier:
    """Get user's subscription tier, defaulting to FREE"""
    subscription = get_user_subscription(db, user_id)
    if subscription and subscription.status.value == "active":
        return subscription.tier
    return SubscriptionTier.FREE

def create_default_subscription(db: Session, user_id: int) -> Subscription:
    """Create a default FREE subscription for a new user"""
    subscription = Subscription(
        user_id=user_id,
        tier=SubscriptionTier.FREE,
        status=SubscriptionStatus.ACTIVE
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription

# Tier limits configuration
TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "verifications_per_month": 10,
        "api_calls_per_day": 100,
        "search_queries_per_day": 50,
        "exports_per_month": 0,
        "historical_days": 7,
        "alerts": 0,
        "collections": 0,
    },
    SubscriptionTier.PRO: {
        "verifications_per_month": None,  # Unlimited
        "api_calls_per_day": 10000,
        "search_queries_per_day": None,  # Unlimited
        "exports_per_month": None,  # Unlimited
        "historical_days": None,  # All-time
        "alerts": 5,
        "collections": 10,
    },
    SubscriptionTier.TEAM: {
        "verifications_per_month": None,  # Unlimited
        "api_calls_per_day": 50000,
        "search_queries_per_day": None,  # Unlimited
        "exports_per_month": None,  # Unlimited
        "historical_days": None,  # All-time
        "alerts": 20,
        "collections": None,  # Unlimited
    },
    SubscriptionTier.ENTERPRISE: {
        "verifications_per_month": None,  # Unlimited
        "api_calls_per_day": None,  # Unlimited
        "search_queries_per_day": None,  # Unlimited
        "exports_per_month": None,  # Unlimited
        "historical_days": None,  # All-time
        "alerts": None,  # Unlimited
        "collections": None,  # Unlimited
    },
}

def get_tier_limit(tier: SubscriptionTier, limit_type: str):
    """Get a limit for a specific tier"""
    return TIER_LIMITS.get(tier, TIER_LIMITS[SubscriptionTier.FREE]).get(limit_type, 0)

def is_limit_unlimited(tier: SubscriptionTier, limit_type: str) -> bool:
    """Check if a limit is unlimited for a tier"""
    limit = get_tier_limit(tier, limit_type)
    return limit is None

def check_user_limit(db: Session, user_id: int, limit_type: str, count: int = 1) -> tuple[bool, Optional[int], Optional[int]]:
    """
    Check if user can perform an action based on their tier limits.
    Returns: (is_allowed, current_usage, limit)
    """
    tier = get_user_tier(db, user_id)
    limit = get_tier_limit(tier, limit_type)
    
    # Unlimited
    if limit is None:
        return (True, None, None)
    
    # Get current usage
    current_usage = get_current_usage(db, user_id, limit_type)
    
    # Check if adding count would exceed limit
    if current_usage + count > limit:
        return (False, current_usage, limit)
    
    return (True, current_usage, limit)

def get_current_usage(db: Session, user_id: int, usage_type: str) -> int:
    """Get current usage count for a user and usage type"""
    now = datetime.utcnow()
    
    if "per_month" in usage_type:
        # Monthly limit (e.g., verifications_per_month)
        # Get subscription to find billing period start
        subscription = get_user_subscription(db, user_id)
        if subscription and subscription.current_period_start:
            period_start = subscription.current_period_start
        else:
            # Default to start of current month
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = now
        
    elif "per_day" in usage_type:
        # Daily limit (e.g., api_calls_per_day)
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = now
    
    else:
        # Default to daily
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = now
    
    # Map usage_type to database usage_type
    type_mapping = {
        "verifications_per_month": "verification",
        "api_calls_per_day": "api_call",
        "search_queries_per_day": "search",
        "exports_per_month": "export",
    }
    
    db_usage_type = type_mapping.get(usage_type, usage_type)
    
    # Count usage records in the period
    usage_count = db.query(UsageTracking).filter(
        UsageTracking.user_id == user_id,
        UsageTracking.usage_type == db_usage_type,
        UsageTracking.date >= period_start,
        UsageTracking.date <= period_end
    ).count()
    
    return usage_count

def track_usage(db: Session, user_id: int, usage_type: str, metadata: Optional[dict] = None):
    """Track a usage event for a user"""
    now = datetime.utcnow()
    
    # Get subscription for period tracking
    subscription = get_user_subscription(db, user_id)
    
    usage = UsageTracking(
        user_id=user_id,
        usage_type=usage_type,
        count=1,
        period_start=subscription.current_period_start if subscription and subscription.current_period_start else now.replace(day=1),
        period_end=subscription.current_period_end if subscription and subscription.current_period_end else now.replace(day=1) + timedelta(days=30),
        date=now,
        usage_metadata=metadata or {}
    )
    
    db.add(usage)
    db.commit()
    
    return usage

