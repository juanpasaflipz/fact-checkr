"""
Data models for market intelligence system.

These models define the structure of data flowing through the
prediction pipeline - from data aggregation to final prediction output.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class AnalysisTier(Enum):
    """Analysis depth tiers for cost optimization."""
    LIGHTWEIGHT = 1  # Every 1-2 hours, no LLM
    DAILY = 2        # Once per day, full synthesis
    DEEP = 3         # On-demand, detailed analysis


class RiskLevel(Enum):
    """Risk level classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class KeyFactor:
    """A key factor influencing the prediction."""
    factor: str
    impact: float  # -1 to 1, negative = supports NO, positive = supports YES
    confidence: float  # 0 to 1
    source: str  # "news", "social", "historical", "economic", "political"
    evidence: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor": self.factor,
            "impact": self.impact,
            "confidence": self.confidence,
            "source": self.source,
            "evidence": self.evidence
        }


@dataclass
class RiskFactor:
    """A risk factor that adds uncertainty to the prediction."""
    risk: str
    severity: RiskLevel
    probability: float  # 0 to 1, likelihood this risk materializes
    impact_on_prediction: str  # Description of how it affects the prediction
    mitigation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk": self.risk,
            "severity": self.severity.value,
            "probability": self.probability,
            "impact_on_prediction": self.impact_on_prediction,
            "mitigation": self.mitigation
        }


@dataclass
class NewsArticle:
    """A single news article with analysis."""
    title: str
    url: str
    source: str
    published_at: Optional[datetime]
    summary: str
    stance: float  # -1 to 1, negative = opposes, positive = supports market question
    credibility_score: float  # 0 to 1
    relevance_score: float  # 0 to 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "summary": self.summary,
            "stance": self.stance,
            "credibility_score": self.credibility_score,
            "relevance_score": self.relevance_score
        }


@dataclass
class NewsAggregation:
    """Aggregated news data for a market."""
    articles: List[NewsArticle]
    overall_signal: float  # -1 to 1
    volume: int  # Number of articles
    velocity: float  # Articles per hour
    credibility_weighted_signal: float  # Signal weighted by source credibility
    freshness_hours: float  # Age of newest article
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "articles": [a.to_dict() for a in self.articles[:10]],  # Limit to top 10
            "overall_signal": self.overall_signal,
            "volume": self.volume,
            "velocity": self.velocity,
            "credibility_weighted_signal": self.credibility_weighted_signal,
            "freshness_hours": self.freshness_hours
        }


@dataclass
class SocialPost:
    """A single social media post with analysis."""
    platform: str
    content: str
    author: str
    author_credibility: float  # 0 to 1
    engagement_score: float  # Normalized engagement
    sentiment: float  # -1 to 1
    timestamp: datetime
    url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "content": self.content[:200],  # Truncate
            "author": self.author,
            "author_credibility": self.author_credibility,
            "engagement_score": self.engagement_score,
            "sentiment": self.sentiment,
            "timestamp": self.timestamp.isoformat(),
            "url": self.url
        }


@dataclass  
class SentimentAggregation:
    """Aggregated social media sentiment for a market."""
    posts_analyzed: int
    weighted_sentiment: float  # -1 to 1, weighted by credibility and engagement
    raw_sentiment: float  # -1 to 1, unweighted average
    sentiment_confidence: float  # 0 to 1, based on volume and agreement
    momentum: float  # -1 to 1, sentiment trend direction
    volume_trend: float  # -1 to 1, post volume trend
    top_posts: List[SocialPost]
    platform_breakdown: Dict[str, float]  # Platform -> sentiment
    freshness_hours: float
    bot_filtered_count: int  # Number of posts filtered as potential bots
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "posts_analyzed": self.posts_analyzed,
            "weighted_sentiment": self.weighted_sentiment,
            "raw_sentiment": self.raw_sentiment,
            "sentiment_confidence": self.sentiment_confidence,
            "momentum": self.momentum,
            "volume_trend": self.volume_trend,
            "top_posts": [p.to_dict() for p in self.top_posts[:5]],
            "platform_breakdown": self.platform_breakdown,
            "freshness_hours": self.freshness_hours,
            "bot_filtered_count": self.bot_filtered_count
        }


@dataclass
class SimilarMarket:
    """A similar historical market for reference."""
    market_id: int
    question: str
    category: str
    outcome: str  # "yes" or "no"
    final_probability: float  # Final probability before resolution
    similarity_score: float  # 0 to 1
    resolution_date: Optional[datetime]
    key_factors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "market_id": self.market_id,
            "question": self.question,
            "category": self.category,
            "outcome": self.outcome,
            "final_probability": self.final_probability,
            "similarity_score": self.similarity_score,
            "resolution_date": self.resolution_date.isoformat() if self.resolution_date else None,
            "key_factors": self.key_factors
        }


@dataclass
class MarketDataBundle:
    """Complete data bundle for market analysis."""
    news: Optional[NewsAggregation] = None
    sentiment: Optional[SentimentAggregation] = None
    similar_markets: List[SimilarMarket] = field(default_factory=list)
    market_liquidity_signal: float = 0.0  # Current market probability from liquidity
    data_quality_score: float = 0.0  # 0 to 1, overall data quality
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "news": self.news.to_dict() if self.news else None,
            "sentiment": self.sentiment.to_dict() if self.sentiment else None,
            "similar_markets": [m.to_dict() for m in self.similar_markets],
            "market_liquidity_signal": self.market_liquidity_signal,
            "data_quality_score": self.data_quality_score
        }


@dataclass
class PredictionResult:
    """
    Complete prediction output from the synthesizer.
    
    This is the main output of market analysis, containing:
    - Raw and calibrated probability estimates
    - Confidence intervals
    - Key factors and risks
    - Full reasoning chain for transparency
    """
    # Core prediction
    raw_probability: float  # 0 to 1, raw model output
    calibrated_probability: float  # 0 to 1, adjusted for historical accuracy
    confidence: float  # 0 to 1, how confident the model is
    
    # Confidence interval (95%)
    probability_low: float  # Lower bound
    probability_high: float  # Upper bound
    
    # Factors
    key_factors: List[KeyFactor]
    risk_factors: List[RiskFactor]
    
    # Data sources used
    data_sources: Dict[str, Any]
    data_freshness_hours: float
    
    # Reasoning
    reasoning_chain: str  # Full reasoning for transparency
    summary: str  # Human-readable summary
    
    # Metadata
    analysis_tier: AnalysisTier
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_probability": self.raw_probability,
            "calibrated_probability": self.calibrated_probability,
            "confidence": self.confidence,
            "probability_low": self.probability_low,
            "probability_high": self.probability_high,
            "key_factors": [f.to_dict() for f in self.key_factors],
            "risk_factors": [r.to_dict() for r in self.risk_factors],
            "data_sources": self.data_sources,
            "data_freshness_hours": self.data_freshness_hours,
            "reasoning_chain": self.reasoning_chain,
            "summary": self.summary,
            "analysis_tier": self.analysis_tier.value,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat()
        }
    
    def get_explanation(self) -> str:
        """Generate human-readable explanation for display."""
        conf_pct = int(self.confidence * 100)
        prob_pct = int(self.calibrated_probability * 100)
        
        # Determine stance
        if self.calibrated_probability > 0.6:
            stance = "SÍ como probable"
        elif self.calibrated_probability < 0.4:
            stance = "NO como probable"
        else:
            stance = "el resultado como incierto"
        
        # Get top factors
        top_factors = sorted(self.key_factors, key=lambda x: abs(x.impact), reverse=True)[:2]
        factors_text = " y ".join([f.factor for f in top_factors]) if top_factors else "múltiples factores"
        
        # Get top risk
        top_risk = max(self.risk_factors, key=lambda x: x.probability, default=None)
        risk_text = f" Sin embargo, señalamos '{top_risk.risk}' como riesgo." if top_risk else ""
        
        return (
            f"Nuestro análisis ({conf_pct}% confianza) ve {stance} "
            f"debido a {factors_text}.{risk_text} "
            f"Probabilidad estimada: {prob_pct}% "
            f"(rango: {int(self.probability_low*100)}-{int(self.probability_high*100)}%)."
        )
