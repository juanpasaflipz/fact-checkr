"""
Market Intelligence Router

API endpoints for AI-powered market predictions and analysis.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import Market, MarketPredictionFactors, AgentPerformance
from app.services.market_intelligence import (
    MarketSynthesizer,
    CalibrationTracker,
    MarketSimilarityEngine,
)
from app.services.market_intelligence.models import AnalysisTier
from app.services.data_aggregation import DataAggregator

router = APIRouter(prefix="/api/markets", tags=["market-intelligence"])


class KeyFactorResponse(BaseModel):
    factor: str
    impact: float
    confidence: float
    source: str
    evidence: Optional[str] = None


class RiskFactorResponse(BaseModel):
    risk: str
    severity: str
    probability: float
    impact_on_prediction: str


class PredictionFactorsResponse(BaseModel):
    market_id: int
    agent_type: str
    analysis_tier: int
    raw_probability: float
    calibrated_probability: float
    confidence: float
    probability_low: Optional[float]
    probability_high: Optional[float]
    key_factors: List[KeyFactorResponse]
    risk_factors: List[RiskFactorResponse]
    data_sources: Dict[str, Any]
    reasoning_chain: Optional[str]
    summary: Optional[str]
    data_freshness_hours: float
    created_at: str


class SimilarMarketResponse(BaseModel):
    market_id: int
    question: str
    category: Optional[str]
    outcome: str
    final_probability: float
    similarity_score: float
    resolution_date: Optional[str]


class MarketIntelligenceResponse(BaseModel):
    prediction: Optional[PredictionFactorsResponse]
    similar_markets: List[SimilarMarketResponse]
    sentiment_data: Optional[Dict[str, Any]]
    news_data: Optional[Dict[str, Any]]
    data_quality_score: float


@router.get("/{market_id}/prediction")
async def get_market_prediction(
    market_id: int,
    db: Session = Depends(get_db)
) -> Optional[PredictionFactorsResponse]:
    """
    Get the latest AI prediction for a market.
    
    Returns the most recent prediction factors from the synthesizer agent.
    """
    # Get market
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Mercado no encontrado")
    
    # Get latest prediction factors
    prediction = db.query(MarketPredictionFactors).filter(
        MarketPredictionFactors.market_id == market_id
    ).order_by(MarketPredictionFactors.created_at.desc()).first()
    
    if not prediction:
        return None
    
    # Parse JSON factors
    key_factors = []
    if prediction.key_factors:
        for f in prediction.key_factors:
            key_factors.append(KeyFactorResponse(
                factor=f.get("factor", ""),
                impact=f.get("impact", 0),
                confidence=f.get("confidence", 0),
                source=f.get("source", "unknown"),
                evidence=f.get("evidence")
            ))
    
    risk_factors = []
    if prediction.risk_factors:
        for r in prediction.risk_factors:
            risk_factors.append(RiskFactorResponse(
                risk=r.get("risk", ""),
                severity=r.get("severity", "medium"),
                probability=r.get("probability", 0),
                impact_on_prediction=r.get("impact_on_prediction", "")
            ))
    
    return PredictionFactorsResponse(
        market_id=prediction.market_id,
        agent_type=prediction.agent_type,
        analysis_tier=prediction.analysis_tier,
        raw_probability=prediction.raw_probability,
        calibrated_probability=prediction.calibrated_probability,
        confidence=prediction.confidence,
        probability_low=prediction.probability_low,
        probability_high=prediction.probability_high,
        key_factors=key_factors,
        risk_factors=risk_factors,
        data_sources=prediction.data_sources or {},
        reasoning_chain=prediction.reasoning_chain,
        summary=prediction.summary,
        data_freshness_hours=prediction.data_freshness_hours or 24.0,
        created_at=prediction.created_at.isoformat()
    )


@router.get("/{market_id}/intelligence")
async def get_market_intelligence(
    market_id: int,
    db: Session = Depends(get_db)
) -> MarketIntelligenceResponse:
    """
    Get comprehensive intelligence data for a market.
    
    Includes prediction, similar markets, sentiment, and news data.
    """
    # Get market
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Mercado no encontrado")
    
    # Get prediction
    prediction = None
    pred_record = db.query(MarketPredictionFactors).filter(
        MarketPredictionFactors.market_id == market_id
    ).order_by(MarketPredictionFactors.created_at.desc()).first()
    
    if pred_record:
        key_factors = []
        if pred_record.key_factors:
            for f in pred_record.key_factors:
                key_factors.append(KeyFactorResponse(
                    factor=f.get("factor", ""),
                    impact=f.get("impact", 0),
                    confidence=f.get("confidence", 0),
                    source=f.get("source", "unknown"),
                    evidence=f.get("evidence")
                ))
        
        risk_factors = []
        if pred_record.risk_factors:
            for r in pred_record.risk_factors:
                risk_factors.append(RiskFactorResponse(
                    risk=r.get("risk", ""),
                    severity=r.get("severity", "medium"),
                    probability=r.get("probability", 0),
                    impact_on_prediction=r.get("impact_on_prediction", "")
                ))
        
        prediction = PredictionFactorsResponse(
            market_id=pred_record.market_id,
            agent_type=pred_record.agent_type,
            analysis_tier=pred_record.analysis_tier,
            raw_probability=pred_record.raw_probability,
            calibrated_probability=pred_record.calibrated_probability,
            confidence=pred_record.confidence,
            probability_low=pred_record.probability_low,
            probability_high=pred_record.probability_high,
            key_factors=key_factors,
            risk_factors=risk_factors,
            data_sources=pred_record.data_sources or {},
            reasoning_chain=pred_record.reasoning_chain,
            summary=pred_record.summary,
            data_freshness_hours=pred_record.data_freshness_hours or 24.0,
            created_at=pred_record.created_at.isoformat()
        )
    
    # Get similar markets
    similarity_engine = MarketSimilarityEngine(db)
    similar = similarity_engine.find_similar_resolved_markets(
        market_question=market.question,
        category=market.category,
        top_k=5
    )
    
    similar_markets = [
        SimilarMarketResponse(
            market_id=m.market_id,
            question=m.question,
            category=m.category,
            outcome=m.outcome,
            final_probability=m.final_probability,
            similarity_score=m.similarity_score,
            resolution_date=m.resolution_date.isoformat() if m.resolution_date else None
        )
        for m in similar
    ]
    
    # Get sentiment and news data from prediction factors or fetch fresh
    sentiment_data = None
    news_data = None
    
    if pred_record and pred_record.data_sources:
        # Extract sentiment and news from data_sources if available
        data_sources = pred_record.data_sources
        if isinstance(data_sources, dict):
            sentiment_data = data_sources.get("sentiment")
            news_data = data_sources.get("news")
    
    # Only fetch fresh data if we're missing specific pieces, not everything
    if not sentiment_data or not news_data:
        try:
            # Get current probability
            total_liquidity = market.yes_liquidity + market.no_liquidity
            current_prob = market.yes_liquidity / total_liquidity if total_liquidity > 0 else 0.5
            
            # Fetch fresh data using await (we're already in an async context)
            aggregator = DataAggregator(db)
            data_bundle = await aggregator.get_market_data(
                market_id=market.id,
                market_question=market.question,
                market_category=market.category,
                current_probability=current_prob,
                include_similar=False
            )
            
            # Only extract missing data, preserve cached data
            if not sentiment_data and hasattr(data_bundle, 'sentiment') and data_bundle.sentiment:
                sentiment_data = {
                    "posts_analyzed": getattr(data_bundle.sentiment, 'posts_analyzed', 0),
                    "weighted_sentiment": getattr(data_bundle.sentiment, 'weighted_sentiment', 0.0),
                    "raw_sentiment": getattr(data_bundle.sentiment, 'raw_sentiment', 0.0),
                    "sentiment_confidence": getattr(data_bundle.sentiment, 'sentiment_confidence', 0.0),
                    "momentum": getattr(data_bundle.sentiment, 'momentum', 0.0),
                    "volume_trend": getattr(data_bundle.sentiment, 'volume_trend', 0.0),
                    "platform_breakdown": getattr(data_bundle.sentiment, 'platform_breakdown', {}),
                    "freshness_hours": getattr(data_bundle.sentiment, 'freshness_hours', 24.0),
                    "bot_filtered_count": getattr(data_bundle.sentiment, 'bot_filtered_count', 0)
                }
            
            if not news_data and hasattr(data_bundle, 'news') and data_bundle.news:
                news_data = {
                    "volume": getattr(data_bundle.news, 'volume', 0),
                    "overall_signal": getattr(data_bundle.news, 'overall_signal', 0.0),
                    "credibility_weighted_signal": getattr(data_bundle.news, 'credibility_weighted_signal', 0.0),
                    "freshness_hours": getattr(data_bundle.news, 'freshness_hours', 24.0)
                }
        except Exception as e:
            # Log error but don't fail the request
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error fetching fresh sentiment/news data for market {market_id}: {e}")
    
    # Calculate data quality
    data_quality = 0.0
    if prediction:
        data_quality += 0.4
        if prediction.confidence > 0.7:
            data_quality += 0.2
    if similar_markets:
        data_quality += 0.2
    if sentiment_data:
        data_quality += 0.1
    if news_data:
        data_quality += 0.1
    
    return MarketIntelligenceResponse(
        prediction=prediction,
        similar_markets=similar_markets,
        sentiment_data=sentiment_data,
        news_data=news_data,
        data_quality_score=data_quality
    )


@router.post("/{market_id}/analyze")
async def trigger_market_analysis(
    market_id: int,
    background_tasks: BackgroundTasks,
    tier: int = 2,
    db: Session = Depends(get_db)
):
    """
    Trigger a new AI analysis for a market.
    
    This runs in the background and stores results in the database.
    
    Tiers:
    - 1: Lightweight (fast, no LLM)
    - 2: Daily analysis (full synthesis)
    - 3: Deep analysis (detailed reasoning)
    """
    # Get market
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Mercado no encontrado")
    
    if market.status != "open":
        raise HTTPException(status_code=400, detail="El mercado no está abierto")
    
    # Queue background analysis
    background_tasks.add_task(
        run_market_analysis,
        market_id=market_id,
        tier=tier
    )
    
    return {
        "message": "Análisis iniciado",
        "market_id": market_id,
        "tier": tier
    }


async def run_market_analysis(market_id: int, tier: int = 2):
    """Background task to run market analysis."""
    from app.database.connection import SessionLocal
    
    db = SessionLocal()
    try:
        market = db.query(Market).filter(Market.id == market_id).first()
        if not market:
            return
        
        # Get current probability from liquidity
        total_liquidity = market.yes_liquidity + market.no_liquidity
        current_prob = market.yes_liquidity / total_liquidity if total_liquidity > 0 else 0.5
        
        # Create aggregator and synthesizer
        aggregator = DataAggregator(db)
        synthesizer = MarketSynthesizer()
        
        # Get data bundle
        data_bundle = await aggregator.get_market_data(
            market_id=market_id,
            market_question=market.question,
            market_category=market.category,
            current_probability=current_prob
        )
        
        # Determine analysis tier
        analysis_tier = AnalysisTier(tier)
        
        # Run synthesis
        result = await synthesizer.analyze_market(
            market_id=market_id,
            market_question=market.question,
            market_description=market.description or "",
            category=market.category or "general",
            resolution_criteria=market.resolution_criteria or "",
            current_probability=current_prob,
            volume=0,  # Would calculate from trades
            closes_at=market.closes_at,
            data_bundle=data_bundle,
            tier=analysis_tier
        )
        
        # Apply calibration
        calibration = CalibrationTracker(db)
        calibrated_prob = calibration.adjust_probability(
            result.raw_probability,
            result.agent_id
        )
        
        # Store results
        prediction_factors = MarketPredictionFactors(
            market_id=market_id,
            agent_type=result.agent_id,
            analysis_tier=tier,
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
        
        db.add(prediction_factors)
        
        # Record prediction for calibration tracking
        calibration.record_prediction(
            market_id=market_id,
            agent_id=result.agent_id,
            predicted_probability=calibrated_prob
        )
        
        db.commit()
        
    except Exception as e:
        import logging
        logging.error(f"Market analysis failed for {market_id}: {e}")
        db.rollback()
    finally:
        db.close()


@router.get("/calibration/{agent_id}")
async def get_agent_calibration(
    agent_id: str,
    days: int = 90,
    db: Session = Depends(get_db)
):
    """
    Get calibration metrics for an agent.
    
    Returns Brier score, calibration curve, and related stats.
    """
    tracker = CalibrationTracker(db)
    report = tracker.get_calibration_report(agent_id, days)
    
    return {
        "agent_id": report.agent_id,
        "brier_score": report.brier_score,
        "calibration_error": report.calibration_error,
        "num_predictions": report.num_predictions,
        "num_resolved": report.num_resolved,
        "overconfidence_bias": report.overconfidence_bias,
        "time_period_days": report.time_period_days,
        "buckets": [
            {
                "range": f"{b.predicted_low:.0%}-{b.predicted_high:.0%}",
                "predicted_avg": b.predicted_avg,
                "actual_frequency": b.actual_frequency,
                "count": b.count,
                "calibration_error": b.calibration_error
            }
            for b in report.buckets
        ]
    }
