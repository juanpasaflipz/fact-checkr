from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func, case
import logging

from app.database.connection import get_db
from app.database.models import (
    Claim as DBClaim, 
    Source as DBSource, 
    VerificationStatus as DBVerificationStatus, 
    Topic as DBTopic, 
    Entity as DBEntity,
    claim_topics
)
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)

# Note: /trends prefix is handled by main application inclusion or here
# We'll use a generic router and mount it appropriately or use multiple routers if needed.
# Since these are disparate endpoints (analytics, trends, stats), let's group them or separate them.
# The plan called for `stats.py` to handle all these.

router = APIRouter(tags=["stats"])

@router.get("/stats")
@limiter.limit("60/minute")
async def get_stats(request: Request, db: Session = Depends(get_db)):
    """Get real-time statistics from the database"""
    try:
        # Total claims analyzed
        total_claims = db.query(func.count(DBClaim.id)).scalar() or 0
        
        # Claims by status
        verified_count = db.query(func.count(DBClaim.id)).filter(DBClaim.status == DBVerificationStatus.VERIFIED).scalar() or 0
        debunked_count = db.query(func.count(DBClaim.id)).filter(DBClaim.status == DBVerificationStatus.DEBUNKED).scalar() or 0
        misleading_count = db.query(func.count(DBClaim.id)).filter(DBClaim.status == DBVerificationStatus.MISLEADING).scalar() or 0
        unverified_count = db.query(func.count(DBClaim.id)).filter(DBClaim.status == DBVerificationStatus.UNVERIFIED).scalar() or 0
        
        # Fake news detected (debunked + misleading)
        fake_news_count = debunked_count + misleading_count
        
        # Active sources (sources with at least one claim)
        sources_with_claims = db.query(func.count(func.distinct(DBClaim.source_id))).scalar() or 0
        
        # Recent activity (last 24h)
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_count = db.query(func.count(DBClaim.id)).filter(DBClaim.created_at >= yesterday).scalar() or 0
        
        return {
            "total_analyzed": total_claims,
            "fake_news_detected": fake_news_count,
            "verified": verified_count,
            "active_sources": sources_with_claims,
            "recent_24h": recent_count,
            "trend_percentage": 15, # Placeholder
            "trend_up": True
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        # Return safe default values on error
        return {
            "total_analyzed": 0,
            "fake_news_detected": 0,
            "verified": 0,
            "active_sources": 0,
            "recent_24h": 0,
            "trend_percentage": 0,
            "trend_up": False
        }

@router.get("/trends/summary")
async def get_trends_summary(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get summary of trending topics and activity"""
    try:
        today = datetime.utcnow()
        start_date = today - timedelta(days=days)
        previous_start = start_date - timedelta(days=days)
        
        # Current period claims
        current_claims = db.query(func.count(DBClaim.id)).filter(DBClaim.created_at >= start_date).scalar() or 0
        
        # Previous period claims
        previous_claims = db.query(func.count(DBClaim.id))\
            .filter(DBClaim.created_at >= previous_start, DBClaim.created_at < start_date)\
            .scalar() or 0
            
        # Calculate growth
        growth = 0
        if previous_claims > 0:
            growth = ((current_claims - previous_claims) / previous_claims) * 100
            
        # Status breakdown
        status_breakdown = db.query(
            DBClaim.status,
            func.count(DBClaim.id).label('count')
        ).filter(DBClaim.created_at >= start_date)\
        .group_by(DBClaim.status).all()
        
        return {
            "period_days": days,
            "total_claims": current_claims,
            "previous_period_claims": previous_claims,
            "growth_percentage": round(growth, 1),
            "trend_up": growth > 0,
            "status_breakdown": [
                {"status": str(s.status.value) if hasattr(s.status, 'value') else str(s.status), "count": s.count}
                for s in status_breakdown
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching trends summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching trends summary: {str(e)}"
        )

@router.get("/trends/topics")
async def get_trending_topics(
    days: int = 7,
    limit: int = 8,
    db: Session = Depends(get_db)
):
    """Get trending topics with claim counts"""
    today = datetime.utcnow()
    start_date = today - timedelta(days=days)
    previous_start = start_date - timedelta(days=days)
    
    # Get topics with claim counts for current period
    topics_data = db.query(
        DBTopic.id,
        DBTopic.name,
        DBTopic.slug,
        func.count(DBClaim.id).label('claim_count')
    ).outerjoin(claim_topics, DBTopic.id == claim_topics.c.topic_id)\
     .outerjoin(DBClaim, and_(
         DBClaim.id == claim_topics.c.claim_id,
         DBClaim.created_at >= start_date
     ))\
     .group_by(DBTopic.id, DBTopic.name, DBTopic.slug)\
     .order_by(desc('claim_count'))\
     .limit(limit)\
     .all()
    
    result = []
    for topic in topics_data:
        # Get previous period count
        previous_count = db.query(func.count(DBClaim.id))\
            .join(claim_topics, DBClaim.id == claim_topics.c.claim_id)\
            .filter(
                claim_topics.c.topic_id == topic.id,
                DBClaim.created_at >= previous_start,
                DBClaim.created_at < start_date
            ).scalar() or 0
        
        growth = 0
        if previous_count > 0:
            growth = round(((topic.claim_count - previous_count) / previous_count) * 100, 1)
        
        result.append({
            "id": topic.id,
            "name": topic.name,
            "slug": topic.slug,
            "claim_count": topic.claim_count,
            "previous_count": previous_count,
            "growth_percentage": growth,
            "trend_up": growth >= 0
        })
    
    return result


@router.get("/trends/entities")
async def get_trending_entities(
    days: int = 7,
    limit: int = 15,
    db: Session = Depends(get_db)
):
    """Get trending entities with mention counts"""
    today = datetime.utcnow()
    start_date = today - timedelta(days=days)
    
    # Get all entities
    entities = db.query(DBEntity).all()
    
    # Count how many times entity name appears in recent claims
    result = []
    for entity in entities:
        claim_count = db.query(func.count(DBClaim.id))\
            .filter(
                DBClaim.created_at >= start_date,
                or_(
                    DBClaim.claim_text.ilike(f"%{entity.name}%"),
                    DBClaim.original_text.ilike(f"%{entity.name}%")
                )
            ).scalar() or 0
        
        if claim_count > 0:
            result.append({
                "id": entity.id,
                "name": entity.name,
                "type": entity.entity_type or "unknown",
                "claim_count": claim_count
            })
    
    # Sort by claim count and limit
    result.sort(key=lambda x: x["claim_count"], reverse=True)
    return result[:limit]


@router.get("/trends/platforms")
async def get_platform_activity(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get platform activity breakdown"""
    today = datetime.utcnow()
    start_date = today - timedelta(days=days)
    
    # Get claims by platform
    platform_data = db.query(
        DBSource.platform,
        func.count(DBClaim.id).label('total_count'),
        func.sum(case((DBClaim.status == DBVerificationStatus.DEBUNKED, 1), else_=0)).label('debunked_count'),
        func.sum(case((DBClaim.status == DBVerificationStatus.VERIFIED, 1), else_=0)).label('verified_count')
    ).join(DBClaim, DBClaim.source_id == DBSource.id)\
     .filter(DBClaim.created_at >= start_date)\
     .group_by(DBSource.platform)\
     .order_by(desc('total_count'))\
     .all()
    
    platforms = [
        {
            "platform": p.platform or "Unknown",
            "total_count": p.total_count or 0,
            "debunked_count": p.debunked_count or 0,
            "verified_count": p.verified_count or 0
        }
        for p in platform_data
    ]
    
    return {
        "platforms": platforms,
        "daily_breakdown": {}
    }


@router.get("/analytics")
async def get_analytics(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get analytics data"""
    today = datetime.utcnow()
    start_date = today - timedelta(days=days)
    
    # Claims by day
    daily_claims = db.query(
        func.date(DBClaim.created_at).label('date'),
        func.count(DBClaim.id).label('count')
    ).filter(DBClaim.created_at >= start_date)\
     .group_by(func.date(DBClaim.created_at))\
     .order_by('date')\
     .all()
    
    # Status distribution
    status_dist = db.query(
        DBClaim.status,
        func.count(DBClaim.id).label('count')
    ).filter(DBClaim.created_at >= start_date)\
     .group_by(DBClaim.status)\
     .all()
    
    return {
        "period_days": days,
        "daily_claims": [{"date": str(d.date), "count": d.count} for d in daily_claims],
        "status_distribution": [
            {"status": str(s.status.value) if hasattr(s.status, 'value') else str(s.status), "count": s.count}
            for s in status_dist
        ]
    }
