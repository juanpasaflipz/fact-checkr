"""
Tokens Router

API endpoints for virtual token management and portfolio tracking.
"""

from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.auth import get_current_user
from app.services.tokens import VirtualTokenManager

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


class PositionResponse(BaseModel):
    market_id: int
    token_type: str
    amount: float
    average_purchase_price: float
    current_price: float
    current_value: float
    unrealized_gain_loss: float
    unrealized_gain_loss_percent: float


class PortfolioResponse(BaseModel):
    total_invested: float
    current_value: float
    total_gain_loss: float
    total_gain_loss_percent: float
    positions_count: int
    winning_positions: int
    losing_positions: int


@router.get("/portfolio")
async def get_my_portfolio(
    include_resolved: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's portfolio summary.
    
    Returns all positions with current values and P&L.
    """
    manager = VirtualTokenManager(db)
    summary = manager.get_portfolio_summary(current_user.id, include_resolved)
    return summary.to_dict()


@router.get("/positions")
async def get_my_positions(
    include_resolved: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all token positions for the current user.
    """
    manager = VirtualTokenManager(db)
    positions = manager.get_user_positions(current_user.id, include_resolved)
    return [p.to_dict() for p in positions]


@router.get("/position/{market_id}")
async def get_position(
    market_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's position in a specific market.
    """
    manager = VirtualTokenManager(db)
    positions = manager.get_user_positions(current_user.id, include_resolved=True)
    
    market_positions = [p for p in positions if p.market_id == market_id]
    
    if not market_positions:
        return {"message": "No tienes posición en este mercado", "positions": []}
    
    return {
        "market_id": market_id,
        "positions": [p.to_dict() for p in market_positions]
    }


@router.get("/position/{market_id}/history")
async def get_position_history(
    market_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get historical performance for a position.
    """
    manager = VirtualTokenManager(db)
    history = manager.get_position_history(current_user.id, market_id, days)
    return {"market_id": market_id, "history": history}


@router.get("/pnl")
async def get_realized_pnl(
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get realized profit/loss from resolved markets.
    """
    manager = VirtualTokenManager(db)
    return manager.calculate_resolved_pnl(current_user.id, days)


@router.get("/leaderboard")
async def get_leaderboard(
    days: int = 30,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get top performers by realized P&L.
    
    Public endpoint.
    """
    manager = VirtualTokenManager(db)
    return manager.get_leaderboard(days, limit)


@router.get("/price/{market_id}")
async def get_token_prices(
    market_id: int,
    db: Session = Depends(get_db)
):
    """
    Get current token prices for a market.
    
    Public endpoint.
    """
    manager = VirtualTokenManager(db)
    
    yes_price = manager.get_token_price(market_id, "yes")
    no_price = manager.get_token_price(market_id, "no")
    
    if yes_price is None:
        raise HTTPException(status_code=404, detail="Mercado no encontrado")
    
    return {
        "market_id": market_id,
        "yes_token_price": yes_price,
        "no_token_price": no_price,
        "note": "Precio = probabilidad actual del resultado"
    }
