"""
Market Intelligence Service

Multi-agent prediction system for prediction markets with:
- Synthesizer agent for market analysis
- Calibration system for accuracy tracking
- Market similarity engine for bootstrapping new markets
- Data aggregation from multiple sources
"""

from .synthesizer import MarketSynthesizer
from .calibration import CalibrationTracker
from .market_similarity import MarketSimilarityEngine
from .models import (
    PredictionResult,
    NewsAggregation,
    SentimentAggregation,
    MarketDataBundle,
    KeyFactor,
    RiskFactor,
)

__all__ = [
    "MarketSynthesizer",
    "CalibrationTracker", 
    "MarketSimilarityEngine",
    "PredictionResult",
    "NewsAggregation",
    "SentimentAggregation",
    "MarketDataBundle",
    "KeyFactor",
    "RiskFactor",
]
