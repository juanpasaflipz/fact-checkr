"""Comprehensive analytics endpoints for visualizations"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_, case
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from app.database.connection import get_db
from app.database.models import (
    Claim, Source, Topic, TrendingTopic,
    VerificationStatus, Market
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# Response Models
class TopicDistribution(BaseModel):
    topic_id: int
    topic_name: str
    topic_slug: str
    claim_count: int
    verified_count: int
    debunked_count: int
    misleading_count: int
    unverified_count: int
    percentage: float


class PlatformDistribution(BaseModel):
    platform: str
    total_count: int
    verified_count: int
    debunked_count: int
    misleading_count: int
    unverified_count: int
    percentage: float
    avg_engagement: Optional[float] = None


class EngagementMetrics(BaseModel):
    platform: str
    total_likes: int
    total_retweets: int
    total_replies: int
    total_views: int
    avg_likes: float
    avg_retweets: float
    avg_replies: float
    avg_views: float
    post_count: int


class DailyActivity(BaseModel):
    date: str
    claims_count: int
    verified_count: int
    debunked_count: int
    misleading_count: int
    unverified_count: int


class TopicComparison(BaseModel):
    topic_id: int
    topic_name: str
    topic_slug: str
    total_claims: int
    verification_rate: float
    debunk_rate: float
    avg_confidence: float
    engagement_score: float
    trend_score: Optional[float] = None


class AudienceStats(BaseModel):
    total_sources: int
    unique_authors: int
    platforms: List[PlatformDistribution]
    engagement_metrics: List[EngagementMetrics]
    top_authors: List[Dict[str, Any]]


@router.get("/topics/distribution")
async def get_topic_distribution(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get topic distribution with claim counts and verification status breakdown"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get total claims for percentage calculation
    total_claims = db.query(func.count(Claim.id)).filter(
        Claim.created_at >= start_date
    ).scalar() or 1
    
    # Get topic distribution with status breakdown
    topic_data = db.query(
        Topic.id,
        Topic.name,
        Topic.slug,
        func.count(Claim.id).label('claim_count'),
        func.sum(case((Claim.status == VerificationStatus.VERIFIED, 1), else_=0)).label('verified_count'),
        func.sum(case((Claim.status == VerificationStatus.DEBUNKED, 1), else_=0)).label('debunked_count'),
        func.sum(case((Claim.status == VerificationStatus.MISLEADING, 1), else_=0)).label('misleading_count'),
        func.sum(case((Claim.status == VerificationStatus.UNVERIFIED, 1), else_=0)).label('unverified_count')
    ).join(
        Claim.topics, isouter=True
    ).filter(
        Claim.created_at >= start_date
    ).group_by(
        Topic.id, Topic.name, Topic.slug
    ).order_by(
        desc('claim_count')
    ).limit(limit).all()
    
    result = []
    for t in topic_data:
        claim_count = t.claim_count or 0
        result.append(TopicDistribution(
            topic_id=t.id,
            topic_name=t.name,
            topic_slug=t.slug,
            claim_count=claim_count,
            verified_count=int(t.verified_count or 0),
            debunked_count=int(t.debunked_count or 0),
            misleading_count=int(t.misleading_count or 0),
            unverified_count=int(t.unverified_count or 0),
            percentage=(claim_count / total_claims) * 100 if total_claims > 0 else 0
        ))
    
    return {"topics": result, "total_claims": total_claims, "period_days": days}


@router.get("/platforms/distribution")
async def get_platform_distribution(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get platform distribution with engagement metrics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get total sources for percentage calculation
    total_sources = db.query(func.count(Source.id)).filter(
        Source.scraped_at >= start_date
    ).scalar() or 1
    
    # Get platform distribution with status breakdown
    platform_data = db.query(
        Source.platform,
        func.count(Source.id).label('total_count'),
        func.sum(case((Claim.status == VerificationStatus.VERIFIED, 1), else_=0)).label('verified_count'),
        func.sum(case((Claim.status == VerificationStatus.DEBUNKED, 1), else_=0)).label('debunked_count'),
        func.sum(case((Claim.status == VerificationStatus.MISLEADING, 1), else_=0)).label('misleading_count'),
        func.sum(case((Claim.status == VerificationStatus.UNVERIFIED, 1), else_=0)).label('unverified_count')
    ).join(
        Claim, Claim.source_id == Source.id, isouter=True
    ).filter(
        Source.scraped_at >= start_date
    ).group_by(
        Source.platform
    ).order_by(
        desc('total_count')
    ).all()
    
    # Platform name mapping for better display
    platform_display_names = {
        'X (Twitter)': 'Twitter/X',
        'Facebook': 'Facebook',
        'Instagram': 'Instagram',
        'Google News': 'Google News',
        'Twitter': 'Twitter/X',
        'X': 'Twitter/X'
    }

    # Calculate engagement metrics per platform
    platforms = []
    for p in platform_data:
        platform = p.platform or "Unknown"
        display_name = platform_display_names.get(platform, platform)
        
        # Get engagement metrics for this platform
        sources_with_engagement = db.query(Source).filter(
            and_(
                Source.platform == platform,
                Source.scraped_at >= start_date,
                Source.engagement_metrics.isnot(None)
            )
        ).all()
        
        total_likes = 0
        total_retweets = 0
        total_replies = 0
        total_views = 0
        engagement_count = 0
        
        for source in sources_with_engagement:
            engagement_data = source.engagement_metrics
            if engagement_data is not None:
                try:
                    if isinstance(engagement_data, dict):
                        metrics = engagement_data
                    else:
                        metrics = json.loads(str(engagement_data))
                    total_likes += int(metrics.get('likes', 0) or 0)
                    total_retweets += int(metrics.get('retweets', 0) or 0)
                    total_replies += int(metrics.get('replies', 0) or 0)
                    total_views += int(metrics.get('views', 0) or 0)
                    engagement_count += 1
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
        
        avg_engagement = None
        if engagement_count > 0:
            avg_engagement = (total_likes + total_retweets + total_replies + total_views) / engagement_count
        
        platforms.append(PlatformDistribution(
            platform=display_name,
            total_count=int(p.total_count or 0),
            verified_count=int(p.verified_count or 0),
            debunked_count=int(p.debunked_count or 0),
            misleading_count=int(p.misleading_count or 0),
            unverified_count=int(p.unverified_count or 0),
            percentage=(int(p.total_count or 0) / total_sources) * 100 if total_sources > 0 else 0,
            avg_engagement=avg_engagement
        ))
    
    return {"platforms": platforms, "total_sources": total_sources, "period_days": days}


@router.get("/engagement/metrics")
async def get_engagement_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get detailed engagement metrics by platform"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all sources with engagement metrics
    sources = db.query(Source).filter(
        and_(
            Source.scraped_at >= start_date,
            Source.engagement_metrics.isnot(None)
        )
    ).all()
    
    # Aggregate by platform
    platform_metrics: Dict[str, Dict[str, Any]] = {}
    
    for source in sources:
        platform_str = str(source.platform) if getattr(source, 'platform', None) is not None else "Unknown"
        
        if platform_str not in platform_metrics:
            platform_metrics[platform_str] = {
                "total_likes": 0,
                "total_retweets": 0,
                "total_replies": 0,
                "total_views": 0,
                "post_count": 0
            }
        
        engagement_data = source.engagement_metrics
        if engagement_data is not None:
            try:
                if isinstance(engagement_data, dict):
                    metrics = engagement_data
                else:
                    metrics = json.loads(str(engagement_data))
                platform_metrics[platform_str]["total_likes"] += int(metrics.get('likes', 0) or 0)
                platform_metrics[platform_str]["total_retweets"] += int(metrics.get('retweets', 0) or 0)
                platform_metrics[platform_str]["total_replies"] += int(metrics.get('replies', 0) or 0)
                platform_metrics[platform_str]["total_views"] += int(metrics.get('views', 0) or 0)
                platform_metrics[platform_str]["post_count"] += 1
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
    
    result = []
    for platform, metrics in platform_metrics.items():
        count = metrics["post_count"]
        if count > 0:
            result.append(EngagementMetrics(
                platform=platform,
                total_likes=metrics["total_likes"],
                total_retweets=metrics["total_retweets"],
                total_replies=metrics["total_replies"],
                total_views=metrics["total_views"],
                avg_likes=metrics["total_likes"] / count,
                avg_retweets=metrics["total_retweets"] / count,
                avg_replies=metrics["total_replies"] / count,
                avg_views=metrics["total_views"] / count,
                post_count=count
            ))
    
    # Sort by total engagement
    result.sort(key=lambda x: x.total_likes + x.total_retweets + x.total_replies, reverse=True)
    
    return {"metrics": result, "period_days": days}


@router.get("/daily/activity")
async def get_daily_activity(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get daily activity breakdown"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    daily_data = db.query(
        func.date(Claim.created_at).label('date'),
        func.count(Claim.id).label('claims_count'),
        func.sum(case((Claim.status == VerificationStatus.VERIFIED, 1), else_=0)).label('verified_count'),
        func.sum(case((Claim.status == VerificationStatus.DEBUNKED, 1), else_=0)).label('debunked_count'),
        func.sum(case((Claim.status == VerificationStatus.MISLEADING, 1), else_=0)).label('misleading_count'),
        func.sum(case((Claim.status == VerificationStatus.UNVERIFIED, 1), else_=0)).label('unverified_count')
    ).filter(
        Claim.created_at >= start_date
    ).group_by(
        func.date(Claim.created_at)
    ).order_by(
        'date'
    ).all()
    
    result = []
    for d in daily_data:
        result.append(DailyActivity(
            date=str(d.date),
            claims_count=int(d.claims_count or 0),
            verified_count=int(d.verified_count or 0),
            debunked_count=int(d.debunked_count or 0),
            misleading_count=int(d.misleading_count or 0),
            unverified_count=int(d.unverified_count or 0)
        ))
    
    return {"daily_activity": result, "period_days": days}


@router.get("/topics/compare")
async def compare_topics(
    topic_ids: str = Query(..., description="Comma-separated topic IDs"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Compare multiple topics side-by-side"""
    topic_id_list = [int(tid.strip()) for tid in topic_ids.split(',') if tid.strip().isdigit()]
    
    if not topic_id_list:
        return {"topics": [], "error": "Invalid topic IDs"}
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = []
    for topic_id in topic_id_list:
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            continue
        
        # Get claims for this topic
        claims = db.query(Claim).join(
            Claim.topics
        ).filter(
            and_(
                Topic.id == topic_id,
                Claim.created_at >= start_date
            )
        ).all()
        
        total_claims = len(claims)
        verified_count = sum(1 for c in claims if getattr(c, 'status', None) == VerificationStatus.VERIFIED)
        debunked_count = sum(1 for c in claims if getattr(c, 'status', None) == VerificationStatus.DEBUNKED)
        
        # Calculate average confidence
        confidences = [float(getattr(c, 'confidence', 0.0)) for c in claims if getattr(c, 'confidence', None) is not None]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Calculate engagement score (from sources)
        source_ids = [str(c.source_id) for c in claims if getattr(c, 'source_id', None) is not None]
        sources = db.query(Source).filter(Source.id.in_(source_ids)).all() if source_ids else []
        
        total_engagement = 0
        engagement_count = 0
        for source in sources:
            engagement_data = source.engagement_metrics
            if engagement_data is not None:
                try:
                    if isinstance(engagement_data, dict):
                        metrics = engagement_data
                    else:
                        metrics = json.loads(str(engagement_data))
                    engagement = int(metrics.get('likes', 0) or 0) + int(metrics.get('retweets', 0) or 0) + int(metrics.get('replies', 0) or 0)
                    total_engagement += engagement
                    engagement_count += 1
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
        
        engagement_score = total_engagement / engagement_count if engagement_count > 0 else 0.0
        
        # Get trend score if available
        trending_topic = db.query(TrendingTopic).filter(
            TrendingTopic.topic_name.ilike(f"%{topic.name}%")
        ).order_by(desc(TrendingTopic.detected_at)).first()
        
        trend_score = float(getattr(trending_topic, 'final_priority_score', 0.0)) if trending_topic and getattr(trending_topic, 'final_priority_score', None) is not None else None
        
        result.append(TopicComparison(
            topic_id=int(getattr(topic, 'id', 0)),
            topic_name=str(topic.name),
            topic_slug=str(topic.slug),
            total_claims=total_claims,
            verification_rate=(verified_count / total_claims * 100) if total_claims > 0 else 0.0,
            debunk_rate=(debunked_count / total_claims * 100) if total_claims > 0 else 0.0,
            avg_confidence=avg_confidence,
            engagement_score=engagement_score,
            trend_score=trend_score
        ))
    
    return {"topics": result, "period_days": days}


@router.get("/audience/stats")
async def get_audience_stats(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get audience and reading statistics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total sources
    total_sources = db.query(func.count(Source.id)).filter(
        Source.scraped_at >= start_date
    ).scalar() or 0
    
    # Unique authors
    unique_authors = db.query(func.count(func.distinct(Source.author))).filter(
        and_(
            Source.scraped_at >= start_date,
            Source.author.isnot(None)
        )
    ).scalar() or 0
    
    # Platform distribution (duplicate logic to avoid circular calls)
    start_date_platform = datetime.utcnow() - timedelta(days=days)
    total_sources_platform = db.query(func.count(Source.id)).filter(
        Source.scraped_at >= start_date_platform
    ).scalar() or 1
    
    platform_data = db.query(
        Source.platform,
        func.count(Source.id).label('total_count'),
        func.sum(case((Claim.status == VerificationStatus.VERIFIED, 1), else_=0)).label('verified_count'),
        func.sum(case((Claim.status == VerificationStatus.DEBUNKED, 1), else_=0)).label('debunked_count'),
        func.sum(case((Claim.status == VerificationStatus.MISLEADING, 1), else_=0)).label('misleading_count'),
        func.sum(case((Claim.status == VerificationStatus.UNVERIFIED, 1), else_=0)).label('unverified_count')
    ).join(
        Claim, Claim.source_id == Source.id, isouter=True
    ).filter(
        Source.scraped_at >= start_date_platform
    ).group_by(
        Source.platform
    ).order_by(
        desc('total_count')
    ).all()
    
    platforms = []
    for p in platform_data:
        platform = p.platform or "Unknown"
        sources_with_engagement = db.query(Source).filter(
            and_(
                Source.platform == platform,
                Source.scraped_at >= start_date_platform,
                Source.engagement_metrics.isnot(None)
            )
        ).all()
        
        total_likes = 0
        total_retweets = 0
        total_replies = 0
        total_views = 0
        engagement_count = 0
        
        for source in sources_with_engagement:
            engagement_data = source.engagement_metrics
            if engagement_data is not None:
                try:
                    if isinstance(engagement_data, dict):
                        metrics = engagement_data
                    else:
                        metrics = json.loads(str(engagement_data))
                    total_likes += int(metrics.get('likes', 0) or 0)
                    total_retweets += int(metrics.get('retweets', 0) or 0)
                    total_replies += int(metrics.get('replies', 0) or 0)
                    total_views += int(metrics.get('views', 0) or 0)
                    engagement_count += 1
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
        
        avg_engagement = None
        if engagement_count > 0:
            avg_engagement = (total_likes + total_retweets + total_replies + total_views) / engagement_count
        
        platforms.append(PlatformDistribution(
            platform=str(platform),
            total_count=int(p.total_count or 0),
            verified_count=int(p.verified_count or 0),
            debunked_count=int(p.debunked_count or 0),
            misleading_count=int(p.misleading_count or 0),
            unverified_count=int(p.unverified_count or 0),
            percentage=(int(p.total_count or 0) / total_sources_platform) * 100 if total_sources_platform > 0 else 0,
            avg_engagement=avg_engagement
        ))
    
    # Engagement metrics (duplicate logic)
    sources_engagement = db.query(Source).filter(
        and_(
            Source.scraped_at >= start_date,
            Source.engagement_metrics.isnot(None)
        )
    ).all()
    
    platform_metrics: Dict[str, Dict[str, Any]] = {}
    
    for source in sources_engagement:
        platform_str = str(source.platform) if getattr(source, 'platform', None) is not None else "Unknown"
        
        if platform_str not in platform_metrics:
            platform_metrics[platform_str] = {
                "total_likes": 0,
                "total_retweets": 0,
                "total_replies": 0,
                "total_views": 0,
                "post_count": 0
            }
        
        engagement_data = source.engagement_metrics
        if engagement_data is not None:
            try:
                if isinstance(engagement_data, dict):
                    metrics = engagement_data
                else:
                    metrics = json.loads(str(engagement_data))
                platform_metrics[platform_str]["total_likes"] += int(metrics.get('likes', 0) or 0)
                platform_metrics[platform_str]["total_retweets"] += int(metrics.get('retweets', 0) or 0)
                platform_metrics[platform_str]["total_replies"] += int(metrics.get('replies', 0) or 0)
                platform_metrics[platform_str]["total_views"] += int(metrics.get('views', 0) or 0)
                platform_metrics[platform_str]["post_count"] += 1
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
    
    engagement_metrics = []
    for platform, metrics in platform_metrics.items():
        count = metrics["post_count"]
        if count > 0:
            engagement_metrics.append(EngagementMetrics(
                platform=platform,
                total_likes=metrics["total_likes"],
                total_retweets=metrics["total_retweets"],
                total_replies=metrics["total_replies"],
                total_views=metrics["total_views"],
                avg_likes=metrics["total_likes"] / count,
                avg_retweets=metrics["total_retweets"] / count,
                avg_replies=metrics["total_replies"] / count,
                avg_views=metrics["total_views"] / count,
                post_count=count
            ))
    
    engagement_metrics.sort(key=lambda x: x.total_likes + x.total_retweets + x.total_replies, reverse=True)
    
    # Top authors by engagement
    author_stats = db.query(
        Source.author,
        func.count(Source.id).label('post_count'),
        func.sum(
            case(
                (Source.engagement_metrics.isnot(None), 1),
                else_=0
            )
        ).label('has_engagement')
    ).filter(
        and_(
            Source.scraped_at >= start_date,
            Source.author.isnot(None)
        )
    ).group_by(
        Source.author
    ).order_by(
        desc('post_count')
    ).limit(limit).all()
    
    top_authors = []
    for author in author_stats:
        # Get engagement for this author
        author_sources = db.query(Source).filter(
            and_(
                Source.author == author.author,
                Source.scraped_at >= start_date,
                Source.engagement_metrics.isnot(None)
            )
        ).all()
        
        total_engagement = 0
        for source in author_sources:
            engagement_data = source.engagement_metrics
            if engagement_data is not None:
                try:
                    if isinstance(engagement_data, dict):
                        metrics = engagement_data
                    else:
                        metrics = json.loads(str(engagement_data))
                    total_engagement += int(metrics.get('likes', 0) or 0) + int(metrics.get('retweets', 0) or 0) + int(metrics.get('replies', 0) or 0)
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
        
        top_authors.append({
            "author": author.author,
            "post_count": int(author.post_count or 0),
            "total_engagement": total_engagement,
            "avg_engagement": total_engagement / len(author_sources) if author_sources else 0
        })
    
    # Sort by engagement
    top_authors.sort(key=lambda x: x["total_engagement"], reverse=True)
    
    return AudienceStats(
        total_sources=total_sources,
        unique_authors=unique_authors,
        platforms=platforms,
        engagement_metrics=engagement_metrics,
        top_authors=top_authors[:limit]
    )


@router.get("/comprehensive")
async def get_comprehensive_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get all analytics data in one call for dashboard"""
    # Call each endpoint function directly
    from fastapi import Request
    from app.rate_limit import limiter
    
    # Create a mock request for rate limiting (if needed)
    # In practice, these endpoints don't need rate limiting when called internally
    topic_dist = await get_topic_distribution(days, 20, db)
    platform_dist = await get_platform_distribution(days, db)
    engagement = await get_engagement_metrics(days, db)
    daily = await get_daily_activity(days, db)
    audience = await get_audience_stats(days, 10, db)
    
    return {
        "topic_distribution": topic_dist,
        "platform_distribution": platform_dist,
        "engagement_metrics": engagement,
        "daily_activity": daily,
        "audience_stats": audience,
        "period_days": days
    }

