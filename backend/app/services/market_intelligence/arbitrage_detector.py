"""
Arbitrage Detector

Detects divergence between AI predictions, market prices, and crowd votes.
These divergences are high-value signals for users and create engagement hooks.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import Market, MarketPredictionFactors, MarketVote

logger = logging.getLogger(__name__)


class DivergenceType(Enum):
    """Types of divergence between prediction signals."""
    AI_MARKET = "ai_market_divergence"
    CROWD_AI = "crowd_ai_divergence"
    CROWD_MARKET = "crowd_market_divergence"
    THREE_WAY = "three_way_divergence"


@dataclass
class ArbitrageSignal:
    """A detected divergence between prediction signals."""
    type: DivergenceType
    strength: float  # 0-1, higher = stronger divergence
    ai_probability: Optional[float]
    market_probability: float
    crowd_probability: Optional[float]
    description: str
    recommendation: str
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "strength": self.strength,
            "ai_probability": self.ai_probability,
            "market_probability": self.market_probability,
            "crowd_probability": self.crowd_probability,
            "description": self.description,
            "recommendation": self.recommendation,
            "created_at": self.created_at.isoformat()
        }


class ArbitrageDetector:
    """
    Detect divergence between AI, market price, and crowd predictions.
    
    When these signals diverge significantly, it indicates:
    1. Potential market inefficiency
    2. Information asymmetry
    3. Trading opportunities (for engaged users)
    """
    
    # Thresholds for divergence detection
    AI_MARKET_THRESHOLD = 0.15  # 15 percentage points
    CROWD_AI_THRESHOLD = 0.20   # 20 percentage points
    CROWD_MARKET_THRESHOLD = 0.15
    THREE_WAY_THRESHOLD = 0.25
    
    def __init__(self, db: Session):
        self.db = db
    
    def detect_opportunities(
        self,
        market_id: int
    ) -> List[ArbitrageSignal]:
        """
        Detect all divergence opportunities for a market.
        
        Args:
            market_id: Market to analyze
        
        Returns:
            List of detected ArbitrageSignals
        """
        # Get market
        market = self.db.query(Market).filter(Market.id == market_id).first()
        if not market:
            logger.warning(f"Market {market_id} not found")
            return []
        
        # Get current market probability from liquidity
        total_liquidity = market.yes_liquidity + market.no_liquidity
        market_prob = market.yes_liquidity / total_liquidity if total_liquidity > 0 else 0.5
        
        # Get latest AI probability
        ai_pred = self.db.query(MarketPredictionFactors).filter(
            MarketPredictionFactors.market_id == market_id
        ).order_by(MarketPredictionFactors.created_at.desc()).first()
        
        ai_prob = ai_pred.calibrated_probability if ai_pred else None
        
        # Get crowd vote probability
        crowd_prob = self._get_crowd_probability(market_id)
        
        signals = []
        
        # Check AI vs Market divergence
        if ai_prob is not None:
            ai_market_diff = abs(ai_prob - market_prob)
            if ai_market_diff > self.AI_MARKET_THRESHOLD:
                direction = "SÍ" if ai_prob > market_prob else "NO"
                signals.append(ArbitrageSignal(
                    type=DivergenceType.AI_MARKET,
                    strength=min(1.0, ai_market_diff / 0.30),  # Normalize to 0-1
                    ai_probability=ai_prob,
                    market_probability=market_prob,
                    crowd_probability=crowd_prob,
                    description=(
                        f"La IA predice {ai_prob*100:.0f}% SÍ pero el mercado está en "
                        f"{market_prob*100:.0f}%. Diferencia de {ai_market_diff*100:.0f} puntos."
                    ),
                    recommendation=(
                        f"La IA sugiere que {direction} está subvalorado. "
                        f"Considera revisar los factores de la IA antes de tomar posición."
                    ),
                    created_at=datetime.utcnow()
                ))
        
        # Check Crowd vs AI divergence
        if ai_prob is not None and crowd_prob is not None:
            crowd_ai_diff = abs(crowd_prob - ai_prob)
            if crowd_ai_diff > self.CROWD_AI_THRESHOLD:
                signals.append(ArbitrageSignal(
                    type=DivergenceType.CROWD_AI,
                    strength=min(1.0, crowd_ai_diff / 0.35),
                    ai_probability=ai_prob,
                    market_probability=market_prob,
                    crowd_probability=crowd_prob,
                    description=(
                        f"La comunidad vota {crowd_prob*100:.0f}% SÍ pero la IA predice "
                        f"{ai_prob*100:.0f}%. Los humanos y la máquina no están de acuerdo."
                    ),
                    recommendation=(
                        "Divergencia humano-máquina detectada. Esto puede indicar información "
                        "que la IA no captura o sesgo en la comunidad."
                    ),
                    created_at=datetime.utcnow()
                ))
        
        # Check Crowd vs Market divergence
        if crowd_prob is not None:
            crowd_market_diff = abs(crowd_prob - market_prob)
            if crowd_market_diff > self.CROWD_MARKET_THRESHOLD:
                signals.append(ArbitrageSignal(
                    type=DivergenceType.CROWD_MARKET,
                    strength=min(1.0, crowd_market_diff / 0.30),
                    ai_probability=ai_prob,
                    market_probability=market_prob,
                    crowd_probability=crowd_prob,
                    description=(
                        f"Los votos de la comunidad ({crowd_prob*100:.0f}% SÍ) difieren "
                        f"del precio de mercado ({market_prob*100:.0f}%)."
                    ),
                    recommendation=(
                        "La opinión de la comunidad no está reflejada en el precio. "
                        "Quienes votan aún no han puesto créditos donde están sus opiniones."
                    ),
                    created_at=datetime.utcnow()
                ))
        
        # Check three-way divergence
        if ai_prob is not None and crowd_prob is not None:
            max_diff = max(
                abs(ai_prob - market_prob),
                abs(crowd_prob - market_prob),
                abs(crowd_prob - ai_prob)
            )
            if max_diff > self.THREE_WAY_THRESHOLD:
                signals.append(ArbitrageSignal(
                    type=DivergenceType.THREE_WAY,
                    strength=min(1.0, max_diff / 0.40),
                    ai_probability=ai_prob,
                    market_probability=market_prob,
                    crowd_probability=crowd_prob,
                    description=(
                        f"Divergencia triple: IA ({ai_prob*100:.0f}%), "
                        f"mercado ({market_prob*100:.0f}%), "
                        f"comunidad ({crowd_prob*100:.0f}%). "
                        f"Alta incertidumbre."
                    ),
                    recommendation=(
                        "Señales contradictorias de múltiples fuentes. "
                        "Este mercado tiene alta incertidumbre - investiga más antes de decidir."
                    ),
                    created_at=datetime.utcnow()
                ))
        
        return signals
    
    def _get_crowd_probability(self, market_id: int) -> Optional[float]:
        """Get crowd-sourced probability from votes."""
        votes = self.db.query(MarketVote).filter(
            MarketVote.market_id == market_id
        ).all()
        
        if not votes:
            return None
        
        # Weight by confidence if available
        weighted_yes = 0.0
        total_weight = 0.0
        
        for vote in votes:
            weight = vote.confidence if vote.confidence else 3  # Default confidence = 3
            if vote.outcome == "yes":
                weighted_yes += weight
            total_weight += weight
        
        if total_weight == 0:
            return None
        
        return weighted_yes / total_weight
    
    def get_market_signals_summary(
        self,
        market_id: int
    ) -> Dict[str, Any]:
        """
        Get a summary of all signals for a market.
        
        Useful for displaying on the market detail page.
        """
        market = self.db.query(Market).filter(Market.id == market_id).first()
        if not market:
            return {}
        
        total_liquidity = market.yes_liquidity + market.no_liquidity
        market_prob = market.yes_liquidity / total_liquidity if total_liquidity > 0 else 0.5
        
        ai_pred = self.db.query(MarketPredictionFactors).filter(
            MarketPredictionFactors.market_id == market_id
        ).order_by(MarketPredictionFactors.created_at.desc()).first()
        
        crowd_prob = self._get_crowd_probability(market_id)
        
        arbitrage_signals = self.detect_opportunities(market_id)
        
        return {
            "market_id": market_id,
            "signals": {
                "market": {
                    "probability": market_prob,
                    "source": "liquidity_pool"
                },
                "ai": {
                    "probability": ai_pred.calibrated_probability if ai_pred else None,
                    "confidence": ai_pred.confidence if ai_pred else None,
                    "source": ai_pred.agent_type if ai_pred else None
                },
                "crowd": {
                    "probability": crowd_prob,
                    "source": "user_votes"
                }
            },
            "arbitrage_opportunities": [s.to_dict() for s in arbitrage_signals],
            "has_divergence": len(arbitrage_signals) > 0,
            "max_divergence_strength": max(
                (s.strength for s in arbitrage_signals), default=0
            ),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def find_markets_with_opportunities(
        self,
        min_strength: float = 0.5,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find all open markets with significant arbitrage opportunities.
        
        Useful for a "opportunities" dashboard.
        """
        markets = self.db.query(Market).filter(
            Market.status == "open"
        ).all()
        
        opportunities = []
        
        for market in markets:
            signals = self.detect_opportunities(market.id)
            if signals:
                max_strength = max(s.strength for s in signals)
                if max_strength >= min_strength:
                    opportunities.append({
                        "market_id": market.id,
                        "question": market.question,
                        "category": market.category,
                        "max_strength": max_strength,
                        "signal_count": len(signals),
                        "top_signal": signals[0].to_dict() if signals else None
                    })
        
        # Sort by strength descending
        opportunities.sort(key=lambda x: x["max_strength"], reverse=True)
        
        return opportunities[:limit]
