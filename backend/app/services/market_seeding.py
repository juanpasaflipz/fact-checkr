"""
Market Seeding Service

Uses Market Intelligence Agent to seed new markets with intelligent initial probabilities.
"""
from app.agents.market_intelligence_agent import MarketIntelligenceAgent
from app.services.markets import buy_yes, buy_no, yes_probability
from app.database.models import Market, MarketStatus, MarketTrade
from sqlalchemy.orm import Session
from typing import Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)


def get_or_create_system_user_id(db: Session) -> Optional[int]:
    """
    Get or create a system user for agent trades.
    Returns None if system user doesn't exist and can't be created.
    """
    from app.database.models import User
    
    # Look for system user (email: system@factcheckr.mx)
    system_user = db.query(User).filter(User.email == "system@factcheckr.mx").first()
    
    if system_user:
        return system_user.id
    
    # Try to create system user (only if it doesn't exist)
    try:
        from app.utils import get_password_hash
        import secrets
        
        # Use same approach as OAuth user creation - short token under 72 bytes
        placeholder_password = secrets.token_urlsafe(16)  # ~22 chars, well under 72 bytes
        hashed_password = get_password_hash(placeholder_password)
        
        system_user = User(
            email="system@factcheckr.mx",
            username="system_agent",
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            is_admin=False
        )
        db.add(system_user)
        db.commit()
        db.refresh(system_user)
        logger.info("Created system user for agent trades")
        return system_user.id
    except Exception as e:
        logger.warning(f"Could not create system user: {e}")
        db.rollback()
        # Try to get existing user even if creation failed
        system_user = db.query(User).filter(User.email == "system@factcheckr.mx").first()
        if system_user:
            logger.info("Found existing system user")
            return system_user.id
        # If all else fails, try to find any admin user as fallback
        admin_user = db.query(User).filter(User.is_admin == True).first()
        if admin_user:
            logger.warning("Using admin user as fallback for agent trades")
            return admin_user.id
        # Last resort: use first user in database
        first_user = db.query(User).first()
        if first_user:
            logger.warning(f"Using first user (ID: {first_user.id}) as fallback for agent trades")
            return first_user.id
        return None


def _should_use_premium_model(market: Market, db: Session) -> bool:
    """
    Determine if market should use premium model (Sonnet) instead of Haiku.
    
    Criteria:
    - High-value categories (politics, economy)
    - Markets with existing trades (re-assessment)
    - Markets linked to verified claims
    """
    # High-value categories
    premium_categories = ["politics", "economy", "institutions"]
    if market.category in premium_categories:
        return True
    
    # Markets with existing activity
    trade_count = db.query(MarketTrade).filter(
        MarketTrade.market_id == market.id
    ).count()
    if trade_count > 5:
        return True
    
    # Markets linked to verified claims
    if market.claim_id:
        from app.database.models import Claim, VerificationStatus
        claim = db.query(Claim).filter(Claim.id == market.claim_id).first()
        if claim and claim.status in [VerificationStatus.VERIFIED, VerificationStatus.DEBUNKED]:
            return True
    
    return False


async def seed_market_with_agent_assessment(
    market: Market,
    db: Session,
    seed_amount: Optional[float] = None,
    min_confidence: float = 0.4,
    force_model: Optional[str] = None
) -> Dict:
    """
    Use Market Intelligence Agent to assess and seed a market.
    
    This places an initial trade based on agent analysis to set
    a more accurate starting probability than 50/50.
    
    Args:
        market: Market to seed
        db: Database session
        seed_amount: Override recommended seed amount
        min_confidence: Minimum confidence to seed (default 0.4)
        force_model: Override model selection ("haiku" or "sonnet")
    
    Returns:
        Dict with seeding result
    """
    # Determine which model to use
    if force_model:
        model_preference = force_model
    elif _should_use_premium_model(market, db):
        model_preference = "sonnet"
        logger.debug(f"Market {market.id}: Using premium model (Sonnet) for assessment")
    else:
        model_preference = None  # Use default (Haiku)
    
    agent = MarketIntelligenceAgent(model_preference=model_preference)
    
    # Get agent assessment
    assessment = await agent.assess_market_probability(market, db)
    
    yes_prob = assessment["yes_probability"]
    confidence = assessment["confidence"]
    recommended_seed = seed_amount or assessment["recommended_seed_amount"]
    model_used = assessment.get("model_used", "unknown")
    
    # Only seed if confidence is above threshold
    if confidence < min_confidence:
        logger.info(
            f"Market {market.id}: Low confidence ({confidence:.2f}), skipping seed. "
            f"Recommended: {recommended_seed:.1f} credits (model: {model_used})"
        )
        return {
            "seeded": False,
            "reason": "low_confidence",
            "confidence": confidence,
            "model_used": model_used,
            "assessment": assessment
        }
    
    # Check if market already has trades (don't re-seed)
    existing_trades = db.query(MarketTrade).filter(
        MarketTrade.market_id == market.id
    ).count()
    
    if existing_trades > 0:
        logger.info(f"Market {market.id}: Already has {existing_trades} trades, skipping seed")
        return {
            "seeded": False,
            "reason": "already_has_trades",
            "model_used": model_used,
            "assessment": assessment
        }
    
    # Determine which side to seed
    # If yes_prob > 0.5, buy YES to move probability up
    # If yes_prob < 0.5, buy NO to move probability down
    outcome = "yes" if yes_prob > 0.5 else "no"
    
    # Calculate target probability shift
    # We want to move from 50% to approximately the assessed probability
    # But don't move too aggressively (max 20% shift from seed)
    target_prob = yes_prob
    max_shift = 0.20  # Don't move more than 20% from initial 50%
    
    if target_prob > 0.5:
        target_prob = min(0.5 + max_shift, target_prob)
    else:
        target_prob = max(0.5 - max_shift, target_prob)
    
    try:
        # Place seed trade
        if outcome == "yes":
            shares, updated_market = buy_yes(market, recommended_seed, db)
        else:
            shares, updated_market = buy_no(market, recommended_seed, db)
        
        # Get system user for agent trades
        system_user_id = get_or_create_system_user_id(db)
        
        if not system_user_id:
            raise ValueError("Could not create or find system user for agent trades")
        
        # Create trade record (marked as agent trade)
        trade = MarketTrade(
            market_id=market.id,
            user_id=system_user_id,  # System user for agent trades
            outcome=outcome,
            shares=shares,
            price=recommended_seed / shares if shares > 0 else 0.0,
            cost=recommended_seed
        )
        db.add(trade)
        db.commit()
        db.refresh(updated_market)
        
        # Calculate new probability
        new_prob = yes_probability(updated_market)
        
        logger.info(
            f"Market {market.id} seeded: {outcome.upper()} "
            f"({yes_prob:.1%} assessed → {new_prob:.1%} actual) "
            f"with {recommended_seed:.1f} credits (model: {model_used})"
        )
        
        return {
            "seeded": True,
            "outcome": outcome,
            "amount": recommended_seed,
            "shares": shares,
            "initial_probability": 0.5,
            "new_probability": new_prob,
            "assessed_probability": yes_prob,
            "confidence": confidence,
            "model_used": model_used,
            "assessment": assessment
        }
        
    except Exception as e:
        logger.error(f"Failed to seed market {market.id}: {e}")
        db.rollback()
        return {
            "seeded": False,
            "reason": "error",
            "error": str(e),
            "model_used": model_used,
            "assessment": assessment
        }
