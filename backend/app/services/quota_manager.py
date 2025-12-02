"""
Quota Manager for Twitter API

Tracks and manages Twitter API quota usage to ensure we don't exceed monthly limits.
Basic tier: 15,000 posts/month
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.connection import SessionLocal
from app.database.models import Source
import logging
import os

logger = logging.getLogger(__name__)

# Twitter Basic tier limits
TWITTER_MONTHLY_QUOTA = 15000  # 15,000 posts/month
TWITTER_DAILY_QUOTA = TWITTER_MONTHLY_QUOTA / 30  # ~500 posts/day
TWITTER_RUNS_PER_DAY = 4  # 6 AM, 12 PM, 6 PM, midnight
TWITTER_POSTS_PER_RUN = int(TWITTER_DAILY_QUOTA / TWITTER_RUNS_PER_DAY)  # ~125 posts per run

# Safety margin (use 90% of quota to leave buffer)
SAFETY_MARGIN = 0.9
SAFE_POSTS_PER_RUN = int(TWITTER_POSTS_PER_RUN * SAFETY_MARGIN)  # ~112 posts per run


class QuotaManager:
    """Manages Twitter API quota usage"""
    
    def __init__(self):
        self.monthly_quota = TWITTER_MONTHLY_QUOTA
        self.posts_per_run = SAFE_POSTS_PER_RUN
    
    def get_current_month_usage(self, db: Session = None) -> int:
        """Get number of Twitter posts collected this month"""
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False
        
        try:
            # Get first day of current month
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            
            # Count Twitter/X sources from this month
            count = db.query(func.count(Source.id)).filter(
                Source.platform == "X (Twitter)",
                Source.timestamp >= month_start
            ).scalar() or 0
            
            return count
        except Exception as e:
            logger.error(f"Error getting quota usage: {e}")
            return 0
        finally:
            if should_close:
                db.close()
    
    def get_remaining_quota(self, db: Session = None) -> int:
        """Get remaining quota for current month"""
        used = self.get_current_month_usage(db)
        remaining = max(0, self.monthly_quota - used)
        return remaining
    
    def get_quota_percentage(self, db: Session = None) -> float:
        """Get quota usage as percentage"""
        used = self.get_current_month_usage(db)
        return (used / self.monthly_quota) * 100
    
    def can_fetch_posts(self, requested_count: int, db: Session = None) -> tuple[bool, int]:
        """
        Check if we can fetch the requested number of posts.
        
        Returns:
            (can_fetch: bool, allowed_count: int)
        """
        remaining = self.get_remaining_quota(db)
        
        if remaining <= 0:
            logger.warning(f"Twitter quota exhausted. Remaining: {remaining}")
            return False, 0
        
        # Allow up to posts_per_run, but not more than remaining
        allowed = min(requested_count, self.posts_per_run, remaining)
        
        if allowed < requested_count:
            logger.info(
                f"Quota limit: requested {requested_count}, allowed {allowed} "
                f"(remaining: {remaining}, per-run limit: {self.posts_per_run})"
            )
        
        return True, allowed
    
    def get_quota_status(self, db: Session = None) -> dict:
        """Get detailed quota status"""
        used = self.get_current_month_usage(db)
        remaining = self.get_remaining_quota(db)
        percentage = self.get_quota_percentage(db)
        
        return {
            "monthly_quota": self.monthly_quota,
            "used": used,
            "remaining": remaining,
            "percentage_used": round(percentage, 2),
            "posts_per_run": self.posts_per_run,
            "runs_per_day": TWITTER_RUNS_PER_DAY,
            "daily_quota": TWITTER_DAILY_QUOTA,
            "status": "ok" if percentage < 80 else "warning" if percentage < 95 else "critical"
        }


# Global instance
quota_manager = QuotaManager()

