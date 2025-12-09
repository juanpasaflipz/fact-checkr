"""
Market Similarity Engine

Bootstrap new markets using similar resolved markets.
Uses embeddings to find semantically similar historical markets
and transfer learning from their outcomes.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.embeddings import EmbeddingService
from .models import SimilarMarket

logger = logging.getLogger(__name__)


class MarketSimilarityEngine:
    """
    Find similar historical markets for bootstrapping new market predictions.
    
    Uses embedding-based semantic similarity to identify markets that:
    1. Asked similar questions
    2. Are in similar categories
    3. Have similar resolution patterns
    
    This helps provide initial probability estimates and historical context
    for new markets before trading data accumulates.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
    
    def find_similar_resolved_markets(
        self,
        market_question: str,
        category: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[SimilarMarket]:
        """
        Find similar markets that have already resolved.
        
        Args:
            market_question: The question of the new market
            category: Optional category to prioritize
            top_k: Maximum number of similar markets to return
            min_similarity: Minimum similarity threshold (0-1)
        
        Returns:
            List of SimilarMarket objects with similarity scores
        """
        try:
            # Generate embedding for the market question
            query_embedding = self.embedding_service.embed_text(market_question)
            
            if not query_embedding:
                logger.warning("Could not generate embedding for market question")
                return self._fallback_similarity_search(market_question, category, top_k)
            
            # Search for similar resolved markets using pgvector
            # We need to store market embeddings first
            similar_markets = self._vector_similarity_search(
                query_embedding=query_embedding,
                category=category,
                top_k=top_k,
                min_similarity=min_similarity
            )
            
            if similar_markets:
                return similar_markets
            
            # Fallback to text-based similarity
            return self._fallback_similarity_search(market_question, category, top_k)
            
        except Exception as e:
            logger.error(f"Error finding similar markets: {e}")
            return []
    
    def _vector_similarity_search(
        self,
        query_embedding: List[float],
        category: Optional[str],
        top_k: int,
        min_similarity: float
    ) -> List[SimilarMarket]:
        """
        Search using pgvector similarity.
        
        Requires markets to have embeddings stored in a question_embedding column.
        """
        try:
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            
            # Build query with optional category filter
            query = """
                SELECT 
                    m.id,
                    m.question,
                    m.category,
                    m.winning_outcome,
                    m.yes_liquidity / (m.yes_liquidity + m.no_liquidity) as final_probability,
                    m.resolved_at,
                    1 - (m.question_embedding <=> CAST(:embedding AS vector)) as similarity
                FROM markets m
                WHERE m.status = 'resolved'
                  AND m.winning_outcome IS NOT NULL
                  AND m.question_embedding IS NOT NULL
                  AND 1 - (m.question_embedding <=> CAST(:embedding AS vector)) > :min_sim
            """
            
            params = {
                "embedding": embedding_str,
                "min_sim": min_similarity
            }
            
            if category:
                query += " AND m.category = :category"
                params["category"] = category
            
            query += """
                ORDER BY m.question_embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
            """
            params["limit"] = top_k
            
            results = self.db.execute(text(query), params).fetchall()
            
            similar_markets = []
            for r in results:
                # Get key factors from prediction history if available
                key_factors = self._get_market_key_factors(r.id)
                
                similar_markets.append(SimilarMarket(
                    market_id=r.id,
                    question=r.question,
                    category=r.category or "General",
                    outcome=r.winning_outcome,
                    final_probability=float(r.final_probability) if r.final_probability else 0.5,
                    similarity_score=float(r.similarity),
                    resolution_date=r.resolved_at,
                    key_factors=key_factors
                ))
            
            return similar_markets
            
        except Exception as e:
            # pgvector might not be available or embeddings not stored
            logger.debug(f"Vector similarity search failed: {e}")
            return []
    
    def _fallback_similarity_search(
        self,
        market_question: str,
        category: Optional[str],
        top_k: int
    ) -> List[SimilarMarket]:
        """
        Fallback text-based similarity search using PostgreSQL full-text search.
        """
        try:
            # Extract key terms from the question
            # Simple approach: use the question directly with full-text search
            
            query = """
                SELECT 
                    m.id,
                    m.question,
                    m.category,
                    m.winning_outcome,
                    m.yes_liquidity / (m.yes_liquidity + m.no_liquidity) as final_probability,
                    m.resolved_at,
                    ts_rank(
                        to_tsvector('spanish', m.question || ' ' || COALESCE(m.description, '')),
                        plainto_tsquery('spanish', :query)
                    ) as rank
                FROM markets m
                WHERE m.status = 'resolved'
                  AND m.winning_outcome IS NOT NULL
            """
            
            params = {"query": market_question}
            
            if category:
                query += " AND m.category = :category"
                params["category"] = category
            
            query += """
                ORDER BY rank DESC
                LIMIT :limit
            """
            params["limit"] = top_k
            
            results = self.db.execute(text(query), params).fetchall()
            
            similar_markets = []
            for r in results:
                if r.rank and r.rank > 0:  # Only include if there's some text match
                    # Normalize rank to 0-1 similarity score
                    similarity = min(1.0, r.rank / 10.0)  # Approximate normalization
                    
                    key_factors = self._get_market_key_factors(r.id)
                    
                    similar_markets.append(SimilarMarket(
                        market_id=r.id,
                        question=r.question,
                        category=r.category or "General",
                        outcome=r.winning_outcome,
                        final_probability=float(r.final_probability) if r.final_probability else 0.5,
                        similarity_score=similarity,
                        resolution_date=r.resolved_at,
                        key_factors=key_factors
                    ))
            
            return similar_markets
            
        except Exception as e:
            logger.error(f"Fallback similarity search failed: {e}")
            return []
    
    def _get_market_key_factors(self, market_id: int) -> List[str]:
        """Get key factors from prediction history for a market."""
        try:
            result = self.db.execute(
                text("""
                    SELECT key_factors
                    FROM market_prediction_factors
                    WHERE market_id = :market_id
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"market_id": market_id}
            ).fetchone()
            
            if result and result.key_factors:
                factors = result.key_factors
                if isinstance(factors, list):
                    return [f.get("factor", str(f))[:100] for f in factors[:3]]
            
            return []
            
        except Exception:
            return []
    
    def transfer_initial_probability(
        self,
        similar_markets: List[SimilarMarket],
        default_prob: float = 0.5
    ) -> float:
        """
        Calculate an initial probability estimate based on similar markets.
        
        Uses weighted average of similar market outcomes, weighted by similarity.
        
        Args:
            similar_markets: List of similar resolved markets
            default_prob: Default probability if no similar markets found
        
        Returns:
            Initial probability estimate (0-1)
        """
        if not similar_markets:
            return default_prob
        
        # Weight by similarity score
        weighted_sum = 0.0
        total_weight = 0.0
        
        for market in similar_markets:
            # Outcome probability: 1 if YES won, 0 if NO won
            outcome_prob = 1.0 if market.outcome == "yes" else 0.0
            
            # Weight by similarity squared (emphasize more similar markets)
            weight = market.similarity_score ** 2
            
            weighted_sum += outcome_prob * weight
            total_weight += weight
        
        if total_weight == 0:
            return default_prob
        
        # Calculate weighted average
        transferred_prob = weighted_sum / total_weight
        
        # Regress toward 0.5 to avoid overconfidence
        # More regression with fewer similar markets
        regression_factor = min(0.5, 1.0 / (len(similar_markets) + 1))
        transferred_prob = transferred_prob * (1 - regression_factor) + 0.5 * regression_factor
        
        # Clamp to reasonable range
        return max(0.15, min(0.85, transferred_prob))
    
    def get_historical_accuracy_for_category(
        self,
        category: str,
        timeframe_days: int = 365
    ) -> Dict[str, Any]:
        """
        Get historical prediction accuracy statistics for a category.
        
        Useful for understanding how well predictions perform in different categories.
        
        Args:
            category: Market category
            timeframe_days: How far back to look
        
        Returns:
            Dictionary with accuracy statistics
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=timeframe_days)
            
            result = self.db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_markets,
                        AVG(
                            CASE 
                                WHEN winning_outcome = 'yes' 
                                THEN yes_liquidity / (yes_liquidity + no_liquidity)
                                ELSE 1 - yes_liquidity / (yes_liquidity + no_liquidity)
                            END
                        ) as avg_correct_prob,
                        SUM(CASE WHEN winning_outcome = 'yes' THEN 1 ELSE 0 END) as yes_outcomes,
                        SUM(CASE WHEN winning_outcome = 'no' THEN 1 ELSE 0 END) as no_outcomes
                    FROM markets
                    WHERE category = :category
                      AND status = 'resolved'
                      AND resolved_at >= :cutoff
                """),
                {"category": category, "cutoff": cutoff}
            ).fetchone()
            
            if result and result.total_markets > 0:
                return {
                    "category": category,
                    "total_markets": result.total_markets,
                    "avg_market_accuracy": float(result.avg_correct_prob) if result.avg_correct_prob else 0.5,
                    "yes_rate": result.yes_outcomes / result.total_markets,
                    "no_rate": result.no_outcomes / result.total_markets,
                    "timeframe_days": timeframe_days
                }
            
            return {
                "category": category,
                "total_markets": 0,
                "avg_market_accuracy": 0.5,
                "yes_rate": 0.5,
                "no_rate": 0.5,
                "timeframe_days": timeframe_days
            }
            
        except Exception as e:
            logger.error(f"Error getting category accuracy: {e}")
            return {
                "category": category,
                "total_markets": 0,
                "error": str(e)
            }
    
    async def update_market_embedding(self, market_id: int) -> bool:
        """
        Generate and store embedding for a market's question.
        
        Should be called when a new market is created.
        """
        try:
            # Get market question
            result = self.db.execute(
                text("""
                    SELECT question, description
                    FROM markets
                    WHERE id = :market_id
                """),
                {"market_id": market_id}
            ).fetchone()
            
            if not result:
                return False
            
            # Generate embedding
            text_to_embed = result.question
            if result.description:
                text_to_embed += " " + result.description
            
            embedding = self.embedding_service.embed_text(text_to_embed)
            
            if not embedding:
                return False
            
            # Store embedding
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            
            self.db.execute(
                text("""
                    UPDATE markets
                    SET question_embedding = CAST(:embedding AS vector)
                    WHERE id = :market_id
                """),
                {"embedding": embedding_str, "market_id": market_id}
            )
            self.db.commit()
            
            logger.info(f"Updated embedding for market {market_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating market embedding: {e}")
            self.db.rollback()
            return False
