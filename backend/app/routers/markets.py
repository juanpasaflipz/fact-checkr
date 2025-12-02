"""Prediction markets routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime
import re

from app.database.connection import get_db
from app.database.models import Market, MarketStatus, MarketTrade, UserBalance, User, Claim
from app.auth import get_current_user, get_admin_user, get_optional_user
from app.models import (
    MarketSummary,
    MarketDetail,
    TradeRequest,
    TradeResponse,
    UserBalanceResponse,
    CreateMarketRequest,
    ResolveMarketRequest,
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
async def trade_market(
    market_id: int,
    trade_request: TradeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Place a trade on a market"""
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
        
        # Distribute payouts
        for user_id, positions in user_positions.items():
            balance = get_or_create_user_balance(db, user_id)
            
            # Calculate winning shares
            winning_shares = positions[resolve_request.winning_outcome]
            
            if winning_shares > 0:
                # Each winning share pays 1 credit
                payout = winning_shares
                balance.available_credits += payout
        
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

