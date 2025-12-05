"""
Market Notifications Task

Monitors markets for significant changes and creates notifications for subscribed users.
Runs periodically to check for:
- Significant probability changes (>5%)
- Market resolutions
- New markets in user's preferred categories
"""

from celery import shared_task
from app.database.connection import get_db
from app.database.models import (
    Market, MarketStatus, MarketNotification, MarketTrade, User,
    SubscriptionTier
)
from app.services.markets import yes_probability
from app.utils import get_user_tier, get_tier_limit
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.market_notifications.check_market_probability_changes")
def check_market_probability_changes():
    """
    Check for significant probability changes and notify subscribed users.
    Runs periodically (e.g., every hour).
    """
    db = next(get_db())
    
    try:
        # Get all open markets
        markets = db.query(Market).filter(Market.status == MarketStatus.OPEN).all()
        
        for market in markets:
            try:
                # Get recent trades (last hour)
                cutoff = datetime.utcnow() - timedelta(hours=1)
                recent_trades = db.query(MarketTrade).filter(
                    MarketTrade.market_id == market.id,
                    MarketTrade.created_at >= cutoff
                ).all()
                
                if not recent_trades:
                    continue
                
                # Calculate old probability (before recent trades)
                # Simplified: use market state before recent trades
                # In production, you might want to store probability snapshots
                current_prob = yes_probability(market)
                
                # Estimate old probability (simplified - in production, store snapshots)
                # For now, we'll notify if there were significant trades
                if len(recent_trades) >= 5:  # Significant activity
                    # Get Pro users who might be interested
                    # For now, notify all Pro users (can be refined with preferences)
                    pro_users = db.query(User).join(
                        User.subscription
                    ).filter(
                        User.subscription.has(tier=SubscriptionTier.PRO)
                    ).all()
                    
                    for user in pro_users:
                        # Check if notification already exists
                        existing = db.query(MarketNotification).filter(
                            MarketNotification.user_id == user.id,
                            MarketNotification.market_id == market.id,
                            MarketNotification.notification_type == "probability_change",
                            MarketNotification.created_at >= cutoff
                        ).first()
                        
                        if not existing:
                            notification = MarketNotification(
                                user_id=user.id,
                                market_id=market.id,
                                notification_type="probability_change",
                                message=f"El mercado '{market.question}' ha tenido actividad significativa. Probabilidad actual: {(current_prob * 100):.1f}%",
                                read=False
                            )
                            db.add(notification)
                
            except Exception as e:
                logger.error(f"Error processing market {market.id}: {str(e)}")
                continue
        
        db.commit()
        logger.info("Market probability change check completed")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in market notifications task: {str(e)}")
        raise
    finally:
        db.close()


@shared_task(name="app.tasks.market_notifications.notify_market_resolution")
def notify_market_resolution(market_id: int):
    """
    Notify users when a market is resolved.
    Called when a market is resolved.
    """
    db = next(get_db())
    
    try:
        market = db.query(Market).filter(Market.id == market_id).first()
        if not market or market.status != MarketStatus.RESOLVED:
            return
        
        # Get all users who traded on this market
        trades = db.query(MarketTrade).filter(
            MarketTrade.market_id == market_id
        ).all()
        
        user_ids = set(trade.user_id for trade in trades)
        
        for user_id in user_ids:
            notification = MarketNotification(
                user_id=user_id,
                market_id=market_id,
                notification_type="resolution",
                message=f"El mercado '{market.question}' ha sido resuelto. Resultado: {market.winning_outcome.upper()}",
                read=False
            )
            db.add(notification)
        
        db.commit()
        logger.info(f"Resolution notifications sent for market {market_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error notifying market resolution: {str(e)}")
        raise
    finally:
        db.close()


@shared_task(name="app.tasks.market_notifications.notify_new_markets")
def notify_new_markets():
    """
    Notify Pro users about new markets in their preferred categories.
    Runs periodically (e.g., daily).
    """
    db = next(get_db())
    
    try:
        # Get markets created in the last 24 hours
        cutoff = datetime.utcnow() - timedelta(hours=24)
        new_markets = db.query(Market).filter(
            Market.created_at >= cutoff,
            Market.status == MarketStatus.OPEN
        ).all()
        
        if not new_markets:
            return
        
        # Get Pro users with preferred categories
        pro_users = db.query(User).join(
            User.subscription
        ).filter(
            User.subscription.has(tier=SubscriptionTier.PRO),
            User.preferred_categories.isnot(None)
        ).all()
        
        for user in pro_users:
            if not user.preferred_categories:
                continue
            
            # Find new markets in user's preferred categories
            for market in new_markets:
                if market.category and market.category in user.preferred_categories:
                    # Check if notification already exists
                    existing = db.query(MarketNotification).filter(
                        MarketNotification.user_id == user.id,
                        MarketNotification.market_id == market.id,
                        MarketNotification.notification_type == "new_market"
                    ).first()
                    
                    if not existing:
                        notification = MarketNotification(
                            user_id=user.id,
                            market_id=market.id,
                            notification_type="new_market",
                            message=f"Nuevo mercado en {market.category}: '{market.question}'",
                            read=False
                        )
                        db.add(notification)
        
        db.commit()
        logger.info("New market notifications sent")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in new market notifications: {str(e)}")
        raise
    finally:
        db.close()

