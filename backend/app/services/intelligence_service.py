from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.database.models import Claim, Entity, Topic, claim_topics
from app.services.embeddings import EmbeddingService
from app.services.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)

class IntelligenceService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.rag_pipeline = RAGPipeline()

    async def find_similar_claims(self, query: str, limit: int, threshold: float, status: Optional[str] = None):
        return await self.embedding_service.find_similar_claims(
            query_text=query,
            limit=limit,
            threshold=threshold,
            status_filter=status
        )

    async def check_contradictions(self, claim_text: str):
        contradictions = await self.embedding_service.find_contradicting_facts(
            claim_text=claim_text,
            threshold=0.7
        )
        
        similar_debunked = await self.embedding_service.find_similar_claims(
            query_text=claim_text,
            limit=5,
            threshold=0.8,
            status_filter="Debunked"
        )
        
        return {
            "claim": claim_text,
            "potential_contradictions": contradictions,
            "similar_debunked_claims": similar_debunked,
            "alert_level": "high" if (contradictions or similar_debunked) else "none"
        }

    async def get_emerging_narratives(self, hours: int, min_claims: int):
        try:
            time_threshold = datetime.utcnow() - timedelta(hours=hours)
            
            # Count total claims in period for context
            total_claims = self.db.query(Claim).filter(
                Claim.created_at >= time_threshold
            ).count()

            if total_claims < min_claims:
                return {
                    "message": "Not enough recent claims for narrative detection",
                    "claim_count": total_claims,
                    "narratives": []
                }
            
            # Use the SQL query from the router, but encapsulated here
            # Ideally this would be a proper ORM query or stored procedure
            topic_clusters = self.db.execute(text("""
                SELECT 
                    t.name as topic_name,
                    t.slug as topic_slug,
                    COUNT(DISTINCT c.id) as claim_count,
                    COUNT(CASE WHEN c.status = 'Debunked' THEN 1 END) as debunked_count,
                    MIN(c.created_at) as first_seen,
                    MAX(c.created_at) as last_seen
                FROM claims c
                JOIN claim_topics ct ON c.id = ct.claim_id
                JOIN topics t ON t.id = ct.topic_id
                WHERE c.created_at >= :time_threshold
                GROUP BY t.id, t.name, t.slug
                HAVING COUNT(DISTINCT c.id) >= :min_claims
                ORDER BY claim_count DESC
            """), {"time_threshold": time_threshold, "min_claims": min_claims})
            
            narratives = []
            for row in topic_clusters.fetchall():
                debunked_ratio = row.debunked_count / row.claim_count if row.claim_count > 0 else 0
                hours_active = (row.last_seen - row.first_seen).total_seconds() / 3600 if row.last_seen != row.first_seen else 1
                velocity = row.claim_count / max(hours_active, 1)
                
                risk_score = (
                    debunked_ratio * 0.4 +
                    min(velocity / 5, 1.0) * 0.3 +
                    min(row.claim_count / 20, 1.0) * 0.3
                )
                
                narratives.append({
                    "topic": row.topic_name,
                    "slug": row.topic_slug,
                    "claim_count": row.claim_count,
                    "debunked_count": row.debunked_count,
                    "debunked_ratio": round(debunked_ratio, 2),
                    "first_seen": row.first_seen.isoformat() if row.first_seen else None,
                    "last_seen": row.last_seen.isoformat() if row.last_seen else None,
                    "spread_velocity": round(velocity, 2),
                    "risk_score": round(risk_score, 2),
                    "alert_level": "high" if risk_score > 0.7 else "medium" if risk_score > 0.4 else "low"
                })
            
            narratives.sort(key=lambda x: x["risk_score"], reverse=True)
            
            return {
                "time_window_hours": hours,
                "total_claims_analyzed": total_claims,
                "narratives": narratives,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detecting narratives: {e}")
            raise

    async def get_entity_profile(self, entity_name: str, days: int):
        entity = self.db.query(Entity).filter(
            Entity.name.ilike(f"%{entity_name}%")
        ).first()
        
        if not entity:
            return None
        
        time_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Get claims using a cleaner ORM approach or keep specific SQL if complex text search is needed
        claims = self.db.query(Claim).filter(
            Claim.claim_text.ilike(f"%{entity.name}%"),
            Claim.created_at >= time_threshold
        ).order_by(Claim.created_at.desc()).limit(50).all()
        
        total_claims = len(claims)
        status_breakdown = {}
        for claim in claims:
            status = str(claim.status.value) if hasattr(claim.status, 'value') else str(claim.status)
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
        # This SQL is fine for specific analytic aggregations
        related = self.db.execute(text("""
            SELECT 
                e2.name,
                e2.entity_type,
                COUNT(*) as co_occurrence_count
            FROM claims c1
            JOIN entities e2 ON c1.claim_text ILIKE '%' || e2.name || '%'
            WHERE c1.claim_text ILIKE :pattern
            AND e2.id != :entity_id
            AND c1.created_at >= :time_threshold
            GROUP BY e2.id, e2.name, e2.entity_type
            ORDER BY co_occurrence_count DESC
            LIMIT 10
        """), {
            "pattern": f"%{entity.name}%",
            "entity_id": entity.id,
            "time_threshold": time_threshold
        }).fetchall()
        
        return {
            "entity": {
                "id": entity.id,
                "name": entity.name,
                "type": entity.entity_type,
                "position": getattr(entity, 'position', None),
                "political_affiliation": getattr(entity, 'political_affiliation', None)
            },
            "period_days": days,
            "statistics": {
                "total_claims": total_claims,
                "status_breakdown": status_breakdown,
                "debunked_ratio": status_breakdown.get("Debunked", 0) / max(total_claims, 1)
            },
            "related_entities": [
                {"name": r.name, "type": r.entity_type, "co_occurrences": r.co_occurrence_count}
                for r in related
            ],
            "recent_claims": [
                {
                    "id": c.id,
                    "claim": c.claim_text[:200],
                    "status": str(c.status.value) if hasattr(c.status, 'value') else str(c.status),
                    "date": c.created_at.isoformat()
                }
                for c in claims[:10]
            ]
        }

    async def get_realtime_alerts(self):
        alerts = []
        six_hours_ago = datetime.utcnow() - timedelta(hours=6)
        
        # Logic moved from router
        velocity_alerts = self.db.execute(text("""
            SELECT 
                t.name as topic,
                COUNT(*) as claim_count,
                COUNT(CASE WHEN c.status = 'Debunked' THEN 1 END) as debunked
            FROM claims c
            JOIN claim_topics ct ON c.id = ct.claim_id
            JOIN topics t ON t.id = ct.topic_id
            WHERE c.created_at >= :threshold
            GROUP BY t.id, t.name
            HAVING COUNT(*) >= 5
            ORDER BY COUNT(*) DESC
        """), {"threshold": six_hours_ago})
        
        for row in velocity_alerts.fetchall():
            alerts.append({
                "type": "high_velocity",
                "severity": "high" if row.claim_count > 10 else "medium",
                "topic": row.topic,
                "claim_count": row.claim_count,
                "debunked_count": row.debunked,
                "message": f"Alta actividad en tema '{row.topic}': {row.claim_count} claims en 6 horas"
            })

        # Duplicate detection (simplified)
        duplicate_alerts = self.db.execute(text("""
            SELECT 
                claim_text,
                COUNT(*) as occurrence_count,
                array_agg(DISTINCT s.platform) as platforms
            FROM claims c
            JOIN sources s ON s.id = c.source_id
            WHERE c.created_at >= :threshold
            GROUP BY claim_text
            HAVING COUNT(*) >= 3
        """), {"threshold": six_hours_ago})
        
        for row in duplicate_alerts.fetchall():
             alerts.append({
                "type": "potential_coordination",
                "severity": "high",
                "claim_preview": row.claim_text[:150] + "...",
                "occurrence_count": row.occurrence_count,
                "platforms": row.platforms,
                "message": f"Mismo claim aparece {row.occurrence_count} veces en múltiples plataformas"
            })
            
        return {
            "alerts": alerts,
            "alert_count": len(alerts),
            "checked_at": datetime.utcnow().isoformat(),
            "time_window": "6 hours"
        }

