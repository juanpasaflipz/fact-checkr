"""Subscription management routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
import os
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.core.config import settings
from app.database.connection import get_db
from app.database.models import User, Subscription, SubscriptionTier, SubscriptionStatus
from app.core.auth import get_current_user
from app.services.subscription_service import (
    create_stripe_customer,
    create_stripe_subscription,
    cancel_stripe_subscription,
    update_stripe_subscription,
    sync_subscription_from_stripe,
    STRIPE_PRICE_IDS,
)
from app.core.utils import get_user_subscription, get_user_tier
import stripe

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

class SubscriptionResponse(BaseModel):
    id: int
    tier: str
    status: str
    billing_cycle: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    created_at: datetime

class CreateSubscriptionRequest(BaseModel):
    tier: str  # "pro" or "team"
    billing_cycle: str  # "month" or "year"
    trial_days: int = 0

class SubscriptionInfoResponse(BaseModel):
    subscription: Optional[SubscriptionResponse] = None
    tier: str
    limits: dict

@router.get("/info", response_model=SubscriptionInfoResponse)
async def get_subscription_info(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription information"""
    subscription = get_user_subscription(db, user.id)
    tier = get_user_tier(db, user.id)
    
    # Get tier limits
    from app.utils import TIER_LIMITS
    limits = TIER_LIMITS.get(tier, TIER_LIMITS[SubscriptionTier.FREE])
    
    subscription_response = None
    if subscription:
        subscription_response = SubscriptionResponse(
            id=subscription.id,
            tier=subscription.tier.value,
            status=subscription.status.value,
            billing_cycle=subscription.billing_cycle,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            created_at=subscription.created_at
        )
    
    return SubscriptionInfoResponse(
        subscription=subscription_response,
        tier=tier.value,
        limits=limits
    )

@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CreateSubscriptionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session for subscription"""
    # Validate tier
    try:
        tier = SubscriptionTier[request.tier.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier. Must be one of: {', '.join([t.value for t in SubscriptionTier if t != SubscriptionTier.FREE])}"
        )
    
    if tier == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot subscribe to free tier"
        )
    
    # Validate billing cycle
    if request.billing_cycle not in ["month", "year"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Billing cycle must be 'month' or 'year'"
        )
    
    # Get price ID
    price_id = STRIPE_PRICE_IDS.get(tier, {}).get(request.billing_cycle)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Price ID not configured for {tier.value} {request.billing_cycle}"
        )
    
    # Get or create Stripe customer
    subscription = get_user_subscription(db, user.id)
    if subscription and subscription.stripe_customer_id:
        customer_id = subscription.stripe_customer_id
    else:
        customer_id = create_stripe_customer(user.email, user.full_name)
        if subscription:
            subscription.stripe_customer_id = customer_id
            db.commit()
    
    # Create checkout session
    try:
        frontend_url = settings.get_frontend_url()
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            locale="es",  # Spanish locale for checkout page
            success_url=f"{frontend_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend_url}/subscription/cancel",
            metadata={
                "user_id": str(user.id),
                "tier": tier.value,
            },
            subscription_data={
                "trial_period_days": request.trial_days if request.trial_days > 0 else None,
            } if request.trial_days > 0 else {},
        )
        
        return {"checkout_url": checkout_session.url, "session_id": checkout_session.id}
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe error: {str(e)}"
        )

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    import json
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    try:
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            # Subscription is created, sync it
            if session.mode == "subscription":
                subscription_id = session.subscription
                stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                user_id = int(session.metadata.get("user_id"))
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    sync_subscription_from_stripe(db, user, stripe_subscription)
        
        elif event["type"] in ["customer.subscription.updated", "customer.subscription.deleted"]:
            stripe_subscription = event["data"]["object"]
            # Find subscription in database
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_subscription.id
            ).first()
            if subscription:
                user = subscription.user
                sync_subscription_from_stripe(db, user, stripe_subscription)
        
        return {"status": "success"}
    except Exception as e:
        # Log error but return 200 to Stripe (they'll retry)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")
