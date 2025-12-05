"""
Background tasks for market intelligence and seeding
"""
from celery import shared_task
from app.database import SessionLocal
from app.database.models import Market, MarketStatus, MarketTrade
from app.services.market_seeding import seed_market_with_agent_assessment
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.market_intelligence.seed_new_markets")
def seed_new_markets():
    """
    Seed newly created markets that haven't been seeded yet.
    Runs periodically (e.g., every 5 minutes) to batch process new markets.
    """
    db = SessionLocal()
    try:
        # Find markets created in last hour that have no trades
        cutoff = datetime.utcnow() - timedelta(hours=1)
        
        markets = db.query(Market).filter(
            Market.status == MarketStatus.OPEN,
            Market.created_at >= cutoff,
            ~Market.trades.any()  # No trades yet
        ).all()
        
        if not markets:
            logger.debug("No new markets to seed")
            return {"seeded": 0, "skipped": 0}
        
        logger.info(f"Seeding {len(markets)} new markets...")
        
        seeded_count = 0
        skipped_count = 0
        
        # Process markets sequentially (to avoid rate limits)
        for market in markets:
            try:
                # Run async function in sync context
                result = asyncio.run(
                    seed_market_with_agent_assessment(market, db)
                )
                
                if result["seeded"]:
                    seeded_count += 1
                else:
                    skipped_count += 1
                    logger.debug(
                        f"Market {market.id} not seeded: {result.get('reason', 'unknown')}"
                    )
            except Exception as e:
                logger.error(f"Error seeding market {market.id}: {e}")
                skipped_count += 1
        
        logger.info(f"Market seeding complete: {seeded_count} seeded, {skipped_count} skipped")
        
        return {
            "seeded": seeded_count,
            "skipped": skipped_count,
            "total": len(markets)
        }
        
    except Exception as e:
        logger.error(f"Error in seed_new_markets task: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@shared_task(name="app.tasks.market_intelligence.reassess_inactive_markets")
def reassess_inactive_markets():
    """
    Re-assess markets that haven't had trades in 24+ hours.
    Only adjusts if agent assessment differs significantly from current probability.
    """
    db = SessionLocal()
    try:
        from app.services.markets import yes_probability
        from app.agents.market_intelligence_agent import MarketIntelligenceAgent
        
        # Find markets with no trades in last 24 hours
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        markets = db.query(Market).filter(
            Market.status == MarketStatus.OPEN,
            Market.created_at < cutoff  # At least 24 hours old
        ).all()
        
        if not markets:
            return {"assessed": 0, "adjusted": 0}
        
        agent = MarketIntelligenceAgent()
        assessed_count = 0
        adjusted_count = 0
        
        for market in markets:
            try:
                # Get last trade time
                last_trade = db.query(MarketTrade).filter(
                    MarketTrade.market_id == market.id
                ).order_by(MarketTrade.created_at.desc()).first()
                
                if last_trade and last_trade.created_at > cutoff:
                    continue  # Has recent trades, skip
                
                # Get current probability
                current_prob = yes_probability(market)
                
                # Get agent assessment
                assessment = asyncio.run(
                    agent.assess_market_probability(market, db)
                )
                
                assessed_prob = assessment["yes_probability"]
                confidence = assessment["confidence"]
                
                # Only adjust if:
                # 1. Confidence is high (>0.6)
                # 2. Difference is significant (>15%)
                # 3. Market has low volume (few trades)
                trade_count = db.query(MarketTrade).filter(
                    MarketTrade.market_id == market.id
                ).count()
                
                prob_diff = abs(assessed_prob - current_prob)
                
                if (confidence > 0.6 and 
                    prob_diff > 0.15 and 
                    trade_count < 10):  # Low volume markets only
                    
                    # Place small adjustment trade (max 30 credits)
                    adjustment_amount = min(30.0, assessment["recommended_seed_amount"] * 0.3)
                    outcome = "yes" if assessed_prob > current_prob else "no"
                    
                    try:
                        from app.services.markets import buy_yes, buy_no
                        if outcome == "yes":
                            buy_yes(market, adjustment_amount, db)
                        else:
                            buy_no(market, adjustment_amount, db)
                        
                        adjusted_count += 1
                        logger.info(
                            f"Adjusted market {market.id}: {current_prob:.1%} → "
                            f"{yes_probability(market):.1%} (assessed: {assessed_prob:.1%})"
                        )
                    except Exception as e:
                        logger.warning(f"Could not adjust market {market.id}: {e}")
                
                assessed_count += 1
                
            except Exception as e:
                logger.error(f"Error reassessing market {market.id}: {e}")
        
        logger.info(f"Reassessment complete: {assessed_count} assessed, {adjusted_count} adjusted")
        
        return {
            "assessed": assessed_count,
            "adjusted": adjusted_count
        }
        
    except Exception as e:
        logger.error(f"Error in reassess_inactive_markets task: {e}")
        return {"error": str(e)}
    finally:
        db.close()
