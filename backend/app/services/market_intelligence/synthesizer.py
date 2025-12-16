"""
Market Synthesizer Agent

Single intelligent agent that synthesizes multiple data sources
(news, sentiment, historical patterns) into calibrated predictions
with transparent reasoning chains.

Uses Claude Sonnet 3.5 for complex reasoning and structured output.
"""

from app.core.config import settings
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

import anthropic

from .models import (
    PredictionResult,
    NewsAggregation,
    SentimentAggregation,
    SimilarMarket,
    MarketDataBundle,
    KeyFactor,
    RiskFactor,
    AnalysisTier,
    RiskLevel,
)
from .prompts import SYSTEM_PROMPT, build_analysis_prompt

logger = logging.getLogger(__name__)


class MarketSynthesizer:
    """
    Single agent that takes structured inputs and produces
    calibrated prediction with reasoning chain.
    
    This is the core prediction engine for the market intelligence system.
    It synthesizes news, sentiment, and historical data into a coherent
    prediction with full transparency.
    """
    
    AGENT_ID = "synthesizer_v1"
    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 4096
    
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.client = None
        
        if self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("✓ MarketSynthesizer initialized with Claude Sonnet")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
        else:
            logger.warning("ANTHROPIC_API_KEY not found. Synthesizer will use fallback logic.")
    
    async def analyze_market(
        self,
        market_id: int,
        market_question: str,
        market_description: str,
        category: str,
        resolution_criteria: str,
        current_probability: float,
        volume: float,
        closes_at: Optional[datetime],
        data_bundle: MarketDataBundle,
        tier: AnalysisTier = AnalysisTier.DAILY
    ) -> PredictionResult:
        """
        Analyze a market and produce a calibrated prediction.
        
        Args:
            market_id: Unique market identifier
            market_question: The question being predicted
            market_description: Additional context about the market
            category: Market category (politics, economy, etc.)
            resolution_criteria: How the market will be resolved
            current_probability: Current probability from market liquidity
            volume: Trading volume in credits
            closes_at: When the market closes
            data_bundle: Aggregated data from all sources
            tier: Analysis depth tier
        
        Returns:
            PredictionResult with calibrated probability and reasoning
        """
        logger.info(f"Analyzing market {market_id}: {market_question[:50]}... (Tier {tier.value})")
        
        # Calculate days until close
        days_until_close = -1
        if closes_at:
            delta = closes_at - datetime.utcnow()
            days_until_close = max(0, delta.days)
        
        # For lightweight tier, use simple heuristics (no LLM)
        if tier == AnalysisTier.LIGHTWEIGHT:
            return self._lightweight_analysis(
                market_id=market_id,
                market_question=market_question,
                current_probability=current_probability,
                data_bundle=data_bundle
            )
        
        # For daily/deep analysis, use Claude Sonnet
        if not self.client:
            logger.warning("No Anthropic client available, using fallback analysis")
            return self._fallback_analysis(
                market_id=market_id,
                market_question=market_question,
                current_probability=current_probability,
                data_bundle=data_bundle,
                tier=tier
            )
        
        try:
            # Build the analysis prompt
            prompt = build_analysis_prompt(
                market_question=market_question,
                market_description=market_description,
                category=category,
                resolution_criteria=resolution_criteria,
                current_probability=current_probability,
                volume=volume,
                days_until_close=days_until_close,
                news_data=data_bundle.news.to_dict() if data_bundle.news else None,
                sentiment_data=data_bundle.sentiment.to_dict() if data_bundle.sentiment else None,
                similar_markets=[m.to_dict() for m in data_bundle.similar_markets]
            )
            
            # Call Claude Sonnet
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse the response
            response_text = response.content[0].text
            result = self._parse_llm_response(response_text, data_bundle, tier)
            
            logger.info(
                f"Market {market_id} analysis complete: "
                f"prob={result.calibrated_probability:.2f}, "
                f"conf={result.confidence:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Claude analysis for market {market_id}: {e}")
            return self._fallback_analysis(
                market_id=market_id,
                market_question=market_question,
                current_probability=current_probability,
                data_bundle=data_bundle,
                tier=tier
            )
    
    def _parse_llm_response(
        self,
        response_text: str,
        data_bundle: MarketDataBundle,
        tier: AnalysisTier
    ) -> PredictionResult:
        """Parse the LLM JSON response into a PredictionResult."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_text = response_text
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0]
            
            data = json.loads(json_text.strip())
            
            # Parse key factors
            key_factors = []
            for f in data.get("key_factors", []):
                key_factors.append(KeyFactor(
                    factor=f.get("factor", "Unknown factor"),
                    impact=float(f.get("impact", 0)),
                    confidence=float(f.get("confidence", 0.5)),
                    source=f.get("source", "unknown"),
                    evidence=f.get("evidence")
                ))
            
            # Parse risk factors
            risk_factors = []
            for r in data.get("risk_factors", []):
                severity_str = r.get("severity", "medium").lower()
                severity = RiskLevel(severity_str) if severity_str in ["low", "medium", "high", "critical"] else RiskLevel.MEDIUM
                risk_factors.append(RiskFactor(
                    risk=r.get("risk", "Unknown risk"),
                    severity=severity,
                    probability=float(r.get("probability", 0.5)),
                    impact_on_prediction=r.get("impact_on_prediction", "")
                ))
            
            raw_prob = float(data.get("probability", 0.5))
            confidence = float(data.get("confidence", 0.5))
            
            # Calculate confidence interval based on confidence
            # Lower confidence = wider interval
            interval_width = 0.3 * (1 - confidence)  # Max 30% width at 0 confidence
            prob_low = max(0.0, raw_prob - interval_width)
            prob_high = min(1.0, raw_prob + interval_width)
            
            # Calculate data freshness
            freshness = 24.0  # Default
            if data_bundle.news and data_bundle.news.freshness_hours:
                freshness = min(freshness, data_bundle.news.freshness_hours)
            if data_bundle.sentiment and data_bundle.sentiment.freshness_hours:
                freshness = min(freshness, data_bundle.sentiment.freshness_hours)
            
            return PredictionResult(
                raw_probability=raw_prob,
                calibrated_probability=raw_prob,  # Calibration applied separately
                confidence=confidence,
                probability_low=prob_low,
                probability_high=prob_high,
                key_factors=key_factors,
                risk_factors=risk_factors,
                data_sources={
                    "news": data_bundle.news is not None,
                    "sentiment": data_bundle.sentiment is not None,
                    "similar_markets": len(data_bundle.similar_markets),
                    "market_liquidity": True
                },
                data_freshness_hours=freshness,
                reasoning_chain=data.get("reasoning_chain", ""),
                summary=data.get("summary", ""),
                analysis_tier=tier,
                agent_id=self.AGENT_ID
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            raise
    
    def _lightweight_analysis(
        self,
        market_id: int,
        market_question: str,
        current_probability: float,
        data_bundle: MarketDataBundle
    ) -> PredictionResult:
        """
        Lightweight analysis without LLM calls.
        Uses simple signal combination from available data.
        """
        signals = []
        weights = []
        
        # Market liquidity signal (current price)
        signals.append(current_probability)
        weights.append(0.4)  # Base weight for market wisdom
        
        # News signal
        if data_bundle.news:
            # Convert -1 to 1 signal to 0 to 1 probability adjustment
            news_adjustment = data_bundle.news.credibility_weighted_signal * 0.15
            signals.append(current_probability + news_adjustment)
            weights.append(0.25)
        
        # Sentiment signal
        if data_bundle.sentiment:
            sentiment_adjustment = data_bundle.sentiment.weighted_sentiment * 0.1
            signals.append(current_probability + sentiment_adjustment)
            weights.append(0.2)
        
        # Similar markets signal
        if data_bundle.similar_markets:
            # Weight by similarity and use outcome
            similar_prob = 0.0
            total_weight = 0.0
            for sm in data_bundle.similar_markets[:3]:
                outcome_prob = 1.0 if sm.outcome == "yes" else 0.0
                similar_prob += outcome_prob * sm.similarity_score
                total_weight += sm.similarity_score
            
            if total_weight > 0:
                similar_prob /= total_weight
                signals.append(similar_prob)
                weights.append(0.15)
        
        # Weighted combination
        total_weight = sum(weights)
        combined_prob = sum(s * w for s, w in zip(signals, weights)) / total_weight
        combined_prob = max(0.05, min(0.95, combined_prob))  # Clamp
        
        # Calculate confidence based on data availability
        confidence = 0.3  # Base confidence for lightweight
        if data_bundle.news:
            confidence += 0.15
        if data_bundle.sentiment:
            confidence += 0.15
        if data_bundle.similar_markets:
            confidence += 0.1
        
        # Wider confidence interval for lightweight
        interval_width = 0.2
        
        return PredictionResult(
            raw_probability=combined_prob,
            calibrated_probability=combined_prob,
            confidence=confidence,
            probability_low=max(0.0, combined_prob - interval_width),
            probability_high=min(1.0, combined_prob + interval_width),
            key_factors=[
                KeyFactor(
                    factor="Precio de mercado actual",
                    impact=current_probability - 0.5,
                    confidence=0.7,
                    source="market"
                )
            ],
            risk_factors=[
                RiskFactor(
                    risk="Análisis ligero - datos limitados",
                    severity=RiskLevel.MEDIUM,
                    probability=0.5,
                    impact_on_prediction="Mayor incertidumbre en la estimación"
                )
            ],
            data_sources={
                "news": data_bundle.news is not None,
                "sentiment": data_bundle.sentiment is not None,
                "similar_markets": len(data_bundle.similar_markets),
                "market_liquidity": True
            },
            data_freshness_hours=24.0,
            reasoning_chain="Lightweight analysis: Combined market price with available signals.",
            summary=f"Análisis rápido basado en precio de mercado ({current_probability*100:.0f}%) y señales disponibles.",
            analysis_tier=AnalysisTier.LIGHTWEIGHT,
            agent_id=self.AGENT_ID
        )
    
    def _fallback_analysis(
        self,
        market_id: int,
        market_question: str,
        current_probability: float,
        data_bundle: MarketDataBundle,
        tier: AnalysisTier
    ) -> PredictionResult:
        """
        Fallback analysis when LLM is not available.
        More sophisticated than lightweight but still rule-based.
        """
        # Start with market price as base
        base_prob = current_probability
        
        # Collect all adjustment factors
        adjustments = []
        key_factors = []
        
        # News-based adjustment
        if data_bundle.news and data_bundle.news.volume > 0:
            news_signal = data_bundle.news.credibility_weighted_signal
            news_adjustment = news_signal * 0.1  # Max 10% adjustment
            adjustments.append(news_adjustment)
            
            key_factors.append(KeyFactor(
                factor=f"Señal de noticias: {'positiva' if news_signal > 0 else 'negativa'}",
                impact=news_signal,
                confidence=min(0.8, data_bundle.news.volume / 10),  # More articles = more confidence
                source="news",
                evidence=f"{data_bundle.news.volume} artículos analizados"
            ))
        
        # Sentiment-based adjustment
        if data_bundle.sentiment and data_bundle.sentiment.posts_analyzed > 10:
            sentiment_signal = data_bundle.sentiment.weighted_sentiment
            sentiment_conf = data_bundle.sentiment.sentiment_confidence
            sentiment_adjustment = sentiment_signal * 0.08 * sentiment_conf
            adjustments.append(sentiment_adjustment)
            
            key_factors.append(KeyFactor(
                factor=f"Sentimiento social: {'positivo' if sentiment_signal > 0 else 'negativo'}",
                impact=sentiment_signal,
                confidence=sentiment_conf,
                source="social",
                evidence=f"{data_bundle.sentiment.posts_analyzed} publicaciones analizadas"
            ))
        
        # Historical similar markets
        if data_bundle.similar_markets:
            yes_outcomes = sum(1 for m in data_bundle.similar_markets if m.outcome == "yes")
            total = len(data_bundle.similar_markets)
            historical_rate = yes_outcomes / total
            historical_adjustment = (historical_rate - 0.5) * 0.15
            adjustments.append(historical_adjustment)
            
            key_factors.append(KeyFactor(
                factor=f"Mercados similares: {yes_outcomes}/{total} resolvieron SÍ",
                impact=historical_rate - 0.5,
                confidence=min(0.7, total / 5),  # More similar markets = more confidence
                source="historical"
            ))
        
        # Apply adjustments
        final_prob = base_prob + sum(adjustments)
        final_prob = max(0.05, min(0.95, final_prob))
        
        # Calculate confidence
        confidence = 0.5  # Base for fallback
        if data_bundle.news:
            confidence += 0.1
        if data_bundle.sentiment:
            confidence += 0.1
        if data_bundle.similar_markets:
            confidence += 0.1
        
        # Confidence interval
        interval_width = 0.15 * (1 - confidence)
        
        return PredictionResult(
            raw_probability=final_prob,
            calibrated_probability=final_prob,
            confidence=confidence,
            probability_low=max(0.0, final_prob - interval_width - 0.1),
            probability_high=min(1.0, final_prob + interval_width + 0.1),
            key_factors=key_factors,
            risk_factors=[
                RiskFactor(
                    risk="Análisis sin LLM - razonamiento limitado",
                    severity=RiskLevel.MEDIUM,
                    probability=0.3,
                    impact_on_prediction="Factores cualitativos pueden no estar capturados"
                )
            ],
            data_sources={
                "news": data_bundle.news is not None,
                "sentiment": data_bundle.sentiment is not None,
                "similar_markets": len(data_bundle.similar_markets),
                "market_liquidity": True
            },
            data_freshness_hours=24.0,
            reasoning_chain=(
                f"Fallback analysis: Started with market price ({base_prob:.2f}), "
                f"applied {len(adjustments)} adjustments based on available data. "
                f"Final probability: {final_prob:.2f}"
            ),
            summary=(
                f"Análisis basado en reglas combinando el precio de mercado actual "
                f"({base_prob*100:.0f}%) con {len(key_factors)} factores identificados."
            ),
            analysis_tier=tier,
            agent_id=f"{self.AGENT_ID}_fallback"
        )
    
    async def batch_analyze(
        self,
        markets: List[Dict[str, Any]],
        data_bundles: Dict[int, MarketDataBundle],
        tier: AnalysisTier = AnalysisTier.DAILY
    ) -> Dict[int, PredictionResult]:
        """
        Analyze multiple markets in batch.
        
        For cost efficiency, this can be used during daily analysis runs.
        """
        results = {}
        
        for market in markets:
            market_id = market["id"]
            data_bundle = data_bundles.get(market_id, MarketDataBundle())
            
            try:
                result = await self.analyze_market(
                    market_id=market_id,
                    market_question=market["question"],
                    market_description=market.get("description", ""),
                    category=market.get("category", ""),
                    resolution_criteria=market.get("resolution_criteria", ""),
                    current_probability=market.get("current_probability", 0.5),
                    volume=market.get("volume", 0),
                    closes_at=market.get("closes_at"),
                    data_bundle=data_bundle,
                    tier=tier
                )
                results[market_id] = result
                
            except Exception as e:
                logger.error(f"Failed to analyze market {market_id}: {e}")
                # Continue with other markets
        
        return results
