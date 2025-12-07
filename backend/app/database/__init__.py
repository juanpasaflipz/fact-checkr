# Database package
from .models import (
    Base, Source, Claim, Topic, Entity, VerificationStatus,
    User, Subscription, UsageTracking,
    SubscriptionTier, SubscriptionStatus
)
from .connection import get_engine, SessionLocal, get_db

# Backwards compatibility alias
engine = get_engine

__all__ = [
    "Base",
    "Source",
    "Claim",
    "Topic",
    "Entity",
    "VerificationStatus",
    "User",
    "Subscription",
    "UsageTracking",
    "SubscriptionTier",
    "SubscriptionStatus",
    "engine",
    "SessionLocal",
    "get_db",
]
