"""
Market Analytics Service

Provides analytics and insights for prediction markets including:
- Historical probability data
- User performance metrics
- Category trends
- Market statistics
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from app.database.models import Market, MarketTrade, UserMarketStats, MarketStatus
from app.services.markets import yes_probability, no_probability, calculate_volume


def get_market_history(market_id: int, days: int, db: Session) -> List[Dict[str, Any]]:
    """
    Get historical probability data for a market over time.
    
    Returns a list of data points showing how probabilities changed.
    Each point includes timestamp, yes_probability, no_probability, and volume.
    
    Args:
        market_id: Market ID
        days: Number of days of history to retrieve
        db: Database session
        
    Returns:
        List of dictionaries with historical data points
    """
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        return []
    
    # Get all trades for this market
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    trades = db.query(MarketTrade).filter(
        MarketTrade.market_id == market_id,
        MarketTrade.created_at >= cutoff_date
    ).order_by(MarketTrade.created_at).all()
    
    if not trades:
        # Return current state if no trades
        return [{
            "timestamp": datetime.utcnow().isoformat(),
            "yes_probability": yes_probability(market),
            "no_probability": no_probability(market),
            "volume": calculate_volume(market, db)
        }]
    
    # Reconstruct market state at each trade
    history = []
    
    # Initial state (before any trades)
    initial_yes = 1000.0
    initial_no = 1000.0
    
    for trade in trades:
        # Simulate the trade to get probabilities at that point
        # This is a simplified version - in production, you might want to store snapshots
        if trade.outcome == "yes":
            k = initial_yes * initial_no
            new_yes = initial_yes + trade.cost
            new_no = k / new_yes if new_yes > 0 else initial_no
            initial_yes = new_yes
            initial_no = new_no
        else:
            k = initial_yes * initial_no
            new_no = initial_no + trade.cost
            new_yes = k / new_no if new_no > 0 else initial_yes
            initial_yes = new_yes
            initial_no = new_no
        
        total = initial_yes + initial_no
        yes_prob = initial_yes / total if total > 0 else 0.5
        no_prob = initial_no / total if total > 0 else 0.5
        
        history.append({
            "timestamp": trade.created_at.isoformat(),
            "yes_probability": yes_prob,
            "no_probability": no_prob,
            "volume": sum(t.cost for t in trades if t.created_at <= trade.created_at)
        })
    
    # Add current state
    history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "yes_probability": yes_probability(market),
        "no_probability": no_probability(market),
        "volume": calculate_volume(market, db)
    })
    
    return history


def get_user_performance(user_id: int, db: Session) -> Dict[str, Any]:
    """
    Calculate user's market performance metrics.
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        Dictionary with performance metrics including rank
    """
    stats = db.query(UserMarketStats).filter(
        UserMarketStats.user_id == user_id
    ).first()
    
    if not stats:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "accuracy_rate": 0.0,
            "total_volume": 0.0,
            "credits_earned": 0.0,
            "rank": None
        }
    
    # Calculate rank based on accuracy rate
    # Count users with higher accuracy rate
    rank = db.query(func.count(UserMarketStats.user_id)).filter(
        UserMarketStats.accuracy_rate > stats.accuracy_rate
    ).scalar() + 1
    
    return {
        "total_trades": stats.total_trades,
        "winning_trades": stats.winning_trades,
        "losing_trades": stats.losing_trades,
        "accuracy_rate": stats.accuracy_rate,
        "total_volume": stats.total_volume,
        "credits_earned": stats.total_credits_earned,
        "rank": rank
    }


def get_category_trends(category: str, days: int, db: Session) -> Dict[str, Any]:
    """
    Get trend data for a category of markets.
    
    Args:
        category: Market category
        days: Number of days to analyze
        db: Database session
        
    Returns:
        Dictionary with trend statistics
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all markets in this category
    markets = db.query(Market).filter(
        Market.category == category,
        Market.created_at >= cutoff_date
    ).all()
    
    if not markets:
        return {
            "category": category,
            "total_markets": 0,
            "total_volume": 0.0,
            "average_probability": 0.5,
            "resolved_markets": 0
        }
    
    # Calculate aggregate statistics
    total_volume = sum(calculate_volume(m, db) for m in markets)
    total_prob = sum(yes_probability(m) for m in markets)
    avg_prob = total_prob / len(markets) if markets else 0.5
    
    resolved = sum(1 for m in markets if m.status == MarketStatus.RESOLVED)
    
    return {
        "category": category,
        "total_markets": len(markets),
        "total_volume": total_volume,
        "average_probability": avg_prob,
        "resolved_markets": resolved
    }


def update_user_market_stats(db: Session, user_id: int, amount: float, outcome: str):
    """
    Update user market stats after a trade.
    Note: Accuracy will be updated when markets resolve.
    
    Args:
        db: Database session
        user_id: User ID
        amount: Trade amount
        outcome: Trade outcome ("yes" or "no")
    """
    from app.database.models import UserMarketStats
    
    stats = db.query(UserMarketStats).filter(
        UserMarketStats.user_id == user_id
    ).first()
    
    if not stats:
        stats = UserMarketStats(user_id=user_id)
        db.add(stats)
    
    stats.total_trades += 1
    stats.total_volume += amount
    stats.last_updated = datetime.utcnow()
    
    db.commit()
    db.refresh(stats)


def update_user_stats_on_resolution(
    db: Session,
    market_id: int,
    winning_outcome: str
):
    """
    Update user stats when a market resolves.
    This calculates wins/losses and accuracy.
    
    Args:
        db: Database session
        market_id: Market ID
        winning_outcome: "yes" or "no"
    """
    from app.database.models import MarketTrade, UserMarketStats
    
    # Get all trades for this market
    trades = db.query(MarketTrade).filter(
        MarketTrade.market_id == market_id
    ).all()
    
    # Group trades by user and outcome
    user_positions = {}
    for trade in trades:
        if trade.user_id not in user_positions:
            user_positions[trade.user_id] = {"yes": 0.0, "no": 0.0}
        
        if trade.outcome == "yes":
            user_positions[trade.user_id]["yes"] += trade.shares
        else:
            user_positions[trade.user_id]["no"] += trade.shares
    
    # Update stats for each user
    for user_id, positions in user_positions.items():
        stats = db.query(UserMarketStats).filter(
            UserMarketStats.user_id == user_id
        ).first()
        
        if not stats:
            stats = UserMarketStats(user_id=user_id)
            db.add(stats)
        
        # Determine if user won
        winning_shares = positions[winning_outcome]
        losing_shares = positions["yes" if winning_outcome == "no" else "no"]
        
        if winning_shares > 0:
            stats.winning_trades += 1
        if losing_shares > 0:
            stats.losing_trades += 1
        
        # Recalculate accuracy
        total_resolved = stats.winning_trades + stats.losing_trades
        if total_resolved > 0:
            stats.accuracy_rate = stats.winning_trades / total_resolved
        
        # Update credits earned (winning shares pay 1 credit each)
        stats.total_credits_earned += winning_shares
        
        stats.last_updated = datetime.utcnow()
    
    db.commit()

