"""
Virtual Token Manager

Manages virtual tokens representing market positions.
Token value = current_probability * base_value.

This system prepares for future blockchain migration by:
1. Tracking token ownership and transfers
2. Maintaining price history
3. Calculating portfolio performance
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.database.models import Market, MarketTrade

logger = logging.getLogger(__name__)


@dataclass
class TokenPosition:
    """A user's position in a market."""
    market_id: int
    token_type: str  # "yes" or "no"
    amount: float
    average_purchase_price: float
    current_price: float
    current_value: float
    unrealized_gain_loss: float
    unrealized_gain_loss_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "market_id": self.market_id,
            "token_type": self.token_type,
            "amount": self.amount,
            "average_purchase_price": self.average_purchase_price,
            "current_price": self.current_price,
            "current_value": self.current_value,
            "unrealized_gain_loss": self.unrealized_gain_loss,
            "unrealized_gain_loss_percent": self.unrealized_gain_loss_percent
        }


@dataclass
class PortfolioSummary:
    """Summary of a user's entire portfolio."""
    total_invested: float
    current_value: float
    total_gain_loss: float
    total_gain_loss_percent: float
    positions_count: int
    winning_positions: int
    losing_positions: int
    positions: List[TokenPosition]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_invested": self.total_invested,
            "current_value": self.current_value,
            "total_gain_loss": self.total_gain_loss,
            "total_gain_loss_percent": self.total_gain_loss_percent,
            "positions_count": self.positions_count,
            "winning_positions": self.winning_positions,
            "losing_positions": self.losing_positions,
            "positions": [p.to_dict() for p in self.positions]
        }


class VirtualTokenManager:
    """
    Manages virtual tokens representing market positions.
    
    Token pricing:
    - YES token value = yes_probability * 1 credit
    - NO token value = no_probability * 1 credit
    - At resolution, winning tokens = 1 credit, losing tokens = 0
    """
    
    BASE_VALUE = 1.0  # Each token resolves to 1 credit if correct
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_token_price(self, market_id: int, token_type: str) -> Optional[float]:
        """
        Get current price for a token type in a market.
        
        Price = current probability of that outcome.
        """
        market = self.db.query(Market).filter(Market.id == market_id).first()
        if not market:
            return None
        
        total_liquidity = market.yes_liquidity + market.no_liquidity
        if total_liquidity == 0:
            return 0.5  # Default
        
        if token_type.lower() == "yes":
            return market.yes_liquidity / total_liquidity
        else:
            return market.no_liquidity / total_liquidity
    
    def get_user_positions(
        self,
        user_id: int,
        include_resolved: bool = False
    ) -> List[TokenPosition]:
        """
        Get all token positions for a user.
        
        Aggregates trades into positions per market.
        """
        # Get all trades for user
        query = self.db.query(
            MarketTrade.market_id,
            MarketTrade.outcome,
            func.sum(MarketTrade.shares).label('total_shares'),
            func.sum(MarketTrade.cost).label('total_cost')
        ).filter(
            MarketTrade.user_id == user_id
        ).group_by(
            MarketTrade.market_id,
            MarketTrade.outcome
        )
        
        trades = query.all()
        
        if not trades:
            return []
        
        positions = []
        market_ids = list(set(t.market_id for t in trades))
        
        # Get markets
        markets = {
            m.id: m 
            for m in self.db.query(Market).filter(Market.id.in_(market_ids)).all()
        }
        
        for trade in trades:
            market = markets.get(trade.market_id)
            if not market:
                continue
            
            # Skip resolved markets if not requested
            if not include_resolved and market.status == "resolved":
                continue
            
            # Calculate average purchase price
            avg_price = trade.total_cost / trade.total_shares if trade.total_shares > 0 else 0
            
            # Get current price
            current_price = self.get_token_price(trade.market_id, trade.outcome)
            
            # For resolved markets, use final price
            if market.status == "resolved":
                if market.winning_outcome == trade.outcome:
                    current_price = 1.0
                else:
                    current_price = 0.0
            
            # Calculate values
            current_value = trade.total_shares * current_price
            gain_loss = current_value - trade.total_cost
            gain_loss_percent = (gain_loss / trade.total_cost * 100) if trade.total_cost > 0 else 0
            
            positions.append(TokenPosition(
                market_id=trade.market_id,
                token_type=trade.outcome,
                amount=trade.total_shares,
                average_purchase_price=avg_price,
                current_price=current_price,
                current_value=current_value,
                unrealized_gain_loss=gain_loss,
                unrealized_gain_loss_percent=gain_loss_percent
            ))
        
        return positions
    
    def get_portfolio_summary(
        self,
        user_id: int,
        include_resolved: bool = False
    ) -> PortfolioSummary:
        """
        Get complete portfolio summary for a user.
        """
        positions = self.get_user_positions(user_id, include_resolved)
        
        if not positions:
            return PortfolioSummary(
                total_invested=0.0,
                current_value=0.0,
                total_gain_loss=0.0,
                total_gain_loss_percent=0.0,
                positions_count=0,
                winning_positions=0,
                losing_positions=0,
                positions=[]
            )
        
        total_invested = sum(p.amount * p.average_purchase_price for p in positions)
        current_value = sum(p.current_value for p in positions)
        total_gain_loss = sum(p.unrealized_gain_loss for p in positions)
        
        gain_loss_percent = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0
        
        winning = sum(1 for p in positions if p.unrealized_gain_loss > 0)
        losing = sum(1 for p in positions if p.unrealized_gain_loss < 0)
        
        return PortfolioSummary(
            total_invested=total_invested,
            current_value=current_value,
            total_gain_loss=total_gain_loss,
            total_gain_loss_percent=gain_loss_percent,
            positions_count=len(positions),
            winning_positions=winning,
            losing_positions=losing,
            positions=sorted(positions, key=lambda x: x.unrealized_gain_loss, reverse=True)
        )
    
    def get_position_history(
        self,
        user_id: int,
        market_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get historical performance for a position.
        
        Shows how the position value changed over time.
        """
        # Get user's trades for this market
        trades = self.db.query(MarketTrade).filter(
            MarketTrade.user_id == user_id,
            MarketTrade.market_id == market_id
        ).order_by(MarketTrade.created_at).all()
        
        if not trades:
            return []
        
        # Build position over time
        history = []
        cumulative_shares = {"yes": 0.0, "no": 0.0}
        cumulative_cost = {"yes": 0.0, "no": 0.0}
        
        for trade in trades:
            cumulative_shares[trade.outcome] += trade.shares
            cumulative_cost[trade.outcome] += trade.cost
            
            # Get market state at trade time (approximation)
            history.append({
                "timestamp": trade.created_at.isoformat(),
                "action": "buy",
                "outcome": trade.outcome,
                "shares": trade.shares,
                "price": trade.price,
                "cost": trade.cost,
                "cumulative_shares": dict(cumulative_shares),
                "cumulative_cost": dict(cumulative_cost)
            })
        
        return history
    
    def calculate_resolved_pnl(
        self,
        user_id: int,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Calculate realized profit/loss from resolved markets.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get resolved markets user participated in
        result = self.db.execute(
            text("""
                SELECT 
                    m.id,
                    m.question,
                    m.winning_outcome,
                    m.resolved_at,
                    t.outcome,
                    SUM(t.shares) as total_shares,
                    SUM(t.cost) as total_cost
                FROM markets m
                JOIN market_trades t ON m.id = t.market_id
                WHERE m.status = 'resolved'
                  AND m.resolved_at >= :cutoff
                  AND t.user_id = :user_id
                GROUP BY m.id, m.question, m.winning_outcome, m.resolved_at, t.outcome
                ORDER BY m.resolved_at DESC
            """),
            {"cutoff": cutoff, "user_id": user_id}
        ).fetchall()
        
        total_profit = 0.0
        total_loss = 0.0
        markets_won = 0
        markets_lost = 0
        
        resolved_positions = []
        
        for row in result:
            payout = row.total_shares if row.outcome == row.winning_outcome else 0
            profit_loss = payout - row.total_cost
            
            if profit_loss > 0:
                total_profit += profit_loss
                markets_won += 1
            else:
                total_loss += abs(profit_loss)
                markets_lost += 1
            
            resolved_positions.append({
                "market_id": row.id,
                "question": row.question[:100],
                "position": row.outcome.upper(),
                "winner": row.winning_outcome.upper(),
                "shares": row.total_shares,
                "cost": row.total_cost,
                "payout": payout,
                "profit_loss": profit_loss,
                "resolved_at": row.resolved_at.isoformat()
            })
        
        return {
            "period_days": days,
            "total_profit": total_profit,
            "total_loss": total_loss,
            "net_pnl": total_profit - total_loss,
            "markets_won": markets_won,
            "markets_lost": markets_lost,
            "win_rate": markets_won / (markets_won + markets_lost) if (markets_won + markets_lost) > 0 else 0,
            "resolved_positions": resolved_positions
        }
    
    def get_leaderboard(
        self,
        period_days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top performers by realized P&L.
        """
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        
        result = self.db.execute(
            text("""
                WITH resolved_trades AS (
                    SELECT 
                        t.user_id,
                        CASE 
                            WHEN t.outcome = m.winning_outcome THEN t.shares
                            ELSE 0
                        END as payout,
                        t.cost
                    FROM market_trades t
                    JOIN markets m ON m.id = t.market_id
                    WHERE m.status = 'resolved'
                      AND m.resolved_at >= :cutoff
                )
                SELECT 
                    user_id,
                    SUM(payout) as total_payout,
                    SUM(cost) as total_cost,
                    SUM(payout) - SUM(cost) as net_pnl,
                    COUNT(*) as trade_count
                FROM resolved_trades
                GROUP BY user_id
                ORDER BY net_pnl DESC
                LIMIT :limit
            """),
            {"cutoff": cutoff, "limit": limit}
        ).fetchall()
        
        leaderboard = []
        for i, row in enumerate(result, 1):
            leaderboard.append({
                "rank": i,
                "user_id": row.user_id,
                "total_payout": row.total_payout,
                "total_invested": row.total_cost,
                "net_pnl": row.net_pnl,
                "roi_percent": (row.net_pnl / row.total_cost * 100) if row.total_cost > 0 else 0,
                "trade_count": row.trade_count
            })
        
        return leaderboard
