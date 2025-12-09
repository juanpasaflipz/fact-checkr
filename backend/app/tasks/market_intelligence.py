"""
Background tasks for market intelligence and seeding

Implements tiered analysis system:
- Tier 1 (Lightweight): Every 1-2 hours, no LLM calls
- Tier 2 (Daily): Once per day, full multi-agent synthesis
- Tier 3 (On-Demand): Deep analysis when triggered
"""
from celery import shared_task
from app.database import SessionLocal
from app.database.models import Market, MarketStatus, MarketTrade, MarketPredictionFactors
from app.services.market_seeding import seed_market_with_agent_assessment
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Tiered Analysis Tasks
# =============================================================================

@shared_task(name="app.tasks.market_intelligence.tier1_lightweight_update")
def tier1_lightweight_update():
    """
    Tier 1 - Lightweight update for active markets.
    
    Runs every 1-2 hours to:
    - Update sentiment scores (no LLM)
    - Track news volume
    - Detect probability shifts that need tier3 analysis
    
    Cost: ~$0 per market (no LLM calls)
    """
    from app.services.market_intelligence import MarketSynthesizer
    from app.services.market_intelligence.models import AnalysisTier
    from app.services.data_aggregation import DataAggregator
    
    db = SessionLocal()
    try:
        # Get all open markets
        markets = db.query(Market).filter(
            Market.status == MarketStatus.OPEN
        ).all()
        
        if not markets:
            return {"updated": 0, "triggered_tier3": 0}
        
        logger.info(f"Tier 1 update for {len(markets)} markets...")
        
        synthesizer = MarketSynthesizer()
        aggregator = DataAggregator(db)
        updated = 0
        triggered_tier3 = 0
        
        for market in markets:
            try:
                # Get current probability
                total_liq = market.yes_liquidity + market.no_liquidity
                current_prob = market.yes_liquidity / total_liq if total_liq > 0 else 0.5
                
                # Get last prediction
                last_pred = db.query(MarketPredictionFactors).filter(
                    MarketPredictionFactors.market_id == market.id
                ).order_by(MarketPredictionFactors.created_at.desc()).first()
                
                # Run lightweight analysis
                data_bundle = asyncio.run(
                    aggregator.get_market_data(
                        market_id=market.id,
                        market_question=market.question,
                        market_category=market.category,
                        current_probability=current_prob,
                        include_similar=False  # Skip for speed
                    )
                )
                
                result = asyncio.run(
                    synthesizer.analyze_market(
                        market_id=market.id,
                        market_question=market.question,
                        market_description=market.description or "",
                        category=market.category or "general",
                        resolution_criteria=market.resolution_criteria or "",
                        current_probability=current_prob,
                        volume=0,
                        closes_at=market.closes_at,
                        data_bundle=data_bundle,
                        tier=AnalysisTier.LIGHTWEIGHT
                    )
                )
                
                # Store lightweight result
                pred_factors = MarketPredictionFactors(
                    market_id=market.id,
                    agent_type=result.agent_id,
                    analysis_tier=1,
                    raw_probability=result.raw_probability,
                    calibrated_probability=result.calibrated_probability,
                    confidence=result.confidence,
                    probability_low=result.probability_low,
                    probability_high=result.probability_high,
                    key_factors=[f.to_dict() for f in result.key_factors],
                    risk_factors=[r.to_dict() for r in result.risk_factors],
                    data_sources=result.data_sources,
                    reasoning_chain=result.reasoning_chain,
                    summary=result.summary,
                    data_freshness_hours=result.data_freshness_hours
                )
                db.add(pred_factors)
                updated += 1
                
                # Check if tier 3 should be triggered
                if last_pred:
                    prob_shift = abs(result.calibrated_probability - last_pred.calibrated_probability)
                    if prob_shift > 0.10:  # >10% shift
                        logger.info(
                            f"Market {market.id} had {prob_shift:.1%} shift, triggering tier3"
                        )
                        tier3_deep_analysis.delay(market.id)
                        triggered_tier3 += 1
                
            except Exception as e:
                logger.warning(f"Tier1 failed for market {market.id}: {e}")
                continue
        
        db.commit()
        logger.info(f"Tier 1 complete: {updated} updated, {triggered_tier3} triggered tier3")
        
        return {
            "updated": updated,
            "triggered_tier3": triggered_tier3,
            "total": len(markets)
        }
        
    except Exception as e:
        logger.error(f"Error in tier1_lightweight_update: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@shared_task(name="app.tasks.market_intelligence.tier2_daily_analysis")
def tier2_daily_analysis():
    """
    Tier 2 - Full daily analysis for all open markets.
    
    Runs once per day to:
    - Full multi-agent synthesis with Claude Sonnet
    - Update calibrated probabilities
    - Refresh key factors and risk assessment
    
    Cost: ~$0.05-0.10 per market
    """
    from app.services.market_intelligence import MarketSynthesizer, CalibrationTracker
    from app.services.market_intelligence.models import AnalysisTier
    from app.services.data_aggregation import DataAggregator
    
    db = SessionLocal()
    try:
        markets = db.query(Market).filter(
            Market.status == MarketStatus.OPEN
        ).all()
        
        if not markets:
            return {"analyzed": 0}
        
        logger.info(f"Tier 2 daily analysis for {len(markets)} markets...")
        
        synthesizer = MarketSynthesizer()
        calibration = CalibrationTracker(db)
        aggregator = DataAggregator(db)
        analyzed = 0
        
        for market in markets:
            try:
                total_liq = market.yes_liquidity + market.no_liquidity
                current_prob = market.yes_liquidity / total_liq if total_liq > 0 else 0.5
                
                # Full data aggregation including similar markets
                data_bundle = asyncio.run(
                    aggregator.get_market_data(
                        market_id=market.id,
                        market_question=market.question,
                        market_category=market.category,
                        current_probability=current_prob,
                        news_hours=48,  # Longer window for daily
                        sentiment_hours=48,
                        include_similar=True
                    )
                )
                
                # Full synthesis
                result = asyncio.run(
                    synthesizer.analyze_market(
                        market_id=market.id,
                        market_question=market.question,
                        market_description=market.description or "",
                        category=market.category or "general",
                        resolution_criteria=market.resolution_criteria or "",
                        current_probability=current_prob,
                        volume=0,
                        closes_at=market.closes_at,
                        data_bundle=data_bundle,
                        tier=AnalysisTier.DAILY
                    )
                )
                
                # Apply calibration
                calibrated_prob = calibration.adjust_probability(
                    result.raw_probability,
                    result.agent_id
                )
                
                # Store results
                pred_factors = MarketPredictionFactors(
                    market_id=market.id,
                    agent_type=result.agent_id,
                    analysis_tier=2,
                    raw_probability=result.raw_probability,
                    calibrated_probability=calibrated_prob,
                    confidence=result.confidence,
                    probability_low=result.probability_low,
                    probability_high=result.probability_high,
                    key_factors=[f.to_dict() for f in result.key_factors],
                    risk_factors=[r.to_dict() for r in result.risk_factors],
                    data_sources=result.data_sources,
                    reasoning_chain=result.reasoning_chain,
                    summary=result.summary,
                    data_freshness_hours=result.data_freshness_hours
                )
                db.add(pred_factors)
                
                # Record prediction for calibration
                calibration.record_prediction(
                    market_id=market.id,
                    agent_id=result.agent_id,
                    predicted_probability=calibrated_prob
                )
                
                analyzed += 1
                
            except Exception as e:
                logger.error(f"Tier2 failed for market {market.id}: {e}")
                continue
        
        db.commit()
        logger.info(f"Tier 2 complete: {analyzed}/{len(markets)} analyzed")
        
        return {"analyzed": analyzed, "total": len(markets)}
        
    except Exception as e:
        logger.error(f"Error in tier2_daily_analysis: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@shared_task(name="app.tasks.market_intelligence.tier3_deep_analysis")
def tier3_deep_analysis(market_id: int):
    """
    Tier 3 - On-demand deep analysis for a specific market.
    
    Triggered by:
    - Probability shift >10%
    - User request for detailed analysis
    - Breaking news detected
    - New market creation
    
    Cost: ~$0.20-0.30 per analysis
    """
    from app.services.market_intelligence import MarketSynthesizer, CalibrationTracker
    from app.services.market_intelligence.models import AnalysisTier
    from app.services.data_aggregation import DataAggregator
    
    db = SessionLocal()
    try:
        market = db.query(Market).filter(Market.id == market_id).first()
        
        if not market:
            logger.warning(f"Market {market_id} not found for tier3 analysis")
            return {"error": "Market not found"}
        
        logger.info(f"Tier 3 deep analysis for market {market_id}: {market.question[:50]}...")
        
        synthesizer = MarketSynthesizer()
        calibration = CalibrationTracker(db)
        aggregator = DataAggregator(db)
        
        total_liq = market.yes_liquidity + market.no_liquidity
        current_prob = market.yes_liquidity / total_liq if total_liq > 0 else 0.5
        
        # Extended data aggregation
        data_bundle = asyncio.run(
            aggregator.get_market_data(
                market_id=market.id,
                market_question=market.question,
                market_category=market.category,
                current_probability=current_prob,
                news_hours=72,  # 3 days of news
                sentiment_hours=48,
                include_similar=True,
                similar_count=10  # More similar markets
            )
        )
        
        # Deep synthesis
        result = asyncio.run(
            synthesizer.analyze_market(
                market_id=market.id,
                market_question=market.question,
                market_description=market.description or "",
                category=market.category or "general",
                resolution_criteria=market.resolution_criteria or "",
                current_probability=current_prob,
                volume=0,
                closes_at=market.closes_at,
                data_bundle=data_bundle,
                tier=AnalysisTier.DEEP
            )
        )
        
        # Apply calibration
        calibrated_prob = calibration.adjust_probability(
            result.raw_probability,
            result.agent_id
        )
        
        # Store results
        pred_factors = MarketPredictionFactors(
            market_id=market.id,
            agent_type=result.agent_id,
            analysis_tier=3,
            raw_probability=result.raw_probability,
            calibrated_probability=calibrated_prob,
            confidence=result.confidence,
            probability_low=result.probability_low,
            probability_high=result.probability_high,
            key_factors=[f.to_dict() for f in result.key_factors],
            risk_factors=[r.to_dict() for r in result.risk_factors],
            data_sources=result.data_sources,
            reasoning_chain=result.reasoning_chain,
            summary=result.summary,
            data_freshness_hours=result.data_freshness_hours
        )
        db.add(pred_factors)
        
        # Record prediction
        calibration.record_prediction(
            market_id=market.id,
            agent_id=result.agent_id,
            predicted_probability=calibrated_prob
        )
        
        db.commit()
        
        logger.info(
            f"Tier 3 complete for {market_id}: "
            f"prob={calibrated_prob:.2f}, conf={result.confidence:.2f}"
        )
        
        return {
            "market_id": market_id,
            "probability": calibrated_prob,
            "confidence": result.confidence,
            "key_factors_count": len(result.key_factors),
            "risk_factors_count": len(result.risk_factors)
        }
        
    except Exception as e:
        logger.error(f"Error in tier3_deep_analysis for {market_id}: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@shared_task(name="app.tasks.market_intelligence.update_calibration_on_resolution")
def update_calibration_on_resolution(market_id: int, outcome: str):
    """
    Update calibration scores when a market resolves.
    
    Called after a market is resolved to:
    - Calculate Brier scores for all agents that predicted
    - Update agent performance tracking
    """
    from app.services.market_intelligence import CalibrationTracker
    
    db = SessionLocal()
    try:
        calibration = CalibrationTracker(db)
        calibration.record_resolution(market_id, outcome)
        
        logger.info(f"Calibration updated for market {market_id} resolution: {outcome}")
        return {"market_id": market_id, "outcome": outcome, "success": True}
        
    except Exception as e:
        logger.error(f"Error updating calibration for {market_id}: {e}")
        return {"error": str(e)}
    finally:
        db.close()


# =============================================================================
# Original Tasks (kept for compatibility)
# =============================================================================


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
