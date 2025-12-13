"""Stripe subscription management"""
import os
import stripe
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database.models import User, Subscription, SubscriptionTier, SubscriptionStatus

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# Stripe price IDs - set these in your Stripe dashboard
STRIPE_PRICE_IDS = {
    SubscriptionTier.PRO: {
        "month": os.getenv("STRIPE_PRO_MONTHLY_PRICE_ID", ""),
        "year": os.getenv("STRIPE_PRO_YEARLY_PRICE_ID", ""),
    },
    SubscriptionTier.TEAM: {
        "month": os.getenv("STRIPE_TEAM_MONTHLY_PRICE_ID", ""),
        "year": os.getenv("STRIPE_TEAM_YEARLY_PRICE_ID", ""),
    },
}

def create_stripe_customer(email: str, name: Optional[str] = None) -> str:
    """Create a Stripe customer"""
    customer = stripe.Customer.create(
        email=email,
        name=name,
    )
    return customer.id

def create_stripe_subscription(
    customer_id: str,
    price_id: str,
    trial_days: int = 0
) -> stripe.Subscription:
    """Create a Stripe subscription"""
    subscription_params = {
        "customer": customer_id,
        "items": [{"price": price_id}],
    }
    
    if trial_days > 0:
        subscription_params["trial_period_days"] = trial_days
    
    subscription = stripe.Subscription.create(**subscription_params)
    return subscription

def cancel_stripe_subscription(subscription_id: str, cancel_immediately: bool = False):
    """Cancel a Stripe subscription"""
    if cancel_immediately:
        stripe.Subscription.delete(subscription_id)
    else:
        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )

def get_stripe_subscription(subscription_id: str) -> stripe.Subscription:
    """Get a Stripe subscription"""
    return stripe.Subscription.retrieve(subscription_id)

def update_stripe_subscription(subscription_id: str, new_price_id: str) -> stripe.Subscription:
    """Update subscription to a new price/tier"""
    subscription = stripe.Subscription.retrieve(subscription_id)
    
    # Update subscription
    updated = stripe.Subscription.modify(
        subscription_id,
        items=[{
            "id": subscription["items"]["data"][0].id,
            "price": new_price_id,
        }],
        proration_behavior="always_invoice",  # Prorate the change
    )
    
    return updated

def sync_subscription_from_stripe(
    db: Session,
    user: User,
    stripe_subscription: stripe.Subscription
) -> Subscription:
    """Sync subscription data from Stripe to database"""
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    
    # Determine tier from price ID
    price_id = stripe_subscription["items"]["data"][0].price.id
    tier = SubscriptionTier.FREE
    billing_cycle = "month"
    
    for t, prices in STRIPE_PRICE_IDS.items():
        if price_id in prices.values():
            tier = t
            billing_cycle = "month" if price_id == prices["month"] else "year"
            break
    
    # Map Stripe status to our status
    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "canceled": SubscriptionStatus.CANCELED,
        "past_due": SubscriptionStatus.PAST_DUE,
        "trialing": SubscriptionStatus.TRIALING,
        "incomplete": SubscriptionStatus.INCOMPLETE,
        "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED,
        "unpaid": SubscriptionStatus.UNPAID,
    }
    
    status = status_map.get(stripe_subscription.status, SubscriptionStatus.ACTIVE)
    
    if subscription:
        # Update existing subscription
        subscription.stripe_subscription_id = stripe_subscription.id
        subscription.stripe_price_id = price_id
        subscription.tier = tier
        subscription.status = status
        subscription.billing_cycle = billing_cycle
        subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
        subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
        subscription.cancel_at_period_end = stripe_subscription.cancel_at_period_end
        
        if stripe_subscription.canceled_at:
            subscription.canceled_at = datetime.fromtimestamp(stripe_subscription.canceled_at)
    else:
        # Create new subscription
        subscription = Subscription(
            user_id=user.id,
            stripe_customer_id=stripe_subscription.customer,
            stripe_subscription_id=stripe_subscription.id,
            stripe_price_id=price_id,
            tier=tier,
            status=status,
            billing_cycle=billing_cycle,
            current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
            current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
            cancel_at_period_end=stripe_subscription.cancel_at_period_end,
        )
        db.add(subscription)
    
    db.commit()
    db.refresh(subscription)
    return subscription

