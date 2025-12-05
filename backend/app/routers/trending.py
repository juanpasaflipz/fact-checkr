"""
Trending Topics API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database.connection import get_db
from app.database.models import TrendingTopic, TopicPriorityQueue, Source
from app.services.topic_prioritizer import TopicPrioritizer
from app.services.trending_detector import TrendingDetector
from app.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api/v1/trending", tags=["Trending Topics"])


@router.get("/topics")
async def get_trending_topics(
    limit: int = Query(20, ge=1, le=100),
    hours: int = Query(24, ge=1, le=168),
    min_score: float = Query(0.3, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    user = Depends(get_optional_user)  # Optional auth
):
    """Get trending topics
    
    Args:
        limit: Maximum number of topics to return
        hours: Hours to look back
        min_score: Minimum priority score
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    topics = db.query(TrendingTopic).filter(
        and_(
            TrendingTopic.detected_at >= cutoff_time,
            TrendingTopic.final_priority_score >= min_score,
            TrendingTopic.status == 'active'
        )
    ).order_by(
        TrendingTopic.final_priority_score.desc()
    ).limit(limit).all()
    
    return {
        "topics": [
            {
                "id": t.id,
                "topic_name": t.topic_name,
                "topic_keywords": t.topic_keywords,
                "trend_score": t.trend_score,
                "engagement_velocity": t.engagement_velocity,
                "cross_platform_correlation": t.cross_platform_correlation,
                "context_relevance_score": t.context_relevance_score,
                "misinformation_risk_score": t.misinformation_risk_score,
                "final_priority_score": t.final_priority_score,
                "detected_at": t.detected_at.isoformat(),
                "topic_metadata": t.topic_metadata
            }
            for t in topics
        ],
        "count": len(topics),
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/topics/{topic_id}")
async def get_topic_details(
    topic_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_optional_user)
):
    """Get detailed information about a trending topic"""
    topic = db.query(TrendingTopic).filter(TrendingTopic.id == topic_id).first()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Get associated sources
    from app.database.models import trending_topic_sources
    sources = db.query(Source).join(
        trending_topic_sources
    ).filter(
        trending_topic_sources.c.topic_id == topic_id
    ).limit(50).all()
    
    # Get context intelligence
    from app.services.context_intelligence import ContextIntelligenceService
    context_service = ContextIntelligenceService()
    topic_key = context_service._normalize_topic_key(
        topic.topic_name, topic.topic_keywords
    )
    context = context_service._get_cached_intelligence(topic_key)
    
    return {
        "topic": {
            "id": topic.id,
            "topic_name": topic.topic_name,
            "topic_keywords": topic.topic_keywords,
            "trend_score": topic.trend_score,
            "engagement_velocity": topic.engagement_velocity,
            "cross_platform_correlation": topic.cross_platform_correlation,
            "context_relevance_score": topic.context_relevance_score,
            "misinformation_risk_score": topic.misinformation_risk_score,
            "final_priority_score": topic.final_priority_score,
            "detected_at": topic.detected_at.isoformat(),
            "topic_metadata": topic.topic_metadata
        },
        "context_intelligence": {
            "political_context": context.political_context if context else None,
            "economic_context": context.economic_context if context else None,
            "social_context": context.social_context if context else None,
            "relevance_score": context.relevance_score if context else None,
            "noise_filter_score": context.noise_filter_score if context else None
        } if context else None,
        "sources_count": len(sources),
        "sources": [
            {
                "id": s.id,
                "platform": s.platform,
                "content": s.content[:200] + "..." if len(s.content) > 200 else s.content,
                "author": s.author,
                "url": s.url,
                "timestamp": s.timestamp.isoformat(),
                "engagement_metrics": s.engagement_metrics
            }
            for s in sources[:20]  # Limit to 20 for response size
        ]
    }


@router.post("/topics/detect")
async def trigger_trending_detection(
    user = Depends(get_current_user)  # Require auth
):
    """Manually trigger trending topic detection"""
    from app.tasks.scraper import detect_and_prioritize_topics
    
    # Trigger async task
    task = detect_and_prioritize_topics.delay()
    
    return {
        "status": "started",
        "task_id": task.id,
        "message": "Trending topic detection started"
    }


@router.get("/priority-queue")
async def get_priority_queue(
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)  # Require auth
):
    """Get priority queue of topics to process"""
    query = db.query(TopicPriorityQueue)
    
    if status:
        query = query.filter(TopicPriorityQueue.processing_status == status)
    
    entries = query.order_by(
        TopicPriorityQueue.priority_score.desc(),
        TopicPriorityQueue.queued_at.asc()
    ).limit(limit).all()
    
    return {
        "queue": [
            {
                "id": e.id,
                "topic_id": e.topic_id,
                "topic_name": e.topic.topic_name,
                "priority_score": e.priority_score,
                "queued_at": e.queued_at.isoformat(),
                "processed_at": e.processed_at.isoformat() if e.processed_at else None,
                "processing_status": e.processing_status
            }
            for e in entries
        ],
        "count": len(entries)
    }

