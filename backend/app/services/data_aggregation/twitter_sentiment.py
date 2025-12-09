"""
Twitter Sentiment Analyzer

Embedding-based sentiment analysis for social media posts.
Fast and cheap - no LLM calls required.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.services.embeddings import EmbeddingService
from app.services.market_intelligence.models import (
    SentimentAggregation,
    SocialPost,
)
from .noise_filter import NoiseFilter, WeightedPost

logger = logging.getLogger(__name__)


# Sentiment anchor phrases for embedding comparison
# These are used to determine sentiment via cosine similarity
POSITIVE_ANCHORS = [
    "Esto es muy positivo y bueno",
    "Estoy de acuerdo, es verdad",
    "Excelente noticia, apoyo totalmente",
    "Esto va a mejorar las cosas",
    "Gran avance, muy bien",
    "Sí, esto es correcto",
    "Apruebo esta decisión",
]

NEGATIVE_ANCHORS = [
    "Esto es muy negativo y malo",
    "No estoy de acuerdo, es mentira",
    "Terrible noticia, rechazo totalmente", 
    "Esto va a empeorar las cosas",
    "Gran retroceso, muy mal",
    "No, esto es incorrecto",
    "Rechazo esta decisión",
]


class TwitterSentimentAnalyzer:
    """
    Embedding-based sentiment analysis for social media.
    
    Uses cosine similarity between post embeddings and sentiment
    anchor phrases to determine sentiment without LLM calls.
    
    Much faster and cheaper than LLM-based sentiment analysis.
    """
    
    def __init__(self, db: Session = None):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.noise_filter = NoiseFilter()
        
        # Pre-compute anchor embeddings (cached)
        self._positive_embedding = None
        self._negative_embedding = None
        self._anchors_ready = False
    
    def _ensure_anchors(self):
        """Ensure anchor embeddings are computed."""
        if self._anchors_ready:
            return
        
        try:
            # Combine anchors and get single embedding for each pole
            positive_text = " ".join(POSITIVE_ANCHORS)
            negative_text = " ".join(NEGATIVE_ANCHORS)
            
            self._positive_embedding = self.embedding_service.embed_text(positive_text)
            self._negative_embedding = self.embedding_service.embed_text(negative_text)
            
            if self._positive_embedding and self._negative_embedding:
                self._anchors_ready = True
                logger.info("✓ Sentiment anchors initialized")
            else:
                logger.warning("Could not initialize sentiment anchors")
        except Exception as e:
            logger.error(f"Error initializing sentiment anchors: {e}")
    
    async def analyze_sentiment_for_market(
        self,
        market_question: str,
        posts: List[Dict[str, Any]] = None,
        hours: int = 24,
        platforms: List[str] = None
    ) -> SentimentAggregation:
        """
        Analyze sentiment from social media posts for a market.
        
        Args:
            market_question: The market question for context
            posts: Pre-fetched posts (if None, will attempt to fetch)
            hours: Time window for posts
            platforms: Platforms to include (default: all)
        
        Returns:
            SentimentAggregation with weighted sentiment scores
        """
        # Ensure anchors are ready
        self._ensure_anchors()
        
        # If no posts provided, try to fetch them
        if posts is None:
            posts = await self._fetch_posts(market_question, hours, platforms)
        
        if not posts:
            return self._empty_aggregation()
        
        # Filter noise
        filtered_posts, bot_count = self.noise_filter.filter_posts(
            posts,
            min_credibility=0.3,
            check_coordination=True
        )
        
        if not filtered_posts:
            return self._empty_aggregation(bot_filtered=bot_count)
        
        # Calculate sentiment for each post
        for post in filtered_posts:
            sentiment = await self._calculate_post_sentiment(
                post.content,
                market_question
            )
            post.sentiment = sentiment
        
        # Aggregate results
        return self._aggregate_sentiment(filtered_posts, bot_count)
    
    async def _calculate_post_sentiment(
        self,
        post_content: str,
        market_question: str
    ) -> float:
        """
        Calculate sentiment of a post using embedding similarity.
        
        Compares post embedding to positive/negative anchor embeddings
        to determine sentiment direction and magnitude.
        
        Args:
            post_content: The post text
            market_question: Context for understanding stance
        
        Returns:
            Sentiment score from -1 (negative) to +1 (positive)
        """
        if not self._anchors_ready:
            return 0.0
        
        try:
            # Combine post with market question for context
            contextualized = f"Mercado: {market_question}\nOpinión: {post_content}"
            
            post_embedding = self.embedding_service.embed_text(contextualized[:1000])
            
            if not post_embedding:
                return 0.0
            
            # Calculate cosine similarity to each anchor
            positive_sim = self._cosine_similarity(post_embedding, self._positive_embedding)
            negative_sim = self._cosine_similarity(post_embedding, self._negative_embedding)
            
            # Convert similarities to sentiment score
            # Normalize to [-1, 1] range
            raw_sentiment = positive_sim - negative_sim
            
            # Scale and clamp
            sentiment = max(-1.0, min(1.0, raw_sentiment * 2))
            
            return sentiment
            
        except Exception as e:
            logger.warning(f"Error calculating post sentiment: {e}")
            return 0.0
    
    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def _fetch_posts(
        self,
        market_question: str,
        hours: int,
        platforms: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch relevant posts from database/scrapers.
        
        This connects to the existing scraping infrastructure.
        """
        try:
            from app.database.connection import SessionLocal
            from app.database.models import Source
            from sqlalchemy import desc
            
            db = SessionLocal()
            
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            # Query recent sources that might be relevant
            query = db.query(Source).filter(
                Source.timestamp >= cutoff
            )
            
            if platforms:
                query = query.filter(Source.platform.in_(platforms))
            
            # Limit for performance
            sources = query.order_by(desc(Source.timestamp)).limit(500).all()
            
            posts = []
            for source in sources:
                # Basic keyword relevance check
                content_lower = (source.content or "").lower()
                question_words = market_question.lower().split()
                
                # Skip if no keyword overlap
                if not any(word in content_lower for word in question_words[:5]):
                    continue
                
                posts.append({
                    "content": source.content,
                    "author": source.author or "unknown",
                    "platform": source.platform,
                    "timestamp": source.timestamp,
                    "url": source.url,
                    "engagement_metrics": source.engagement_metrics or {},
                    "author_metadata": source.author_metadata or {}
                })
            
            db.close()
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching posts: {e}")
            return []
    
    def _aggregate_sentiment(
        self,
        posts: List[WeightedPost],
        bot_filtered: int
    ) -> SentimentAggregation:
        """Aggregate sentiment from weighted posts."""
        if not posts:
            return self._empty_aggregation(bot_filtered=bot_filtered)
        
        # Calculate weighted sentiment
        total_weight = sum(p.combined_weight for p in posts)
        
        if total_weight > 0:
            weighted_sentiment = sum(
                p.sentiment * p.combined_weight 
                for p in posts
            ) / total_weight
        else:
            weighted_sentiment = 0.0
        
        # Raw average sentiment
        raw_sentiment = sum(p.sentiment for p in posts) / len(posts)
        
        # Sentiment confidence based on agreement and volume
        sentiment_variance = sum(
            (p.sentiment - raw_sentiment) ** 2 for p in posts
        ) / len(posts)
        
        # Higher variance = lower confidence
        # More posts = higher confidence
        volume_factor = min(1.0, len(posts) / 50)
        agreement_factor = 1.0 / (1.0 + sentiment_variance * 2)
        confidence = volume_factor * agreement_factor
        
        # Calculate momentum (sentiment trend)
        # Sort by timestamp and compare first half vs second half
        sorted_posts = sorted(posts, key=lambda p: p.timestamp)
        mid = len(sorted_posts) // 2
        
        if mid > 0:
            early_sentiment = sum(p.sentiment for p in sorted_posts[:mid]) / mid
            late_sentiment = sum(p.sentiment for p in sorted_posts[mid:]) / (len(sorted_posts) - mid)
            momentum = late_sentiment - early_sentiment
        else:
            momentum = 0.0
        
        # Volume trend (comparing to expected)
        volume_trend = 0.0  # Would need historical data
        
        # Platform breakdown
        platform_sentiments: Dict[str, List[float]] = {}
        for post in posts:
            if post.platform not in platform_sentiments:
                platform_sentiments[post.platform] = []
            platform_sentiments[post.platform].append(post.sentiment)
        
        platform_breakdown = {
            platform: sum(sents) / len(sents)
            for platform, sents in platform_sentiments.items()
        }
        
        # Get top posts by engagement
        top_posts = sorted(posts, key=lambda p: p.engagement_score, reverse=True)[:5]
        social_posts = [
            SocialPost(
                platform=p.platform,
                content=p.content[:300],
                author=p.author,
                author_credibility=p.credibility_weight,
                engagement_score=p.engagement_score,
                sentiment=p.sentiment,
                timestamp=p.timestamp
            )
            for p in top_posts
        ]
        
        # Freshness - time since oldest post in analysis
        oldest = min(p.timestamp for p in posts) if posts else datetime.utcnow()
        freshness = (datetime.utcnow() - oldest).total_seconds() / 3600
        
        return SentimentAggregation(
            posts_analyzed=len(posts),
            weighted_sentiment=weighted_sentiment,
            raw_sentiment=raw_sentiment,
            sentiment_confidence=confidence,
            momentum=momentum,
            volume_trend=volume_trend,
            top_posts=social_posts,
            platform_breakdown=platform_breakdown,
            freshness_hours=freshness,
            bot_filtered_count=bot_filtered
        )
    
    def _empty_aggregation(self, bot_filtered: int = 0) -> SentimentAggregation:
        """Return empty aggregation when no data available."""
        return SentimentAggregation(
            posts_analyzed=0,
            weighted_sentiment=0.0,
            raw_sentiment=0.0,
            sentiment_confidence=0.0,
            momentum=0.0,
            volume_trend=0.0,
            top_posts=[],
            platform_breakdown={},
            freshness_hours=24.0,
            bot_filtered_count=bot_filtered
        )
