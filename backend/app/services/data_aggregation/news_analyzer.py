"""
News Analyzer Service

Aggregates and analyzes news articles related to prediction markets.
Uses Claude Haiku for cost-effective summarization and stance detection.
"""

import os
import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

import httpx
import anthropic

from app.services.market_intelligence.models import (
    NewsArticle,
    NewsAggregation,
)

logger = logging.getLogger(__name__)


# Known credible Mexican news sources with credibility scores
SOURCE_CREDIBILITY = {
    # High credibility (0.85-1.0)
    "animalpolitico.com": 0.90,
    "aristeguinoticias.com": 0.88,
    "eluniversal.com.mx": 0.85,
    "proceso.com.mx": 0.87,
    "reforma.com": 0.88,
    "milenio.com": 0.82,
    "excelsior.com.mx": 0.80,
    "jornada.com.mx": 0.82,
    "expansion.mx": 0.85,
    "forbes.com.mx": 0.85,
    "elfinanciero.com.mx": 0.86,
    "eleconomista.com.mx": 0.85,
    
    # Government/Official sources (high credibility for data)
    "ine.mx": 0.95,
    "banxico.org.mx": 0.95,
    "inegi.org.mx": 0.95,
    "dof.gob.mx": 0.93,
    "gob.mx": 0.88,
    
    # Medium credibility (0.6-0.8)
    "elheraldodemexico.com": 0.70,
    "sdpnoticias.com": 0.65,
    "infobae.com": 0.72,
    "televisa.com": 0.68,
    "azteca.com": 0.65,
    
    # Low credibility or satire (0.0-0.6)
    "deforma.com": 0.0,  # Satire
}


class NewsAnalyzer:
    """
    Analyzes news articles for prediction markets.
    
    Uses:
    - Serper API for news search
    - Claude Haiku for summarization and stance detection
    - Source credibility weighting
    """
    
    HAIKU_MODEL = "claude-3-5-haiku-20241022"
    MAX_ARTICLES = 20
    
    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        self.anthropic_client = None
        if self.anthropic_api_key:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                logger.info("✓ NewsAnalyzer initialized with Claude Haiku")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
        
        if not self.serper_api_key:
            logger.warning("SERPER_API_KEY not found. News search will be limited.")
    
    async def aggregate_news_for_market(
        self,
        market_question: str,
        market_category: str = None,
        hours: int = 24,
        max_articles: int = None
    ) -> NewsAggregation:
        """
        Aggregate news articles relevant to a market question.
        
        Args:
            market_question: The market question to find news about
            market_category: Optional category for focused search
            hours: How many hours back to search
            max_articles: Maximum articles to analyze (default: MAX_ARTICLES)
        
        Returns:
            NewsAggregation with analyzed articles and signals
        """
        max_articles = max_articles or self.MAX_ARTICLES
        
        # Search for relevant news
        raw_articles = await self._search_news(
            query=market_question,
            category=market_category,
            hours=hours
        )
        
        if not raw_articles:
            return self._empty_aggregation()
        
        # Limit articles for cost control
        raw_articles = raw_articles[:max_articles]
        
        # Analyze each article (with Haiku if available)
        analyzed_articles = []
        for article in raw_articles:
            try:
                analyzed = await self._analyze_article(article, market_question)
                if analyzed:
                    analyzed_articles.append(analyzed)
            except Exception as e:
                logger.warning(f"Failed to analyze article: {e}")
                continue
        
        if not analyzed_articles:
            return self._empty_aggregation()
        
        # Calculate aggregated signals
        return self._calculate_aggregation(analyzed_articles)
    
    async def _search_news(
        self,
        query: str,
        category: str = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Search for news using Serper API."""
        if not self.serper_api_key:
            return self._mock_search_results(query)
        
        try:
            async with httpx.AsyncClient() as client:
                # Build search query - focus on Mexican news
                search_query = f"{query} Mexico site:mx OR site:com.mx"
                if category:
                    search_query = f"{search_query} {category}"
                
                response = await client.post(
                    "https://google.serper.dev/news",
                    headers={
                        "X-API-KEY": self.serper_api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": search_query,
                        "gl": "mx",
                        "hl": "es",
                        "num": 30,
                        "tbs": f"qdr:h{hours}"  # Time range
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Serper API error: {response.status_code}")
                    return []
                
                data = response.json()
                return data.get("news", [])
                
        except Exception as e:
            logger.error(f"News search failed: {e}")
            return []
    
    async def _analyze_article(
        self,
        article: Dict[str, Any],
        market_question: str
    ) -> Optional[NewsArticle]:
        """
        Analyze a single news article for stance and relevance.
        
        Uses Claude Haiku for:
        - Summarization
        - Stance detection (supports/opposes market question)
        - Relevance scoring
        """
        title = article.get("title", "")
        snippet = article.get("snippet", "")
        link = article.get("link", "")
        source = article.get("source", "")
        date_str = article.get("date", "")
        
        # Get source credibility
        credibility = self._get_source_credibility(link)
        
        # Skip low credibility sources
        if credibility < 0.3:
            logger.debug(f"Skipping low credibility source: {source}")
            return None
        
        # Parse date
        published_at = None
        if date_str:
            try:
                # Serper returns relative dates like "2 hours ago"
                # For now, approximate based on current time
                published_at = datetime.utcnow()
            except Exception:
                pass
        
        # Analyze with Haiku if available
        if self.anthropic_client:
            analysis = await self._haiku_analyze(
                title=title,
                snippet=snippet,
                market_question=market_question
            )
            
            return NewsArticle(
                title=title,
                url=link,
                source=source,
                published_at=published_at,
                summary=analysis.get("summary", snippet[:200]),
                stance=analysis.get("stance", 0.0),
                credibility_score=credibility,
                relevance_score=analysis.get("relevance", 0.5)
            )
        
        # Fallback: simple keyword-based analysis
        return NewsArticle(
            title=title,
            url=link,
            source=source,
            published_at=published_at,
            summary=snippet[:200] if snippet else title,
            stance=0.0,  # Neutral without LLM
            credibility_score=credibility,
            relevance_score=0.5
        )
    
    async def _haiku_analyze(
        self,
        title: str,
        snippet: str,
        market_question: str
    ) -> Dict[str, Any]:
        """
        Use Claude Haiku for quick article analysis.
        
        Cost-effective: ~$0.00025 per article
        """
        try:
            response = self.anthropic_client.messages.create(
                model=self.HAIKU_MODEL,
                max_tokens=300,
                system="You analyze news articles for prediction market relevance. Be concise. Respond only with valid JSON.",
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this news article for the prediction market question.

MARKET QUESTION: {market_question}

ARTICLE TITLE: {title}
ARTICLE SNIPPET: {snippet}

Respond with JSON:
{{
    "summary": "1-2 sentence summary in Spanish",
    "stance": -1.0 to 1.0 (negative = suggests NO, positive = suggests YES, 0 = neutral/unclear),
    "relevance": 0.0 to 1.0 (how relevant to the market question)
}}"""
                }]
            )
            
            import json
            response_text = response.content[0].text
            
            # Extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            return json.loads(response_text.strip())
            
        except Exception as e:
            logger.warning(f"Haiku analysis failed: {e}")
            return {"summary": snippet[:200], "stance": 0.0, "relevance": 0.5}
    
    def _get_source_credibility(self, url: str) -> float:
        """Get credibility score for a source based on URL."""
        url_lower = url.lower()
        
        for source, score in SOURCE_CREDIBILITY.items():
            if source in url_lower:
                return score
        
        # Default credibility for unknown sources
        # Prefer .mx domains slightly
        if ".mx" in url_lower:
            return 0.6
        return 0.5
    
    def _calculate_aggregation(
        self,
        articles: List[NewsArticle]
    ) -> NewsAggregation:
        """Calculate aggregated signals from analyzed articles."""
        if not articles:
            return self._empty_aggregation()
        
        # Calculate signals
        total_credibility = sum(a.credibility_score for a in articles)
        
        # Credibility-weighted stance
        if total_credibility > 0:
            weighted_stance = sum(
                a.stance * a.credibility_score * a.relevance_score
                for a in articles
            ) / total_credibility
        else:
            weighted_stance = 0.0
        
        # Simple average stance
        overall_stance = sum(a.stance for a in articles) / len(articles)
        
        # Calculate velocity (articles per hour)
        # Approximate based on having data within the search window
        velocity = len(articles) / 24.0  # Default to 24-hour window
        
        # Freshness - use current time as approximation
        freshness = 1.0  # 1 hour default for recent search
        
        return NewsAggregation(
            articles=sorted(articles, key=lambda x: x.relevance_score, reverse=True),
            overall_signal=overall_stance,
            volume=len(articles),
            velocity=velocity,
            credibility_weighted_signal=weighted_stance,
            freshness_hours=freshness
        )
    
    def _empty_aggregation(self) -> NewsAggregation:
        """Return empty aggregation when no data available."""
        return NewsAggregation(
            articles=[],
            overall_signal=0.0,
            volume=0,
            velocity=0.0,
            credibility_weighted_signal=0.0,
            freshness_hours=24.0
        )
    
    def _mock_search_results(self, query: str) -> List[Dict[str, Any]]:
        """Return mock results when Serper API is not available."""
        logger.warning("Using mock news results - Serper API key not configured")
        return [
            {
                "title": f"Artículo relacionado a: {query[:50]}",
                "snippet": "Este es un resultado de prueba. Configure SERPER_API_KEY para obtener noticias reales.",
                "link": "https://example.com/article",
                "source": "Mock News",
                "date": "1 hour ago"
            }
        ]
    
    def calculate_news_signal(self, aggregation: NewsAggregation) -> float:
        """
        Calculate a normalized news signal from aggregation.
        
        Returns:
            Float from -1 to 1:
            - Positive = news supports YES outcome
            - Negative = news supports NO outcome
            - Near 0 = neutral or conflicting
        """
        if not aggregation or aggregation.volume == 0:
            return 0.0
        
        # Weight by credibility and volume
        # More articles with consistent signal = stronger signal
        base_signal = aggregation.credibility_weighted_signal
        
        # Confidence boost from volume (diminishing returns)
        volume_factor = min(1.0, aggregation.volume / 10.0)
        
        # Freshness decay
        freshness_factor = max(0.5, 1.0 - (aggregation.freshness_hours / 48.0))
        
        return base_signal * volume_factor * freshness_factor
