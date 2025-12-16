"""
Lightweight Market Intelligence Agent

Efficiently assesses prediction market probabilities without expensive RAG pipeline.
Uses single LLM call + fast DB queries for context.

Default: Claude Haiku 3.5 (fast, cheap)
Upgrade: Claude Sonnet 3.5 (better reasoning, more expensive)
"""
from app.agents.base_agent import BaseAgent
from app.database.models import Market, MarketTrade, MarketStatus
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Dict, List, Optional
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class MarketIntelligenceAgent(BaseAgent):
    """Lightweight agent for market probability assessment"""
    
    def __init__(self, model_preference: Optional[str] = None):
        """
        Initialize Market Intelligence Agent.
        
        Args:
            model_preference: "haiku" (default, fast/cheap), "sonnet" (better reasoning),
                            "gpt-mini" (OpenAI budget), "gpt-4o" (OpenAI premium)
        """
        super().__init__()
        
        # Get model preference from env or parameter
        preference = model_preference or settings.MARKET_INTELLIGENCE_MODEL
        
        # Model selection map
        model_map = {
            "haiku": "claude-3-haiku-20240307",  # Fastest, cheapest (recommended) - using stable version
            "sonnet": "claude-sonnet-3-5-20241022",  # Better reasoning, more expensive
            "gpt-mini": "gpt-4o-mini",  # OpenAI budget option
            "gpt-4o": "gpt-4o"  # OpenAI premium
        }
        
        self.primary_model = model_map.get(preference, "claude-3-haiku-20240307")
        self.fallback_model = "gpt-4o-mini"  # Always use mini as fallback
        
        # Log model selection
        logger.info(f"MarketIntelligenceAgent initialized with model: {self.primary_model}")
    
    @property
    def name(self) -> str:
        return "MarketIntelligenceAgent"
    
    @property
    def description(self) -> str:
        return "Provides efficient probability assessments for prediction markets"
    
    async def analyze(self, claim: str, context: Dict) -> 'AgentResult':
        """
        Required by BaseAgent interface, but not used for market intelligence.
        Market intelligence uses assess_market_probability() instead.
        """
        from app.agents.base_agent import AgentResult
        return AgentResult(
            agent_name=self.name,
            confidence=0.0,
            findings="{}",
            error="Use assess_market_probability() instead of analyze() for market intelligence"
        )
    
    async def assess_market_probability(
        self,
        market: Market,
        db: Session,
        use_claim_context: bool = True,
        force_model: Optional[str] = None
    ) -> Dict:
        """
        Efficiently assess market probability with minimal API calls.
        
        Args:
            market: Market instance to assess
            db: Database session
            use_claim_context: Whether to include claim context if available
            force_model: Override model for this assessment (e.g., "sonnet" for important markets)
        
        Returns:
            Dict with probability assessment and recommended seed amount
        """
        # Override model if specified
        original_model = self.primary_model
        if force_model:
            model_map = {
                "haiku": "claude-3-haiku-20240307",
                "sonnet": "claude-sonnet-3-5-20241022",
                "gpt-mini": "gpt-4o-mini",
                "gpt-4o": "gpt-4o"
            }
            if force_model.lower() in model_map:
                self.primary_model = model_map[force_model.lower()]
                logger.debug(f"Using forced model: {self.primary_model}")
        
        try:
            # 1. Build minimal context (no expensive RAG)
            context_parts = []
            
            # If linked to a claim, get basic claim info (no verification)
            if market.claim_id and use_claim_context:
                from app.database.models import Claim
                claim = db.query(Claim).filter(Claim.id == market.claim_id).first()
                if claim:
                    context_parts.append(f"Afirmación relacionada: {claim.claim_text[:200]}")
                    if claim.status:
                        context_parts.append(f"Estado de verificación: {claim.status.value}")
            
            # 2. Find similar markets (fast DB query, not semantic search)
            similar_markets = self._get_similar_markets(market, db)
            if similar_markets:
                avg_initial = sum(m['initial_prob'] for m in similar_markets) / len(similar_markets)
                context_parts.append(
                    f"Mercados similares resueltos: {len(similar_markets)} "
                    f"(probabilidad inicial promedio: {avg_initial:.1%})"
                )
            
            # 3. Category trends (if available)
            if market.category:
                category_stats = self._get_category_stats(market.category, db)
                if category_stats:
                    context_parts.append(
                        f"Tendencia en categoría '{market.category}': "
                        f"{category_stats['avg_yes_prob']:.1%} probabilidad promedio "
                        f"({category_stats['count']} mercados activos)"
                    )
            
            context_text = "\n".join(context_parts) if context_parts else "Sin contexto adicional disponible"
            
            # 4. Single focused LLM call (no multi-agent orchestration)
            # Determine category-specific expertise
            category_expertise = {
                "politics": "analista político experto en México",
                "economy": "analista económico experto en México",
                "security": "analista de seguridad experto en México",
                "rights": "analista de derechos humanos experto en México",
                "environment": "analista ambiental experto en México",
                "mexico-us-relations": "analista de relaciones internacionales experto en México-EU",
                "institutions": "analista institucional experto en México",
                "sports": "analista deportivo experto en México",
                "financial-markets": "analista financiero experto en mercados mexicanos",
                "weather": "meteorólogo experto en clima de México",
                "social-incidents": "analista social experto en eventos e incidentes en México"
            }
            expertise = category_expertise.get(market.category, "analista experto en México")
            
            # Category-specific data sources
            data_sources = {
                "politics": "INE, INEGI, datos electorales, tendencias políticas",
                "economy": "Banxico, INEGI, datos económicos, indicadores financieros",
                "security": "SESNSP, datos de seguridad, estadísticas criminales",
                "sports": "resultados oficiales de ligas, estadísticas deportivas",
                "financial-markets": "BMV, Banxico, datos de mercado, indicadores financieros",
                "weather": "CONAGUA, datos meteorológicos oficiales, patrones climáticos",
                "social-incidents": "reportes oficiales, noticias verificadas, datos de eventos"
            }
            sources = data_sources.get(market.category, "datos oficiales relevantes, tendencias actuales")
            
            prompt = f"""Eres un {expertise}. Estima la probabilidad objetiva de que este mercado de predicción resuelva en SÍ.

MERCADO: "{market.question}"
DESCRIPCIÓN: {market.description or "No disponible"}
CATEGORÍA: {market.category or "General"}

CONTEXTO ADICIONAL:
{context_text}

INSTRUCCIONES:
1. Basándote SOLO en conocimiento general sobre {market.category or "el tema"}, datos históricos, y tendencias actuales en México
2. NO busques evidencia específica - solo estima probabilidad basada en contexto disponible
3. Sé conservador: probabilidades extremas (0.2 o 0.8+) solo con alta confianza
4. Considera: contexto mexicano, {sources}, tendencias recientes
5. Si el contexto es insuficiente, usa probabilidad moderada (0.4-0.6) con baja confianza

RESPONDE EN JSON (solo este objeto, sin markdown, sin código):
{{
    "yes_probability": 0.0-1.0,
    "confidence": 0.0-1.0,
    "reasoning": "1-2 oraciones explicando la estimación",
    "key_factors": ["factor1", "factor2", "factor3"],
    "uncertainty": "low|medium|high"
}}"""
            
            response = await self._call_llm(
                system_prompt="Eres un analista político experto en México, especializado en estimaciones probabilísticas rápidas basadas en contexto limitado.",
                user_prompt=prompt,
                max_tokens=300,  # Shorter response = faster + cheaper
                temperature=0.2
            )
            
            assessment = self._parse_json_response(response)
            
            # Validate and normalize assessment
            yes_prob = float(assessment.get("yes_probability", 0.5))
            yes_prob = max(0.0, min(1.0, yes_prob))  # Clamp to [0, 1]
            
            confidence = float(assessment.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
            
            uncertainty = assessment.get("uncertainty", "medium")
            if uncertainty not in ["low", "medium", "high"]:
                uncertainty = "medium"
            
            # Calculate seed amount based on confidence and uncertainty
            uncertainty_multiplier = {"low": 1.0, "medium": 0.7, "high": 0.4}
            base_seed = 50.0  # Smaller base seed
            recommended_seed = base_seed * confidence * uncertainty_multiplier.get(uncertainty, 0.7)
            recommended_seed = min(recommended_seed, 200.0)  # Cap at 200 credits
            
            return {
                "yes_probability": yes_prob,
                "confidence": confidence,
                "reasoning": assessment.get("reasoning", "Análisis basado en contexto disponible"),
                "key_factors": assessment.get("key_factors", []),
                "uncertainty": uncertainty,
                "recommended_seed_amount": recommended_seed,
                "model_used": self.primary_model
            }
            
        except Exception as e:
            logger.error(f"Error assessing market {market.id}: {e}")
            # Return conservative default
            return {
                "yes_probability": 0.5,
                "confidence": 0.3,
                "reasoning": "No se pudo realizar análisis automático",
                "key_factors": [],
                "uncertainty": "high",
                "recommended_seed_amount": 20.0,
                "error": str(e),
                "model_used": self.primary_model
            }
        finally:
            # Restore original model
            if force_model:
                self.primary_model = original_model
    
    def _get_similar_markets(
        self,
        market: Market,
        db: Session,
        limit: int = 5
    ) -> List[Dict]:
        """Fast DB query for similar markets (by category/keywords)"""
        if not market.category:
            return []
        
        try:
            # Find resolved markets in same category
            similar = db.query(Market).filter(
                Market.category == market.category,
                Market.status == MarketStatus.RESOLVED,
                Market.id != market.id
            ).order_by(desc(Market.resolved_at)).limit(limit).all()
            
            results = []
            for m in similar:
                # Get first trade to estimate initial probability
                first_trade = db.query(MarketTrade).filter(
                    MarketTrade.market_id == m.id
                ).order_by(MarketTrade.created_at).first()
                
                # Estimate initial prob (rough approximation)
                # If first trade was YES, market was likely < 50% initially
                initial_prob = 0.5  # Default
                if first_trade:
                    # This is approximate - ideally we'd track initial liquidity
                    # For now, assume first trade direction indicates initial bias
                    initial_prob = 0.4 if first_trade.outcome == "yes" else 0.6
                
                results.append({
                    "question": m.question[:100],
                    "initial_prob": initial_prob,
                    "resolved": m.winning_outcome
                })
            
            return results
        except Exception as e:
            logger.debug(f"Error getting similar markets: {e}")
            return []
    
    def _get_category_stats(
        self,
        category: str,
        db: Session
    ) -> Optional[Dict]:
        """Get aggregate stats for category (fast DB query)"""
        try:
            from app.services.markets import yes_probability
            
            markets = db.query(Market).filter(
                Market.category == category,
                Market.status == MarketStatus.OPEN
            ).limit(20).all()
            
            if not markets:
                return None
            
            probs = [yes_probability(m) for m in markets]
            return {
                "avg_yes_prob": sum(probs) / len(probs),
                "count": len(markets)
            }
        except Exception as e:
            logger.debug(f"Error getting category stats: {e}")
            return None
