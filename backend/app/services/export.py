"""
Market Data Export Service

Provides functionality to export market data in various formats:
- CSV
- JSON
- Excel (future)
"""

from sqlalchemy.orm import Session
from app.database.models import Market, MarketTrade
from app.services.markets import yes_probability, no_probability, calculate_volume
from typing import Dict, List, Any
import csv
import json
import io


def export_market_data(market_id: int, format: str, db: Session) -> Dict[str, Any]:
    """
    Export market data in the specified format.
    
    Args:
        market_id: Market ID
        format: Export format ('csv', 'json', 'excel')
        db: Database session
        
    Returns:
        Dictionary with 'content' (bytes) and 'filename' (str)
    """
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise ValueError("Market not found")
    
    # Get all trades for this market
    trades = db.query(MarketTrade).filter(
        MarketTrade.market_id == market_id
    ).order_by(MarketTrade.created_at).all()
    
    # Prepare data
    market_data = {
        "market": {
            "id": market.id,
            "question": market.question,
            "description": market.description,
            "category": market.category,
            "status": market.status.value,
            "yes_probability": yes_probability(market),
            "no_probability": no_probability(market),
            "volume": calculate_volume(market, db),
            "created_at": market.created_at.isoformat() if market.created_at else None,
            "closes_at": market.closes_at.isoformat() if market.closes_at else None,
            "resolved_at": market.resolved_at.isoformat() if market.resolved_at else None,
            "winning_outcome": market.winning_outcome,
        },
        "trades": [
            {
                "id": trade.id,
                "user_id": trade.user_id,
                "outcome": trade.outcome,
                "shares": trade.shares,
                "price": trade.price,
                "cost": trade.cost,
                "created_at": trade.created_at.isoformat() if trade.created_at else None,
            }
            for trade in trades
        ]
    }
    
    if format == "json":
        return export_json(market_data, market)
    elif format == "csv":
        return export_csv(market_data, market)
    else:
        raise ValueError(f"Unsupported format: {format}")


def export_json(market_data: Dict[str, Any], market: Market) -> Dict[str, Any]:
    """Export market data as JSON"""
    content = json.dumps(market_data, indent=2, ensure_ascii=False)
    filename = f"market_{market.slug}_{market.id}.json"
    
    return {
        "content": content.encode('utf-8'),
        "filename": filename,
        "content_type": "application/json"
    }


def export_csv(market_data: Dict[str, Any], market: Market) -> Dict[str, Any]:
    """Export market data as CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write market info header
    writer.writerow(["Market Information"])
    writer.writerow(["Question", market_data["market"]["question"]])
    writer.writerow(["Description", market_data["market"]["description"] or ""])
    writer.writerow(["Category", market_data["market"]["category"] or ""])
    writer.writerow(["Status", market_data["market"]["status"]])
    writer.writerow(["Yes Probability", f"{market_data['market']['yes_probability']:.2%}"])
    writer.writerow(["No Probability", f"{market_data['market']['no_probability']:.2%}"])
    writer.writerow(["Volume", market_data["market"]["volume"]])
    writer.writerow([])
    
    # Write trades header
    writer.writerow(["Trades"])
    writer.writerow(["ID", "User ID", "Outcome", "Shares", "Price", "Cost", "Created At"])
    
    # Write trade data
    for trade in market_data["trades"]:
        writer.writerow([
            trade["id"],
            trade["user_id"],
            trade["outcome"].upper(),
            trade["shares"],
            trade["price"],
            trade["cost"],
            trade["created_at"]
        ])
    
    content = output.getvalue().encode('utf-8')
    filename = f"market_{market.slug}_{market.id}.csv"
    
    return {
        "content": content,
        "filename": filename,
        "content_type": "text/csv"
    }

