"""Prediction markets routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime
import re

from app.database.connection import get_db
from app.database.models import (
    Market, MarketStatus, MarketTrade, UserBalance, User, Claim,
    MarketProposal, UserMarketStats, SubscriptionTier, MarketNotification
)
from app.auth import get_current_user, get_admin_user, get_optional_user
from app.middleware import TierChecker
from app.utils import (
    get_user_tier, check_user_limit, track_usage, get_tier_limit
)
from app.models import (
    MarketSummary,
    MarketDetail,
    TradeRequest,
    TradeResponse,
    UserBalanceResponse,
    CreateMarketRequest,
    ResolveMarketRequest,
    MarketProposalResponse,
    MarketAnalyticsResponse,
    UserPerformanceResponse,
    LeaderboardEntry,
    MarketNotificationResponse,
    MarketInsightsResponse,
)
from app.services.markets import (
    yes_probability,
    no_probability,
    buy_yes,
    buy_no,
    calculate_volume,
)

router = APIRouter(prefix="/markets", tags=["markets"])


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


def get_or_create_user_balance(db: Session, user_id: int) -> UserBalance:
    """Get user balance or create one with default credits if missing"""
    balance = db.query(UserBalance).filter(UserBalance.user_id == user_id).first()
    if not balance:
        from app.utils import create_default_user_balance
        balance = create_default_user_balance(db, user_id)
    return balance


def get_or_create_user_market_stats(db: Session, user_id: int) -> UserMarketStats:
    """Get user market stats or create one if missing"""
    stats = db.query(UserMarketStats).filter(UserMarketStats.user_id == user_id).first()
    if not stats:
        stats = UserMarketStats(user_id=user_id)
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


def update_user_market_stats(db: Session, user_id: int, amount: float, outcome: str):
    """Update user market stats after a trade"""
    stats = get_or_create_user_market_stats(db, user_id)
    stats.total_trades += 1
    stats.total_volume += amount
    stats.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(stats)


@router.get("", response_model=List[MarketSummary])
async def list_markets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    claim_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    for_you: Optional[bool] = Query(None),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """List all open markets (public read-only, or personalized if authenticated)"""
    query = db.query(Market).filter(Market.status == MarketStatus.OPEN)
    
    if claim_id:
        query = query.filter(Market.claim_id == claim_id)
    
    if category:
        query = query.filter(Market.category == category)
    
    # Personalized feed: filter by user's preferred categories
    if for_you and user and user.preferred_categories:
        query = query.filter(Market.category.in_(user.preferred_categories))
    
    markets = query.order_by(desc(Market.created_at)).offset(skip).limit(limit).all()
    
    result = []
    for market in markets:
        yes_prob = yes_probability(market)
        no_prob = no_probability(market)
        volume = calculate_volume(market, db)
        
        result.append(MarketSummary(
            id=market.id,
            slug=market.slug,
            question=market.question,
            yes_probability=yes_prob,
            no_probability=no_prob,
            volume=volume,
            closes_at=market.closes_at,
            status=market.status.value,
            claim_id=market.claim_id,
            category=market.category
        ))
    
    return result


@router.get("/{market_id}", response_model=MarketDetail)
async def get_market(
    market_id: int,
    db: Session = Depends(get_db)
):
    """Get market details (public read-only)"""
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    yes_prob = yes_probability(market)
    no_prob = no_probability(market)
    volume = calculate_volume(market, db)
    
    return MarketDetail(
        id=market.id,
        slug=market.slug,
        question=market.question,
        description=market.description,
        yes_probability=yes_prob,
        no_probability=no_prob,
        yes_liquidity=market.yes_liquidity,
        no_liquidity=market.no_liquidity,
        volume=volume,
        created_at=market.created_at,
        closes_at=market.closes_at,
        resolved_at=market.resolved_at,
        status=market.status.value,
        winning_outcome=market.winning_outcome,
        resolution_source=market.resolution_source,
        resolution_criteria=market.resolution_criteria,
        claim_id=market.claim_id,
        category=market.category
    )


@router.get("/balance", response_model=UserBalanceResponse)
async def get_user_balance(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's credit balance"""
    balance = get_or_create_user_balance(db, user.id)
    return UserBalanceResponse(
        available_credits=balance.available_credits,
        locked_credits=balance.locked_credits
    )


@router.post("/{market_id}/trade", response_model=TradeResponse)
@TierChecker.check_limit("market_trades_per_day", count=1, track=True)
async def trade_market(
    market_id: int,
    trade_request: TradeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Place a trade on a market (Free: 10/day, Pro: Unlimited)"""
    # Get market
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Validate market is open
    if market.status != MarketStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Market is {market.status.value} and cannot be traded"
        )
    
    # Validate outcome
    if trade_request.outcome not in ["yes", "no"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Outcome must be 'yes' or 'no'"
        )
    
    # Validate amount
    if trade_request.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    # Get user balance
    balance = get_or_create_user_balance(db, user.id)
    
    # Check sufficient credits
    if balance.available_credits < trade_request.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient credits. Available: {balance.available_credits}, Required: {trade_request.amount}"
        )
    
    try:
        # Execute trade via AMM
        if trade_request.outcome == "yes":
            shares, updated_market = buy_yes(market, trade_request.amount, db)
        else:
            shares, updated_market = buy_no(market, trade_request.amount, db)
        
        # Calculate average price
        avg_price = trade_request.amount / shares if shares > 0 else 0.0
        
        # Create trade record
        trade = MarketTrade(
            market_id=market.id,
            user_id=user.id,
            outcome=trade_request.outcome,
            shares=shares,
            price=avg_price,
            cost=trade_request.amount
        )
        db.add(trade)
        
        # Update user balance
        balance.available_credits -= trade_request.amount
        
        # Update user market stats
        update_user_market_stats(db, user.id, trade_request.amount, trade_request.outcome)
        
        db.commit()
        db.refresh(balance)
        db.refresh(updated_market)
        
        # Calculate updated probabilities
        yes_prob = yes_probability(updated_market)
        no_prob = no_probability(updated_market)
        volume = calculate_volume(updated_market, db)
        
        return TradeResponse(
            shares=shares,
            price=avg_price,
            cost=trade_request.amount,
            market=MarketSummary(
                id=updated_market.id,
                slug=updated_market.slug,
                question=updated_market.question,
                yes_probability=yes_prob,
                no_probability=no_prob,
                volume=volume,
                closes_at=updated_market.closes_at,
                status=updated_market.status.value,
                claim_id=updated_market.claim_id
            ),
            user_balance=balance.available_credits
        )
    
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trade failed: {str(e)}"
        )


@router.post("/create", response_model=MarketDetail)
@TierChecker.require_tier(SubscriptionTier.PRO, SubscriptionTier.TEAM, SubscriptionTier.ENTERPRISE)
async def create_market_pro(
    market_request: CreateMarketRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new market (Pro users only)"""
    # Validate claim_id if provided
    if market_request.claim_id:
        claim = db.query(Claim).filter(Claim.id == market_request.claim_id).first()
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim not found"
            )
    
    # Generate unique slug
    base_slug = slugify(market_request.question)
    slug = base_slug
    counter = 1
    while db.query(Market).filter(Market.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Create market
    market = Market(
        slug=slug,
        question=market_request.question,
        description=market_request.description,
        claim_id=market_request.claim_id,
        category=market_request.category,
        resolution_criteria=market_request.resolution_criteria,
        status=MarketStatus.OPEN,
        yes_liquidity=1000.0,
        no_liquidity=1000.0,
        closes_at=market_request.closes_at,
        created_by_user_id=user.id
    )
    
    db.add(market)
    db.commit()
    db.refresh(market)
    
    # Auto-seed with agent assessment (async, non-blocking)
    # Run in background task to avoid blocking response
    from app.tasks.market_intelligence import seed_new_markets
    seed_new_markets.delay()  # Celery task runs async
    
    # Return market detail
    yes_prob = yes_probability(market)
    no_prob = no_probability(market)
    volume = calculate_volume(market, db)
    
    return MarketDetail(
        id=market.id,
        slug=market.slug,
        question=market.question,
        description=market.description,
        yes_probability=yes_prob,
        no_probability=no_prob,
        yes_liquidity=market.yes_liquidity,
        no_liquidity=market.no_liquidity,
        volume=volume,
        created_at=market.created_at,
        closes_at=market.closes_at,
        resolved_at=market.resolved_at,
        status=market.status.value,
        winning_outcome=market.winning_outcome,
        resolution_source=market.resolution_source,
        resolution_criteria=market.resolution_criteria,
        claim_id=market.claim_id,
        category=market.category
    )


@router.post("/propose", response_model=MarketProposalResponse)
@TierChecker.check_limit("market_proposals_per_month", count=1, track=True)
async def propose_market(
    market_request: CreateMarketRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Propose a new market (requires admin approval)"""
    # Create proposal
    proposal = MarketProposal(
        user_id=user.id,
        question=market_request.question,
        description=market_request.description,
        category=market_request.category,
        resolution_criteria=market_request.resolution_criteria,
        status="pending"
    )
    
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    
    return MarketProposalResponse(
        id=proposal.id,
        user_id=proposal.user_id,
        question=proposal.question,
        description=proposal.description,
        category=proposal.category,
        resolution_criteria=proposal.resolution_criteria,
        status=proposal.status,
        created_at=proposal.created_at,
        reviewed_at=proposal.reviewed_at,
        reviewed_by=proposal.reviewed_by
    )


@router.post("/admin/markets", response_model=MarketDetail)
async def create_market(
    market_request: CreateMarketRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new market (admin only)"""
    # Validate claim_id if provided
    if market_request.claim_id:
        claim = db.query(Claim).filter(Claim.id == market_request.claim_id).first()
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim not found"
            )
    
    # Generate unique slug
    base_slug = slugify(market_request.question)
    slug = base_slug
    counter = 1
    while db.query(Market).filter(Market.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Create market
    market = Market(
        slug=slug,
        question=market_request.question,
        description=market_request.description,
        claim_id=market_request.claim_id,
        category=market_request.category,
        resolution_criteria=market_request.resolution_criteria,
        status=MarketStatus.OPEN,
        yes_liquidity=1000.0,
        no_liquidity=1000.0,
        closes_at=market_request.closes_at
    )
    
    db.add(market)
    db.commit()
    db.refresh(market)
    
    # Auto-seed with agent assessment (async, non-blocking)
    # Run in background task to avoid blocking response
    from app.tasks.market_intelligence import seed_new_markets
    seed_new_markets.delay()  # Celery task runs async
    
    # Return market detail
    yes_prob = yes_probability(market)
    no_prob = no_probability(market)
    volume = calculate_volume(market, db)
    
    return MarketDetail(
        id=market.id,
        slug=market.slug,
        question=market.question,
        description=market.description,
        yes_probability=yes_prob,
        no_probability=no_prob,
        yes_liquidity=market.yes_liquidity,
        no_liquidity=market.no_liquidity,
        volume=volume,
        created_at=market.created_at,
        closes_at=market.closes_at,
        resolved_at=market.resolved_at,
        status=market.status.value,
        winning_outcome=market.winning_outcome,
        resolution_source=market.resolution_source,
        resolution_criteria=market.resolution_criteria,
        claim_id=market.claim_id,
        category=market.category
    )


@router.post("/admin/markets/{market_id}/resolve", response_model=MarketDetail)
async def resolve_market(
    market_id: int,
    resolve_request: ResolveMarketRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Resolve a market and distribute payouts (admin only)"""
    # Get market
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Validate market is open
    if market.status != MarketStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Market is already {market.status.value}"
        )
    
    # Validate winning outcome
    if resolve_request.winning_outcome not in ["yes", "no"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Winning outcome must be 'yes' or 'no'"
        )
    
    try:
        # Mark market as resolved
        market.status = MarketStatus.RESOLVED
        market.winning_outcome = resolve_request.winning_outcome
        market.resolved_at = datetime.utcnow()
        market.resolution_source = resolve_request.resolution_source
        
        # Calculate payouts for all users
        # Get all trades for this market
        trades = db.query(MarketTrade).filter(MarketTrade.market_id == market.id).all()
        
        # Calculate net position per user
        user_positions = {}
        for trade in trades:
            if trade.user_id not in user_positions:
                user_positions[trade.user_id] = {"yes": 0.0, "no": 0.0}
            
            if trade.outcome == "yes":
                user_positions[trade.user_id]["yes"] += trade.shares
            else:
                user_positions[trade.user_id]["no"] += trade.shares
        
        # Distribute payouts and update stats
        from app.services.market_analytics import update_user_stats_on_resolution
        
        for user_id, positions in user_positions.items():
            balance = get_or_create_user_balance(db, user_id)
            
            # Calculate winning shares
            winning_shares = positions[resolve_request.winning_outcome]
            
            if winning_shares > 0:
                # Each winning share pays 1 credit
                payout = winning_shares
                balance.available_credits += payout
        
        # Update user market stats after resolution
        update_user_stats_on_resolution(db, market.id, resolve_request.winning_outcome)
        
        # Send resolution notifications
        from app.tasks.market_notifications import notify_market_resolution
        notify_market_resolution.delay(market.id)
        
        db.commit()
        db.refresh(market)
        
        # Return resolved market detail
        yes_prob = yes_probability(market)
        no_prob = no_probability(market)
        volume = calculate_volume(market, db)
        
        return MarketDetail(
            id=market.id,
            slug=market.slug,
            question=market.question,
            description=market.description,
            yes_probability=yes_prob,
            no_probability=no_prob,
            yes_liquidity=market.yes_liquidity,
            no_liquidity=market.no_liquidity,
            volume=volume,
            created_at=market.created_at,
            closes_at=market.closes_at,
            resolved_at=market.resolved_at,
            status=market.status.value,
            winning_outcome=market.winning_outcome,
            resolution_source=market.resolution_source,
            resolution_criteria=market.resolution_criteria,
            claim_id=market.claim_id,
            category=market.category
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve market: {str(e)}"
        )


@router.get("/{market_id}/analytics", response_model=MarketAnalyticsResponse)
@TierChecker.require_tier(SubscriptionTier.PRO, SubscriptionTier.TEAM, SubscriptionTier.ENTERPRISE)
async def get_market_analytics(
    market_id: int,
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get advanced analytics for a market (Pro only)"""
    from app.services.market_analytics import get_market_history, get_category_trends
    
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    history = get_market_history(market_id, days, db)
    category_trends = None
    if market.category:
        category_trends = get_category_trends(market.category, days, db)
    
    return MarketAnalyticsResponse(
        market_id=market_id,
        history=history,
        category_trends=category_trends,
        current_probability={
            "yes": yes_probability(market),
            "no": no_probability(market)
        }
    )


@router.get("/my-performance", response_model=UserPerformanceResponse)
@TierChecker.require_tier(SubscriptionTier.PRO, SubscriptionTier.TEAM, SubscriptionTier.ENTERPRISE)
async def get_my_performance(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's market performance metrics (Pro only)"""
    from app.services.market_analytics import get_user_performance
    
    performance = get_user_performance(user.id, db)
    return UserPerformanceResponse(
        total_trades=performance["total_trades"],
        winning_trades=performance["winning_trades"],
        losing_trades=performance["losing_trades"],
        accuracy_rate=performance["accuracy_rate"],
        total_volume=performance["total_volume"],
        credits_earned=performance["credits_earned"],
        rank=performance["rank"]
    )


@router.get("/proposals", response_model=List[MarketProposalResponse])
async def get_my_proposals(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's market proposals"""
    proposals = db.query(MarketProposal).filter(
        MarketProposal.user_id == user.id
    ).order_by(desc(MarketProposal.created_at)).all()
    
    return [
        MarketProposalResponse(
            id=p.id,
            user_id=p.user_id,
            question=p.question,
            description=p.description,
            category=p.category,
            resolution_criteria=p.resolution_criteria,
            status=p.status,
            created_at=p.created_at,
            reviewed_at=p.reviewed_at,
            reviewed_by=p.reviewed_by
        )
        for p in proposals
    ]


@router.get("/admin/proposals", response_model=List[MarketProposalResponse])
async def list_proposals(
    status: Optional[str] = Query(None),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all market proposals (admin only)"""
    query = db.query(MarketProposal)
    
    if status:
        query = query.filter(MarketProposal.status == status)
    else:
        query = query.filter(MarketProposal.status == "pending")
    
    proposals = query.order_by(desc(MarketProposal.created_at)).all()
    
    return [
        MarketProposalResponse(
            id=p.id,
            user_id=p.user_id,
            question=p.question,
            description=p.description,
            category=p.category,
            resolution_criteria=p.resolution_criteria,
            status=p.status,
            created_at=p.created_at,
            reviewed_at=p.reviewed_at,
            reviewed_by=p.reviewed_by
        )
        for p in proposals
    ]


@router.post("/admin/proposals/{proposal_id}/approve", response_model=MarketDetail)
async def approve_proposal(
    proposal_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Approve a market proposal and create the market (admin only)"""
    proposal = db.query(MarketProposal).filter(MarketProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )
    
    if proposal.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposal is already {proposal.status}"
        )
    
    # Generate unique slug
    base_slug = slugify(proposal.question)
    slug = base_slug
    counter = 1
    while db.query(Market).filter(Market.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Create market from proposal
    market = Market(
        slug=slug,
        question=proposal.question,
        description=proposal.description,
        category=proposal.category,
        resolution_criteria=proposal.resolution_criteria,
        status=MarketStatus.OPEN,
        yes_liquidity=1000.0,
        no_liquidity=1000.0,
        created_by_user_id=proposal.user_id
    )
    
    db.add(market)
    
    # Update proposal status
    proposal.status = "approved"
    proposal.reviewed_at = datetime.utcnow()
    proposal.reviewed_by = admin.id
    
    db.commit()
    db.refresh(market)
    
    # Auto-seed with agent assessment (async, non-blocking)
    from app.tasks.market_intelligence import seed_new_markets
    seed_new_markets.delay()  # Celery task runs async
    
    # Return market detail
    yes_prob = yes_probability(market)
    no_prob = no_probability(market)
    volume = calculate_volume(market, db)
    
    return MarketDetail(
        id=market.id,
        slug=market.slug,
        question=market.question,
        description=market.description,
        yes_probability=yes_prob,
        no_probability=no_prob,
        yes_liquidity=market.yes_liquidity,
        no_liquidity=market.no_liquidity,
        volume=volume,
        created_at=market.created_at,
        closes_at=market.closes_at,
        resolved_at=market.resolved_at,
        status=market.status.value,
        winning_outcome=market.winning_outcome,
        resolution_source=market.resolution_source,
        resolution_criteria=market.resolution_criteria,
        claim_id=market.claim_id,
        category=market.category
    )


@router.post("/admin/proposals/{proposal_id}/reject")
async def reject_proposal(
    proposal_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Reject a market proposal (admin only)"""
    proposal = db.query(MarketProposal).filter(MarketProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )
    
    if proposal.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposal is already {proposal.status}"
        )
    
    proposal.status = "rejected"
    proposal.reviewed_at = datetime.utcnow()
    proposal.reviewed_by = admin.id
    
    db.commit()
    
    return {"message": "Proposal rejected", "proposal_id": proposal_id}


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    category: Optional[str] = Query(None),
    metric: str = Query("accuracy", regex="^(accuracy|volume|trades)$"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get market leaderboard"""
    query = db.query(UserMarketStats, User).join(
        User, UserMarketStats.user_id == User.id
    )
    
    # Filter by category if provided (would need category tracking in stats)
    # For now, we'll just sort by the selected metric
    
    if metric == "accuracy":
        query = query.order_by(desc(UserMarketStats.accuracy_rate))
    elif metric == "volume":
        query = query.order_by(desc(UserMarketStats.total_volume))
    else:  # trades
        query = query.order_by(desc(UserMarketStats.total_trades))
    
    results = query.limit(limit).all()
    
    return [
        LeaderboardEntry(
            rank=idx + 1,
            username=user.username,
            accuracy_rate=stats.accuracy_rate,
            total_trades=stats.total_trades,
            total_volume=stats.total_volume,
            credits_earned=stats.total_credits_earned
        )
        for idx, (stats, user) in enumerate(results)
    ]


@router.get("/notifications", response_model=List[MarketNotificationResponse])
@TierChecker.require_tier(SubscriptionTier.PRO, SubscriptionTier.TEAM, SubscriptionTier.ENTERPRISE)
async def get_notifications(
    unread_only: bool = Query(False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get market notifications for current user (Pro only)"""
    query = db.query(MarketNotification).filter(
        MarketNotification.user_id == user.id
    )
    
    if unread_only:
        query = query.filter(MarketNotification.read == False)
    
    notifications = query.order_by(desc(MarketNotification.created_at)).limit(50).all()
    
    return [
        MarketNotificationResponse(
            id=n.id,
            market_id=n.market_id,
            notification_type=n.notification_type,
            message=n.message,
            read=n.read,
            created_at=n.created_at
        )
        for n in notifications
    ]


@router.post("/notifications/{notification_id}/read")
@TierChecker.require_tier(SubscriptionTier.PRO, SubscriptionTier.TEAM, SubscriptionTier.ENTERPRISE)
async def mark_notification_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read (Pro only)"""
    notification = db.query(MarketNotification).filter(
        MarketNotification.id == notification_id,
        MarketNotification.user_id == user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.read = True
    db.commit()
    
    return {"message": "Notification marked as read"}


@router.post("/notifications/read-all")
@TierChecker.require_tier(SubscriptionTier.PRO, SubscriptionTier.TEAM, SubscriptionTier.ENTERPRISE)
async def mark_all_notifications_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read (Pro only)"""
    db.query(MarketNotification).filter(
        MarketNotification.user_id == user.id,
        MarketNotification.read == False
    ).update({"read": True})
    
    db.commit()
    
    return {"message": "All notifications marked as read"}


@router.get("/{market_id}/export")
@TierChecker.require_tier(SubscriptionTier.PRO, SubscriptionTier.TEAM, SubscriptionTier.ENTERPRISE)
async def export_market_data(
    market_id: int,
    format: str = Query("csv", regex="^(csv|json)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export market data (Pro only)"""
    from app.services.export import export_market_data as export_service
    from app.utils import track_usage
    
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Track export usage
    track_usage(db, user.id, "exports_per_month")
    
    # Export data
    export_result = export_service(market_id, format, db)
    
    return Response(
        content=export_result["content"],
        media_type=export_result["content_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{export_result["filename"]}"'
        }
    )


@router.get("/{market_id}/insights", response_model=MarketInsightsResponse)
@TierChecker.require_tier(SubscriptionTier.PRO, SubscriptionTier.TEAM, SubscriptionTier.ENTERPRISE)
async def get_market_insights(
    market_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered insights for a market (Pro only)"""
    from app.services.ai_insights import generate_market_insights
    
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    insights = generate_market_insights(market_id, db)
    
    return MarketInsightsResponse(
        key_factors=insights.get("key_factors", []),
        historical_context=insights.get("historical_context", ""),
        risk_assessment={
            "level": insights.get("risk_assessment", {}).get("level", "medium"),
            "reasons": insights.get("risk_assessment", {}).get("reasons", [])
        },
        recommendation=insights.get("recommendation", "esperar")
    )

