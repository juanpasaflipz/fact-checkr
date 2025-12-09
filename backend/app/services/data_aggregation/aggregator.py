"""
Data Aggregator

Unified interface for aggregating data from all sources
(news, social media, etc.) for market predictions.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy.orm import Session

from app.services.market_intelligence.models import (
    MarketDataBundle,
    NewsAggregation,
    SentimentAggregation,
    SimilarMarket,
)
from .news_analyzer import NewsAnalyzer
from .twitter_sentiment import TwitterSentimentAnalyzer

logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Unified interface for collecting data from all sources.
    
    Coordinates:
    - News aggregation (via NewsAnalyzer)
    - Social sentiment (via TwitterSentimentAnalyzer)
    - Similar market lookup (via MarketSimilarityEngine)
    
    Provides a single entry point for market analysis.
    """
    
    def __init__(self, db: Session = None):
        self.db = db
        self.news_analyzer = NewsAnalyzer()
        self.sentiment_analyzer = TwitterSentimentAnalyzer(db)
    
    async def get_market_data(
        self,
        market_id: int,
        market_question: str,
        market_category: str = None,
        current_probability: float = 0.5,
        news_hours: int = 24,
        sentiment_hours: int = 24,
        include_similar: bool = True,
        similar_count: int = 5
    ) -> MarketDataBundle:
        """
        Aggregate all data for a market prediction.
        
        Args:
            market_id: Market identifier
            market_question: The market question
            market_category: Market category for focused search
            current_probability: Current market probability from liquidity
            news_hours: Hours of news to aggregate
            sentiment_hours: Hours of social data to aggregate
            include_similar: Whether to find similar markets
            similar_count: Number of similar markets to find
        
        Returns:
            MarketDataBundle with all aggregated data
        """
        logger.info(f"Aggregating data for market {market_id}: {market_question[:50]}...")
        
        # Run aggregations in parallel
        tasks = [
            self._aggregate_news(market_question, market_category, news_hours),
            self._aggregate_sentiment(market_question, sentiment_hours),
        ]
        
        if include_similar:
            tasks.append(
                self._find_similar_markets(market_question, market_category, similar_count)
            )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Extract results
        news_data = results[0] if not isinstance(results[0], Exception) else None
        sentiment_data = results[1] if not isinstance(results[1], Exception) else None
        similar_markets = results[2] if len(results) > 2 and not isinstance(results[2], Exception) else []
        
        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Data aggregation task {i} failed: {result}")
        
        # Calculate data quality score
        quality_score = self._calculate_quality_score(
            news_data, sentiment_data, similar_markets
        )
        
        return MarketDataBundle(
            news=news_data,
            sentiment=sentiment_data,
            similar_markets=similar_markets,
            market_liquidity_signal=current_probability,
            data_quality_score=quality_score
        )
    
    async def _aggregate_news(
        self,
        market_question: str,
        category: str,
        hours: int
    ) -> Optional[NewsAggregation]:
        """Aggregate news data."""
        try:
            return await self.news_analyzer.aggregate_news_for_market(
                market_question=market_question,
                market_category=category,
                hours=hours
            )
        except Exception as e:
            logger.error(f"News aggregation failed: {e}")
            return None
    
    async def _aggregate_sentiment(
        self,
        market_question: str,
        hours: int
    ) -> Optional[SentimentAggregation]:
        """Aggregate social media sentiment."""
        try:
            return await self.sentiment_analyzer.analyze_sentiment_for_market(
                market_question=market_question,
                hours=hours
            )
        except Exception as e:
            logger.error(f"Sentiment aggregation failed: {e}")
            return None
    
    async def _find_similar_markets(
        self,
        market_question: str,
        category: str,
        count: int
    ) -> List[SimilarMarket]:
        """Find similar historical markets."""
        try:
            from app.services.market_intelligence.market_similarity import MarketSimilarityEngine
            
            if not self.db:
                return []
            
            similarity_engine = MarketSimilarityEngine(self.db)
            return similarity_engine.find_similar_resolved_markets(
                market_question=market_question,
                category=category,
                top_k=count
            )
        except Exception as e:
            logger.error(f"Similar market search failed: {e}")
            return []
    
    def _calculate_quality_score(
        self,
        news: Optional[NewsAggregation],
        sentiment: Optional[SentimentAggregation],
        similar_markets: List[SimilarMarket]
    ) -> float:
        """
        Calculate overall data quality score.
        
        Based on:
        - Data availability
        - Data freshness
        - Volume of data
        """
        score = 0.0
        max_score = 0.0
        
        # News quality (40% weight)
        max_score += 0.4
        if news and news.volume > 0:
            # Volume factor (more articles = better)
            volume_factor = min(1.0, news.volume / 10)
            # Freshness factor
            freshness_factor = max(0.0, 1.0 - news.freshness_hours / 48)
            # Credibility factor
            credibility_factor = min(1.0, abs(news.credibility_weighted_signal) + 0.5)
            
            score += 0.4 * (volume_factor * 0.4 + freshness_factor * 0.3 + credibility_factor * 0.3)
        
        # Sentiment quality (35% weight)
        max_score += 0.35
        if sentiment and sentiment.posts_analyzed > 0:
            # Volume factor
            volume_factor = min(1.0, sentiment.posts_analyzed / 50)
            # Confidence factor
            confidence_factor = sentiment.sentiment_confidence
            # Freshness factor
            freshness_factor = max(0.0, 1.0 - sentiment.freshness_hours / 24)
            
            score += 0.35 * (volume_factor * 0.4 + confidence_factor * 0.3 + freshness_factor * 0.3)
        
        # Similar markets quality (25% weight)
        max_score += 0.25
        if similar_markets:
            # Number of similar markets
            count_factor = min(1.0, len(similar_markets) / 5)
            # Average similarity
            avg_similarity = sum(m.similarity_score for m in similar_markets) / len(similar_markets)
            
            score += 0.25 * (count_factor * 0.5 + avg_similarity * 0.5)
        
        return score / max_score if max_score > 0 else 0.0
    
    async def get_lightweight_signals(
        self,
        market_id: int,
        market_question: str,
        current_probability: float
    ) -> Dict[str, Any]:
        """
        Get lightweight signals for Tier 1 analysis.
        
        Fast, no LLM calls. Just retrieves recent data counts
        and simple metrics for quick updates.
        """
        signals = {
            "market_id": market_id,
            "timestamp": datetime.utcnow().isoformat(),
            "current_probability": current_probability,
            "news_volume_24h": 0,
            "sentiment_posts_24h": 0,
            "sentiment_signal": 0.0,
            "news_signal": 0.0,
        }
        
        try:
            # Quick news volume check (no analysis)
            # Just count relevant articles in last 24h
            # This would be a fast database/cache lookup in production
            signals["news_volume_24h"] = 5  # Placeholder
            
            # Quick sentiment signal
            if self.sentiment_analyzer._anchors_ready:
                # Could use cached sentiment if available
                signals["sentiment_posts_24h"] = 10  # Placeholder
                signals["sentiment_signal"] = 0.0  # Neutral placeholder
            
        except Exception as e:
            logger.warning(f"Lightweight signal collection failed: {e}")
        
        return signals


async def create_aggregator(db: Session = None) -> DataAggregator:
    """Factory function to create a DataAggregator."""
    return DataAggregator(db=db)
