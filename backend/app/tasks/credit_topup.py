"""
Monthly Credit Top-up Task

Adds monthly credit top-ups to Pro+ subscribers based on their tier.
Runs on the 1st of each month.
"""

from celery import shared_task
from app.database.connection import get_db
from app.database.models import UserBalance, Subscription, SubscriptionStatus, SubscriptionTier
from app.core.utils import get_user_tier, get_tier_limit
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.credit_topup.monthly_credit_topup")
def monthly_credit_topup():
    """
    Run monthly to add credits to Pro users.
    Executes on the 1st of each month.
    """
    db = next(get_db())
    
    try:
        # Get all active Pro+ subscriptions
        subscriptions = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.tier.in_([
                SubscriptionTier.PRO,
                SubscriptionTier.TEAM,
                SubscriptionTier.ENTERPRISE
            ])
        ).all()
        
        topup_count = 0
        total_credits_added = 0.0
        
        for subscription in subscriptions:
            try:
                tier = subscription.tier
                topup_amount = get_tier_limit(tier, "monthly_credit_topup")
                
                # Skip if no top-up for this tier or if it's None (Enterprise custom)
                if not topup_amount or topup_amount <= 0:
                    continue
                
                # Get or create user balance
                balance = db.query(UserBalance).filter(
                    UserBalance.user_id == subscription.user_id
                ).first()
                
                if not balance:
                    from app.core.utils import create_default_user_balance
                    balance = create_default_user_balance(db, subscription.user_id)
                
                # Add top-up credits
                balance.available_credits += topup_amount
                topup_count += 1
                total_credits_added += topup_amount
                
                logger.info(
                    f"Added {topup_amount} credits to user {subscription.user_id} "
                    f"(tier: {tier.value})"
                )
                
            except Exception as e:
                logger.error(
                    f"Error processing top-up for user {subscription.user_id}: {str(e)}"
                )
                continue
        
        db.commit()
        
        logger.info(
            f"Monthly credit top-up completed: {topup_count} users, "
            f"{total_credits_added} total credits added"
        )
        
        return {
            "success": True,
            "users_processed": topup_count,
            "total_credits_added": total_credits_added
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in monthly credit top-up task: {str(e)}")
        raise
    finally:
        db.close()

