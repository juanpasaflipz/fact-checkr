"""
Market Votes Router

API endpoints for user voting on market outcomes.
Separate from trading - allows users to express opinions without committing credits.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.database.models import MarketVote, Market, User
from app.core.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api/markets", tags=["market-votes"])


class VoteRequest(BaseModel):
    """Request body for submitting a vote."""
    outcome: str = Field(..., pattern="^(yes|no)$")
    confidence: Optional[int] = Field(None, ge=1, le=5)
    reasoning: Optional[str] = Field(None, max_length=500)


class VoteResponse(BaseModel):
    """Response for a vote submission."""
    id: int
    market_id: int
    outcome: str
    confidence: Optional[int]
    reasoning: Optional[str]
    created_at: str
    updated_at: str


class VoteAggregation(BaseModel):
    """Aggregated vote statistics for a market."""
    total_votes: int
    yes_votes: int
    no_votes: int
    yes_percentage: float
    no_percentage: float
    avg_confidence: Optional[float]
    high_confidence_yes: int  # Votes with confidence >= 4
    high_confidence_no: int


@router.post("/{market_id}/vote", response_model=VoteResponse)
async def submit_vote(
    market_id: int,
    vote: VoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit or update a vote on a market.
    
    Each user can only have one vote per market.
    Re-submitting updates the existing vote.
    """
    # Check market exists and is open
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Mercado no encontrado")
    
    if market.status != "open":
        raise HTTPException(status_code=400, detail="El mercado no está abierto para votar")
    
    # Check for existing vote
    existing_vote = db.query(MarketVote).filter(
        MarketVote.market_id == market_id,
        MarketVote.user_id == current_user.id
    ).first()
    
    if existing_vote:
        # Update existing vote
        existing_vote.outcome = vote.outcome
        existing_vote.confidence = vote.confidence
        existing_vote.reasoning = vote.reasoning
        existing_vote.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_vote)
        
        return VoteResponse(
            id=existing_vote.id,
            market_id=existing_vote.market_id,
            outcome=existing_vote.outcome,
            confidence=existing_vote.confidence,
            reasoning=existing_vote.reasoning,
            created_at=existing_vote.created_at.isoformat(),
            updated_at=existing_vote.updated_at.isoformat()
        )
    
    # Create new vote
    new_vote = MarketVote(
        market_id=market_id,
        user_id=current_user.id,
        outcome=vote.outcome,
        confidence=vote.confidence,
        reasoning=vote.reasoning
    )
    db.add(new_vote)
    db.commit()
    db.refresh(new_vote)
    
    return VoteResponse(
        id=new_vote.id,
        market_id=new_vote.market_id,
        outcome=new_vote.outcome,
        confidence=new_vote.confidence,
        reasoning=new_vote.reasoning,
        created_at=new_vote.created_at.isoformat(),
        updated_at=new_vote.updated_at.isoformat()
    )


@router.get("/{market_id}/votes", response_model=VoteAggregation)
async def get_vote_aggregation(
    market_id: int,
    db: Session = Depends(get_db)
):
    """
    Get aggregated vote statistics for a market.
    
    Public endpoint - anyone can see vote statistics.
    """
    # Check market exists
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Mercado no encontrado")
    
    # Get all votes for this market
    votes = db.query(MarketVote).filter(MarketVote.market_id == market_id).all()
    
    if not votes:
        return VoteAggregation(
            total_votes=0,
            yes_votes=0,
            no_votes=0,
            yes_percentage=50.0,
            no_percentage=50.0,
            avg_confidence=None,
            high_confidence_yes=0,
            high_confidence_no=0
        )
    
    # Calculate statistics
    total = len(votes)
    yes_votes = sum(1 for v in votes if v.outcome == "yes")
    no_votes = sum(1 for v in votes if v.outcome == "no")
    
    # Confidence stats
    confidences = [v.confidence for v in votes if v.confidence is not None]
    avg_confidence = sum(confidences) / len(confidences) if confidences else None
    
    high_confidence_yes = sum(1 for v in votes if v.outcome == "yes" and v.confidence and v.confidence >= 4)
    high_confidence_no = sum(1 for v in votes if v.outcome == "no" and v.confidence and v.confidence >= 4)
    
    return VoteAggregation(
        total_votes=total,
        yes_votes=yes_votes,
        no_votes=no_votes,
        yes_percentage=(yes_votes / total) * 100 if total > 0 else 50.0,
        no_percentage=(no_votes / total) * 100 if total > 0 else 50.0,
        avg_confidence=avg_confidence,
        high_confidence_yes=high_confidence_yes,
        high_confidence_no=high_confidence_no
    )


@router.get("/{market_id}/vote", response_model=Optional[VoteResponse])
async def get_my_vote(
    market_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's vote for a market.
    
    Returns None if user hasn't voted.
    """
    vote = db.query(MarketVote).filter(
        MarketVote.market_id == market_id,
        MarketVote.user_id == current_user.id
    ).first()
    
    if not vote:
        return None
    
    return VoteResponse(
        id=vote.id,
        market_id=vote.market_id,
        outcome=vote.outcome,
        confidence=vote.confidence,
        reasoning=vote.reasoning,
        created_at=vote.created_at.isoformat(),
        updated_at=vote.updated_at.isoformat()
    )


@router.delete("/{market_id}/vote")
async def delete_vote(
    market_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete the current user's vote for a market."""
    vote = db.query(MarketVote).filter(
        MarketVote.market_id == market_id,
        MarketVote.user_id == current_user.id
    ).first()
    
    if not vote:
        raise HTTPException(status_code=404, detail="No has votado en este mercado")
    
    db.delete(vote)
    db.commit()
    
    return {"message": "Voto eliminado"}
