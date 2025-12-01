"""
Intelligence API Router

Premium features for researchers, journalists, and media organizations:
- Emerging narrative detection
- Entity network analysis  
- Real-time misinformation alerts
- Research data export
- Similar claim search
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.database.connection import get_db
from app.auth import get_optional_user
from app.services.embeddings import EmbeddingService
from app.services.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/intelligence", tags=["Intelligence"])


# Dependency for premium features (placeholder - integrate with subscription)
async def require_premium(user = Depends(get_optional_user)):
    """Check if user has premium access
    
    TODO: Integrate with subscription system
    For now, allows all authenticated users
    """
    # In production, check user subscription tier
    # if not user or user.subscription.tier not in ["pro", "team", "enterprise"]:
    #     raise HTTPException(status_code=403, detail="Premium subscription required")
    return user


@router.get("/similar-claims")
async def find_similar_claims(
    query: str = Query(..., min_length=10, description="Text to find similar claims for"),
    limit: int = Query(10, ge=1, le=50),
    threshold: float = Query(0.7, ge=0.5, le=0.99),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Find semantically similar claims using AI embeddings.
    
    Useful for:
    - Detecting repeat misinformation
    - Finding related fact-checks
    - Research on claim patterns
    """
    embedding_service = EmbeddingService()
    
    similar = await embedding_service.find_similar_claims(
        query_text=query,
        limit=limit,
        threshold=threshold,
        status_filter=status
    )
    
    return {
        "query": query,
        "threshold": threshold,
        "results": similar,
        "count": len(similar)
    }


@router.get("/contradictions")
async def check_contradictions(
    claim: str = Query(..., min_length=10),
    db: Session = Depends(get_db),
    user = Depends(require_premium)
):
    """
    Check if a claim contradicts known verified facts.
    
    Premium feature for journalists and researchers.
    """
    embedding_service = EmbeddingService()
    
    contradictions = await embedding_service.find_contradicting_facts(
        claim_text=claim,
        threshold=0.7
    )
    
    # Also check for similar debunked claims
    similar_debunked = await embedding_service.find_similar_claims(
        query_text=claim,
        limit=5,
        threshold=0.8,
        status_filter="Debunked"
    )
    
    return {
        "claim": claim,
        "potential_contradictions": contradictions,
        "similar_debunked_claims": similar_debunked,
        "alert_level": "high" if (contradictions or similar_debunked) else "none"
    }


@router.get("/narratives/emerging")
async def get_emerging_narratives(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    min_claims: int = Query(3, ge=2, le=20),
    db: Session = Depends(get_db),
    user = Depends(require_premium)
):
    """
    Detect emerging misinformation narratives.
    
    Uses clustering on claim embeddings to identify groups of 
    related claims spreading together.
    
    Premium feature for media organizations.
    """
    from sqlalchemy import text
    
    try:
        # Get recent claims with embeddings
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        result = db.execute(text("""
            SELECT 
                id, claim_text, status, created_at,
                embedding::text as embedding_str
            FROM claims
            WHERE created_at >= :time_threshold
            AND embedding IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 500
        """), {"time_threshold": time_threshold})
        
        claims = result.fetchall()
        
        if len(claims) < min_claims:
            return {
                "message": "Not enough recent claims for narrative detection",
                "claim_count": len(claims),
                "narratives": []
            }
        
        # Simple clustering based on topic co-occurrence
        # Full implementation would use DBSCAN on embeddings
        from app.database.models import claim_topics, Topic
        
        topic_clusters = db.execute(text("""
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
        
        # Sort by risk score
        narratives.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return {
            "time_window_hours": hours,
            "total_claims_analyzed": len(claims),
            "narratives": narratives,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error detecting narratives: {e}")
        raise HTTPException(status_code=500, detail="Error detecting narratives")


@router.get("/entities/{entity_name}/profile")
async def get_entity_profile(
    entity_name: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user = Depends(require_premium)
):
    """
    Get comprehensive profile for a political entity.
    
    Includes:
    - Claim statistics
    - Verified facts
    - Related entities
    - Trend analysis
    """
    from sqlalchemy import text, func
    from app.database.models import Entity, Claim
    
    # Find entity
    entity = db.query(Entity).filter(
        Entity.name.ilike(f"%{entity_name}%")
    ).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    time_threshold = datetime.utcnow() - timedelta(days=days)
    
    # Get claims mentioning this entity
    claims_query = db.execute(text("""
        SELECT 
            c.id, c.claim_text, c.status, c.created_at, c.explanation
        FROM claims c
        WHERE c.claim_text ILIKE :pattern
        AND c.created_at >= :time_threshold
        ORDER BY c.created_at DESC
        LIMIT 50
    """), {"pattern": f"%{entity.name}%", "time_threshold": time_threshold})
    
    claims = claims_query.fetchall()
    
    # Calculate statistics
    total_claims = len(claims)
    status_breakdown = {}
    for claim in claims:
        status = str(claim.status)
        status_breakdown[status] = status_breakdown.get(status, 0) + 1
    
    # Get known facts
    facts = []
    try:
        facts_query = db.execute(text("""
            SELECT fact_text, fact_type, confidence, verified_at
            FROM entity_knowledge
            WHERE entity_id = :entity_id
            AND confidence > 0.7
            ORDER BY confidence DESC
            LIMIT 10
        """), {"entity_id": entity.id})
        facts = [
            {
                "fact": f.fact_text,
                "type": f.fact_type,
                "confidence": f.confidence
            }
            for f in facts_query.fetchall()
        ]
    except:
        pass  # Table might not exist yet
    
    # Get co-occurring entities
    related = db.execute(text("""
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
    })
    
    related_entities = [
        {
            "name": r.name,
            "type": r.entity_type,
            "co_occurrences": r.co_occurrence_count
        }
        for r in related.fetchall()
    ]
    
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
        "known_facts": facts,
        "related_entities": related_entities,
        "recent_claims": [
            {
                "id": c.id,
                "claim": c.claim_text[:200],
                "status": str(c.status),
                "date": c.created_at.isoformat()
            }
            for c in claims[:10]
        ]
    }


@router.get("/alerts/realtime")
async def get_realtime_alerts(
    db: Session = Depends(get_db),
    user = Depends(require_premium)
):
    """
    Get real-time misinformation alerts.
    
    Flags:
    - High-velocity claim clusters
    - Potential contradiction with verified facts
    - Repeat of previously debunked claims
    """
    from sqlalchemy import text
    
    alerts = []
    
    # Check for high-velocity topics (>5 claims in last 6 hours)
    six_hours_ago = datetime.utcnow() - timedelta(hours=6)
    
    velocity_alerts = db.execute(text("""
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
    
    # Check for potential coordinated campaigns (same claim appearing multiple times)
    duplicate_alerts = db.execute(text("""
        SELECT 
            claim_text,
            COUNT(*) as occurrence_count,
            array_agg(DISTINCT platform) as platforms
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


@router.get("/export/research")
async def export_research_data(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    status: Optional[str] = None,
    topic: Optional[str] = None,
    format: str = Query("json", description="Export format: json or csv"),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
    user = Depends(require_premium)
):
    """
    Export claim data for research purposes.
    
    Includes:
    - Full claim text and verification
    - Source information
    - Topic classification
    - Entity mentions
    
    Premium feature for researchers.
    """
    from sqlalchemy import text
    from datetime import datetime
    
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Build query
    query = """
        SELECT 
            c.id,
            c.claim_text,
            c.original_text,
            c.status::text,
            c.explanation,
            c.created_at,
            s.platform,
            s.author,
            s.url as source_url,
            array_agg(DISTINCT t.name) as topics
        FROM claims c
        LEFT JOIN sources s ON s.id = c.source_id
        LEFT JOIN claim_topics ct ON c.id = ct.claim_id
        LEFT JOIN topics t ON t.id = ct.topic_id
        WHERE c.created_at >= :start_date
        AND c.created_at <= :end_date
    """
    
    params = {"start_date": start, "end_date": end}
    
    if status:
        query += " AND c.status = :status"
        params["status"] = status
    
    if topic:
        query += " AND t.slug = :topic"
        params["topic"] = topic
    
    query += """
        GROUP BY c.id, s.id
        ORDER BY c.created_at DESC
        LIMIT :limit
    """
    params["limit"] = limit
    
    result = db.execute(text(query), params)
    claims = result.fetchall()
    
    data = [
        {
            "id": c.id,
            "claim_text": c.claim_text,
            "original_text": c.original_text,
            "status": c.status,
            "explanation": c.explanation,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "platform": c.platform,
            "author": c.author,
            "source_url": c.source_url,
            "topics": [t for t in c.topics if t] if c.topics else []
        }
        for c in claims
    ]
    
    if format == "csv":
        import csv
        from io import StringIO
        from fastapi.responses import Response
        
        output = StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            for row in data:
                row["topics"] = ";".join(row["topics"]) if row["topics"] else ""
                writer.writerow(row)
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=factcheckr_export_{start_date}_{end_date}.csv"
            }
        )
    
    return {
        "export_date": datetime.utcnow().isoformat(),
        "date_range": {"start": start_date, "end": end_date},
        "filters": {"status": status, "topic": topic},
        "count": len(data),
        "data": data
    }

