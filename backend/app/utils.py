"""Utility functions for authentication, subscriptions, and usage tracking"""
import bcrypt
import os
import re
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.database.models import User, Subscription, SubscriptionTier, SubscriptionStatus, UsageTracking, UserBalance


def get_redis_url() -> str:
    """
    Get Redis URL, preferring private endpoints to avoid egress fees on Railway.
    
    Priority:
    1. Check if REDIS_PUBLIC_URL is set (warning: incurs egress fees) and switch to private
    2. Detect if REDIS_URL uses public Railway endpoint and switch to private
    3. Use REDIS_URL as-is if it's already private or not Railway
    4. Fallback to localhost for local development
    
    Returns:
        Redis connection URL string
    """
    # Check for REDIS_PUBLIC_URL first (this is what Railway warns about)
    redis_public_url = os.getenv("REDIS_PUBLIC_URL")
    if redis_public_url:
        # REDIS_PUBLIC_URL uses public endpoint - switch to private
        railway_private_domain = os.getenv("RAILWAY_PRIVATE_DOMAIN")
        if railway_private_domain:
            # Extract port and database from public URL
            port_match = re.search(r':(\d+)', redis_public_url)
            db_match = re.search(r'/(\d+)$', redis_public_url)
            
            port = port_match.group(1) if port_match else "6379"
            db = db_match.group(1) if db_match else "0"
            
            # Use Railway's private internal domain (no egress fees)
            return f"redis://redis.railway.internal:{port}/{db}"
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Check if we're on Railway and using a public endpoint
    railway_private_domain = os.getenv("RAILWAY_PRIVATE_DOMAIN")
    railway_tcp_proxy = os.getenv("RAILWAY_TCP_PROXY_DOMAIN")
    
    # If on Railway and REDIS_URL contains public endpoint, switch to private
    if railway_private_domain and railway_tcp_proxy:
        # Check if current REDIS_URL uses the public TCP proxy domain
        if railway_tcp_proxy in redis_url or "railway.app" in redis_url:
            # Switch to private endpoint: redis.railway.internal
            # Extract port and database from existing URL if present
            port_match = re.search(r':(\d+)', redis_url)
            db_match = re.search(r'/(\d+)$', redis_url)
            
            port = port_match.group(1) if port_match else "6379"
            db = db_match.group(1) if db_match else "0"
            
            # Use Railway's private internal domain
            return f"redis://redis.railway.internal:{port}/{db}"
    
    # Use REDIS_URL as-is (already private, local, or custom config)
    return redis_url


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    # bcrypt has a 72-byte limit - truncate if needed
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    # bcrypt has a 72-byte limit - truncate if needed
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

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
    # Check if subscription already exists
    existing_subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if existing_subscription:
        return existing_subscription

    subscription = Subscription(
        user_id=user_id,
        tier=SubscriptionTier.FREE,
        status=SubscriptionStatus.ACTIVE
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription

def create_default_user_balance(db: Session, user_id: int) -> UserBalance:
    """Create a default user balance with 1000 demo credits for a new user"""
    # Check if balance already exists
    existing_balance = db.query(UserBalance).filter(UserBalance.user_id == user_id).first()
    if existing_balance:
        return existing_balance
    
    balance = UserBalance(
        user_id=user_id,
        available_credits=1000.0,
        locked_credits=0.0
    )
    db.add(balance)
    db.commit()
    db.refresh(balance)
    return balance

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
        "market_trades_per_day": 10,
        "market_creation": False,
        "market_proposals_per_month": 2,
        "market_analytics": False,
        "market_exports": False,
        "market_notifications": False,
        "monthly_credit_topup": 0,
    },
    SubscriptionTier.PRO: {
        "verifications_per_month": None,  # Unlimited
        "api_calls_per_day": 10000,
        "search_queries_per_day": None,  # Unlimited
        "exports_per_month": None,  # Unlimited
        "historical_days": None,  # All-time
        "alerts": 5,
        "collections": 10,
        "market_trades_per_day": None,  # Unlimited
        "market_creation": True,
        "market_proposals_per_month": 10,
        "market_analytics": True,
        "market_exports": True,
        "market_notifications": True,
        "monthly_credit_topup": 500,
    },
    SubscriptionTier.TEAM: {
        "verifications_per_month": None,  # Unlimited
        "api_calls_per_day": 50000,
        "search_queries_per_day": None,  # Unlimited
        "exports_per_month": None,  # Unlimited
        "historical_days": None,  # All-time
        "alerts": 20,
        "collections": None,  # Unlimited
        "market_trades_per_day": None,  # Unlimited
        "market_creation": True,
        "market_proposals_per_month": 50,
        "market_analytics": True,
        "market_exports": True,
        "market_notifications": True,
        "monthly_credit_topup": 2000,
    },
    SubscriptionTier.ENTERPRISE: {
        "verifications_per_month": None,  # Unlimited
        "api_calls_per_day": None,  # Unlimited
        "search_queries_per_day": None,  # Unlimited
        "exports_per_month": None,  # Unlimited
        "historical_days": None,  # All-time
        "alerts": None,  # Unlimited
        "collections": None,  # Unlimited
        "market_trades_per_day": None,  # Unlimited
        "market_creation": True,
        "market_proposals_per_month": None,  # Unlimited
        "market_analytics": True,
        "market_exports": True,
        "market_notifications": True,
        "monthly_credit_topup": None,  # Custom
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
        "market_trades_per_day": "market_trade",
        "market_proposals_per_month": "market_proposal",
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

