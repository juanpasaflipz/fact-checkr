"""
Embedding Service for Semantic Search and Knowledge Retrieval

This service generates embeddings for claims and enables:
- Semantic similarity search (find related claims)
- Contradiction detection (find conflicting facts)
- Knowledge retrieval (RAG context building)
"""
import os
from typing import List, Dict, Optional
import openai
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate and manage embeddings for claims and facts"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        self.model = "text-embedding-3-small"  # 1536 dimensions, cost-effective
        self.dimensions = 1536
        
        if self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info("✓ Embedding service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            logger.warning("OpenAI API key not found. Embedding service disabled.")
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text"""
        if not self.client:
            return None
        
        try:
            # Truncate long texts (model has 8K token limit)
            truncated_text = text[:8000] if len(text) > 8000 else text
            
            response = self.client.embeddings.create(
                model=self.model,
                input=truncated_text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def embed_claim_with_context(
        self, 
        claim_text: str,
        original_text: str = "",
        status: str = "",
        topics: List[str] = None
    ) -> Optional[List[float]]:
        """Generate contextual embedding for a claim
        
        Combines claim text with metadata for richer semantic representation.
        This helps find similar claims even when wording differs.
        """
        if not self.client:
            return None
        
        # Build context-rich text for embedding
        context_parts = [f"Afirmación: {claim_text}"]
        
        if original_text:
            # Include truncated original for context
            context_parts.append(f"Contexto original: {original_text[:500]}")
        
        if status:
            context_parts.append(f"Estado de verificación: {status}")
        
        if topics:
            context_parts.append(f"Temas: {', '.join(topics)}")
        
        context = "\n".join(context_parts)
        return self.embed_text(context)
    
    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts efficiently"""
        if not self.client:
            return [None] * len(texts)
        
        try:
            # OpenAI supports batch embedding
            truncated_texts = [t[:8000] for t in texts]
            
            response = self.client.embeddings.create(
                model=self.model,
                input=truncated_texts
            )
            
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error in batch embedding: {e}")
            return [None] * len(texts)
    
    async def find_similar_claims(
        self,
        query_text: str = None,
        query_embedding: List[float] = None,
        limit: int = 10,
        threshold: float = 0.75,
        exclude_id: str = None,
        status_filter: str = None
    ) -> List[Dict]:
        """Find semantically similar claims using pgvector
        
        Args:
            query_text: Text to find similar claims for (will be embedded)
            query_embedding: Pre-computed embedding (faster if available)
            limit: Maximum results to return
            threshold: Minimum similarity (0-1, higher = more similar)
            exclude_id: Claim ID to exclude from results
            status_filter: Only return claims with this status
        
        Returns:
            List of similar claims with similarity scores
        """
        from app.database.connection import SessionLocal
        from sqlalchemy import text
        
        # Generate embedding if not provided
        if query_embedding is None:
            if query_text is None:
                return []
            query_embedding = self.embed_text(query_text)
            if query_embedding is None:
                return []
        
        db = SessionLocal()
        try:
            # Convert embedding to PostgreSQL array format
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            
            # Build dynamic query - use CAST instead of :: to avoid SQLAlchemy conflicts
            query = """
                SELECT 
                    id, 
                    claim_text, 
                    original_text,
                    status,
                    explanation,
                    created_at,
                    1 - (embedding <=> CAST(:query_embedding AS vector)) as similarity
                FROM claims
                WHERE embedding IS NOT NULL
                  AND 1 - (embedding <=> CAST(:query_embedding AS vector)) > :threshold
            """
            
            params = {
                "query_embedding": embedding_str,
                "threshold": threshold,
                "limit": limit
            }
            
            if exclude_id:
                query += " AND id != :exclude_id"
                params["exclude_id"] = exclude_id
            
            if status_filter:
                query += " AND status = :status"
                params["status"] = status_filter
            
            query += """
                ORDER BY embedding <=> CAST(:query_embedding AS vector)
                LIMIT :limit
            """
            
            results = db.execute(text(query), params).fetchall()
            
            return [
                {
                    "id": r.id,
                    "claim_text": r.claim_text,
                    "original_text": r.original_text[:200] if r.original_text else "",
                    "status": str(r.status),
                    "explanation": r.explanation,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "similarity": round(r.similarity, 4)
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error finding similar claims: {e}")
            return []
        finally:
            db.close()
    
    async def find_contradicting_facts(
        self,
        claim_text: str,
        entity_ids: List[int] = None,
        threshold: float = 0.7
    ) -> List[Dict]:
        """Find facts that might contradict a claim
        
        Used to detect potential misinformation by comparing against
        verified facts in the knowledge base.
        """
        from app.database.connection import SessionLocal
        
        claim_embedding = self.embed_text(claim_text)
        if not claim_embedding:
            return []
        
        db = SessionLocal()
        try:
            query = """
                SELECT 
                    ek.id,
                    ek.fact_text,
                    ek.confidence,
                    ek.source_claim_id,
                    e.name as entity_name,
                    1 - (ek.fact_embedding <=> :embedding::vector) as similarity
                FROM entity_knowledge ek
                JOIN entities e ON e.id = ek.entity_id
                WHERE ek.fact_embedding IS NOT NULL
                  AND ek.confidence > 0.7
                  AND 1 - (ek.fact_embedding <=> :embedding::vector) > :threshold
            """
            
            params = {
                "embedding": str(claim_embedding),
                "threshold": threshold
            }
            
            if entity_ids:
                query += " AND ek.entity_id = ANY(:entity_ids)"
                params["entity_ids"] = entity_ids
            
            query += """
                ORDER BY ek.fact_embedding <=> :embedding::vector
                LIMIT 10
            """
            
            results = db.execute(query, params).fetchall()
            
            return [
                {
                    "fact_id": r.id,
                    "fact_text": r.fact_text,
                    "entity_name": r.entity_name,
                    "confidence": r.confidence,
                    "source_claim_id": r.source_claim_id,
                    "similarity": round(r.similarity, 4)
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error finding contradicting facts: {e}")
            return []
        finally:
            db.close()
    
    async def update_claim_embedding(self, claim_id: str) -> bool:
        """Update embedding for a specific claim"""
        from app.database.connection import SessionLocal
        from app.database.models import Claim
        
        db = SessionLocal()
        try:
            claim = db.query(Claim).filter(Claim.id == claim_id).first()
            if not claim:
                return False
            
            # Generate contextual embedding
            topics = [t.name for t in claim.topics] if claim.topics else []
            embedding = self.embed_claim_with_context(
                claim_text=claim.claim_text,
                original_text=claim.original_text,
                status=str(claim.status.value) if claim.status else "",
                topics=topics
            )
            
            if embedding:
                db.execute(
                    "UPDATE claims SET embedding = :embedding WHERE id = :claim_id",
                    {"embedding": str(embedding), "claim_id": claim_id}
                )
                db.commit()
                logger.info(f"Updated embedding for claim {claim_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error updating claim embedding: {e}")
            db.rollback()
            return False
        finally:
            db.close()


# Celery task for batch embedding updates
def backfill_embeddings_task():
    """Celery task to backfill embeddings for claims without them"""
    from celery import shared_task
    from app.database.connection import SessionLocal
    from app.database.models import Claim
    
    @shared_task
    def backfill_claim_embeddings(batch_size: int = 100):
        """Process claims without embeddings in batches"""
        service = EmbeddingService()
        db = SessionLocal()
        
        try:
            # Get claims without embeddings
            claims = db.execute("""
                SELECT id, claim_text, original_text, status
                FROM claims
                WHERE embedding IS NULL
                ORDER BY created_at DESC
                LIMIT :batch_size
            """, {"batch_size": batch_size}).fetchall()
            
            if not claims:
                logger.info("No claims need embedding backfill")
                return 0
            
            # Generate embeddings in batch
            texts = [
                f"Afirmación: {c.claim_text}\nContexto: {c.original_text[:500] if c.original_text else ''}"
                for c in claims
            ]
            
            embeddings = service.embed_batch(texts)
            
            # Update database
            updated = 0
            for claim, embedding in zip(claims, embeddings):
                if embedding:
                    db.execute(
                        "UPDATE claims SET embedding = :embedding WHERE id = :id",
                        {"embedding": str(embedding), "id": claim.id}
                    )
                    updated += 1
            
            db.commit()
            logger.info(f"Backfilled embeddings for {updated}/{len(claims)} claims")
            return updated
            
        except Exception as e:
            logger.error(f"Error in embedding backfill: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    return backfill_claim_embeddings

