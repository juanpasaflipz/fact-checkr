from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func, case
from typing import List, Optional
from dotenv import load_dotenv
import os

from app.database.connection import get_db
from app.database.models import Claim as DBClaim, Source as DBSource, VerificationStatus as DBVerificationStatus, Topic as DBTopic, Entity as DBEntity
from app.models import Claim as ClaimResponse, VerificationResult, SocialPost, VerificationStatus, Topic as TopicResponse, Source as SourceResponse
from app.rate_limit import limiter, setup_rate_limiting
from app.auth import get_optional_user, create_access_token
from datetime import timedelta

# Import routers (with error handling)
try:
    from app.routers import auth, subscriptions, usage, whatsapp, telegraph
    ROUTERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some routers not available: {e}")
    ROUTERS_AVAILABLE = False

load_dotenv()

app = FastAPI(title="FactCheckr MX API", version="1.0.0")

# Setup rate limiting (with error handling)
try:
    setup_rate_limiting(app)
except Exception as e:
    print(f"Warning: Rate limiting setup failed: {e}")

# Register routers (only if available)
if ROUTERS_AVAILABLE:
    try:
        app.include_router(auth.router)
        app.include_router(subscriptions.router)
        app.include_router(usage.router)
        app.include_router(whatsapp.router)
        app.include_router(telegraph.router)
    except Exception as e:
        print(f"Warning: Failed to register some routers: {e}")

# CORS middleware - configurable via environment variable
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from sqlalchemy.exc import OperationalError, DatabaseError

@app.exception_handler(OperationalError)
async def database_error_handler(request: Request, exc: OperationalError):
    """Handle database connection errors gracefully"""
    error_msg = str(exc)
    # Don't expose full connection details to frontend
    if "supabase" in error_msg.lower() or "timeout" in error_msg.lower():
        detail = "Database connection timeout. The service is temporarily unavailable. Please try again in a moment."
    else:
        detail = "Database connection error. Please try again later."
    
    return JSONResponse(
        status_code=503,
        content={
            "detail": detail,
            "error_type": "database_connection_error"
        }
    )

@app.exception_handler(DatabaseError)
async def database_error_handler_generic(request: Request, exc: DatabaseError):
    """Handle other database errors"""
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database error occurred. Please try again later.",
            "error_type": "database_error"
        }
    )

@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    import traceback
    # Only show full traceback in development
    import os
    if os.getenv("ENVIRONMENT") != "production":
        return JSONResponse(
            status_code=500,
            content={"message": str(exc), "traceback": traceback.format_exc()},
        )
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred."},
    )

def map_db_claim_to_response(db_claim: DBClaim) -> ClaimResponse:
    """Helper to convert DB Claim to Pydantic ClaimResponse"""
    
    # Map status enum
    status_map = {
        DBVerificationStatus.VERIFIED: VerificationStatus.VERIFIED,
        DBVerificationStatus.DEBUNKED: VerificationStatus.DEBUNKED,
        DBVerificationStatus.MISLEADING: VerificationStatus.MISLEADING,
        DBVerificationStatus.UNVERIFIED: VerificationStatus.UNVERIFIED,
    }
    
    verification = VerificationResult(
        status=status_map.get(db_claim.status, VerificationStatus.UNVERIFIED),
        explanation=db_claim.explanation or "No explanation provided.",
        sources=db_claim.evidence_sources or []
    )
    
    source_post = None
    if db_claim.source:
        source_post = SocialPost(
            id=db_claim.source.id,
            platform=db_claim.source.platform,
            content=db_claim.source.content,
            author=db_claim.source.author or "Unknown",
            timestamp=str(db_claim.source.timestamp),
            url=db_claim.source.url or ""
        )
        
    return ClaimResponse(
        id=db_claim.id,
        original_text=db_claim.original_text,
        claim_text=db_claim.claim_text,
        verification=verification,
        source_post=source_post
    )

@app.get("/")
async def root():
    return {"message": "Fact Checkr API is running (Database Backed)"}

@app.get("/health")
async def health_check():
    """Health check endpoint - always returns 200 for Railway health checks"""
    # Always return 200 immediately - Railway needs this to pass health check
    # Test database connection in background, don't block
    db_status = "unknown"
    try:
        from app.database.connection import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.commit()
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected"
    
    # Always return 200 - Railway health check just needs HTTP 200
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "message": "API is operational"
    }

@app.get("/claims", response_model=List[ClaimResponse])
@limiter.limit("100/minute")
async def get_claims(
    request: Request,
    skip: int = 0, 
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get paginated claims from the database with optional status filter"""
    try:
        query = db.query(DBClaim)
        
        # Filter by status if provided
        if status:
            status_map = {
                "verified": DBVerificationStatus.VERIFIED,
                "debunked": DBVerificationStatus.DEBUNKED,
                "misleading": DBVerificationStatus.MISLEADING,
                "unverified": DBVerificationStatus.UNVERIFIED,
                "todos": None  # "todos" means no filter
            }
            status_enum = status_map.get(status.lower())
            if status_enum:
                query = query.filter(DBClaim.status == status_enum)
        
        claims = query\
            .order_by(desc(DBClaim.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
            
        return [map_db_claim_to_response(c) for c in claims]
    except (OperationalError, DatabaseError) as e:
        db.rollback()
        # Let the exception handler deal with it
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching claims."
        )

@app.get("/claims/search", response_model=List[ClaimResponse])
async def search_claims(
    query: str, 
    db: Session = Depends(get_db)
):
    """Search claims by text"""
    search = f"%{query}%"
    claims = db.query(DBClaim).filter(
        or_(
            DBClaim.claim_text.ilike(search),
            DBClaim.original_text.ilike(search),
            DBClaim.explanation.ilike(search)
        )
    ).order_by(desc(DBClaim.created_at)).limit(50).all()
    
    return [map_db_claim_to_response(c) for c in claims]

@app.get("/claims/trending", response_model=List[ClaimResponse])
async def get_trending_claims(
    days: int = 7,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get trending claims based on recency and verification status"""
    from datetime import datetime, timedelta
    
    # Get claims from specified time window
    time_ago = datetime.utcnow() - timedelta(days=days)
    
    # Weight: Verified and Debunked get priority (more engagement)
    from sqlalchemy import case
    claims = db.query(DBClaim)\
        .filter(DBClaim.created_at >= time_ago)\
        .order_by(
            desc(
                # Prioritize verified and debunked claims
                case(
                    (DBClaim.status == DBVerificationStatus.VERIFIED, 3),
                    (DBClaim.status == DBVerificationStatus.DEBUNKED, 3),
                    (DBClaim.status == DBVerificationStatus.MISLEADING, 2),
                    else_=1
                )
            ),
            desc(DBClaim.created_at)  # Then by recency
        )\
        .limit(limit)\
        .all()
    
    return [map_db_claim_to_response(c) for c in claims]

@app.get("/trends/topics")
async def get_trending_topics(
    days: int = 7,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get trending topics with growth metrics"""
    from datetime import datetime, timedelta
    from app.database.models import claim_topics
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    previous_start = start_date - timedelta(days=days)
    
    # Current period topic counts
    current_counts = db.query(
        DBTopic.id,
        DBTopic.name,
        DBTopic.slug,
        func.count(DBClaim.id).label('current_count')
    ).join(
        claim_topics, DBTopic.id == claim_topics.c.topic_id
    ).join(
        DBClaim, DBClaim.id == claim_topics.c.claim_id
    ).filter(
        DBClaim.created_at >= start_date,
        DBClaim.created_at < end_date
    ).group_by(
        DBTopic.id, DBTopic.name, DBTopic.slug
    ).subquery()
    
    # Previous period topic counts
    previous_counts = db.query(
        DBTopic.id,
        func.count(DBClaim.id).label('previous_count')
    ).join(
        claim_topics, DBTopic.id == claim_topics.c.topic_id
    ).join(
        DBClaim, DBClaim.id == claim_topics.c.claim_id
    ).filter(
        DBClaim.created_at >= previous_start,
        DBClaim.created_at < start_date
    ).group_by(
        DBTopic.id
    ).subquery()
    
    # Join and calculate growth
    results = db.query(
        current_counts.c.id,
        current_counts.c.name,
        current_counts.c.slug,
        current_counts.c.current_count,
        func.coalesce(previous_counts.c.previous_count, 0).label('previous_count')
    ).outerjoin(
        previous_counts, current_counts.c.id == previous_counts.c.id
    ).order_by(
        desc(current_counts.c.current_count)
    ).limit(limit).all()
    
    trending_topics = []
    for r in results:
        growth = 0
        if r.previous_count > 0:
            growth = round(((r.current_count - r.previous_count) / r.previous_count) * 100)
        elif r.current_count > 0:
            growth = 100  # New trending topic
        
        trending_topics.append({
            "id": r.id,
            "name": r.name,
            "slug": r.slug,
            "claim_count": r.current_count,
            "previous_count": r.previous_count,
            "growth_percentage": growth,
            "trend_up": growth > 0
        })
    
    return trending_topics

@app.get("/trends/entities")
async def get_trending_entities(
    days: int = 7,
    limit: int = 15,
    db: Session = Depends(get_db)
):
    """Get trending entities (people, institutions) with claim counts"""
    from datetime import datetime, timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    entities = db.query(
        DBEntity.id,
        DBEntity.name,
        DBEntity.entity_type,
        func.count(DBClaim.id).label('claim_count')
    ).join(
        DBClaim, DBClaim.claim_text.ilike(func.concat('%', DBEntity.name, '%'))
    ).filter(
        DBClaim.created_at >= start_date
    ).group_by(
        DBEntity.id, DBEntity.name, DBEntity.entity_type
    ).order_by(
        func.count(DBClaim.id).desc()
    ).limit(limit).all()
    
    return [
        {
            "id": e.id,
            "name": e.name,
            "type": e.entity_type or "unknown",
            "claim_count": e.claim_count or 0
        }
        for e in entities
    ]

@app.get("/trends/platforms")
async def get_trending_platforms(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get platform activity trends with daily breakdown"""
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Platform distribution
    platform_stats = db.query(
        DBSource.platform,
        func.count(DBClaim.id).label('total_count'),
        func.count(func.case((DBClaim.status == DBVerificationStatus.DEBUNKED, 1))).label('debunked_count'),
        func.count(func.case((DBClaim.status == DBVerificationStatus.VERIFIED, 1))).label('verified_count')
    ).join(
        DBClaim, DBSource.id == DBClaim.source_id
    ).filter(
        DBClaim.created_at >= start_date
    ).group_by(
        DBSource.platform
    ).order_by(
        func.count(DBClaim.id).desc()
    ).all()
    
    # Daily breakdown for chart
    daily_platform = db.query(
        func.date(DBClaim.created_at).label('date'),
        DBSource.platform,
        func.count(DBClaim.id).label('count')
    ).join(
        DBSource, DBSource.id == DBClaim.source_id
    ).filter(
        DBClaim.created_at >= start_date
    ).group_by(
        func.date(DBClaim.created_at), DBSource.platform
    ).order_by(
        func.date(DBClaim.created_at), DBSource.platform
    ).all()
    
    # Organize daily data by platform
    daily_data = {}
    for dp in daily_platform:
        if dp.platform not in daily_data:
            daily_data[dp.platform] = []
        daily_data[dp.platform].append({
            "date": str(dp.date),
            "count": dp.count
        })
    
    return {
        "platforms": [
            {
                "platform": p.platform,
                "total_count": p.total_count,
                "debunked_count": p.debunked_count,
                "verified_count": p.verified_count
            }
            for p in platform_stats
        ],
        "daily_breakdown": daily_data
    }

@app.get("/trends/summary")
async def get_trends_summary(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get comprehensive trends summary for dashboard"""
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    previous_start = start_date - timedelta(days=days)
    
    # Current period stats
    current_claims = db.query(func.count(DBClaim.id)).filter(
        DBClaim.created_at >= start_date
    ).scalar() or 0
    
    # Previous period stats
    previous_claims = db.query(func.count(DBClaim.id)).filter(
        DBClaim.created_at >= previous_start,
        DBClaim.created_at < start_date
    ).scalar() or 0
    
    # Calculate growth
    growth = 0
    if previous_claims > 0:
        growth = round(((current_claims - previous_claims) / previous_claims) * 100)
    elif current_claims > 0:
        growth = 100
    
    # Status breakdown
    status_breakdown = db.query(
        DBClaim.status,
        func.count(DBClaim.id).label('count')
    ).filter(
        DBClaim.created_at >= start_date
    ).group_by(
        DBClaim.status
    ).all()
    
    return {
        "period_days": days,
        "total_claims": current_claims,
        "previous_period_claims": previous_claims,
        "growth_percentage": growth,
        "trend_up": growth > 0,
        "status_breakdown": [
            {"status": str(s.status), "count": s.count}
            for s in status_breakdown
        ]
    }

@app.get("/topics", response_model=List[TopicResponse])
async def get_topics(db: Session = Depends(get_db)):
    """Get all topics"""
    from app.database.models import Topic as DBTopic
    topics = db.query(DBTopic).all()
    return [TopicResponse(id=t.id, name=t.name, slug=t.slug, description=t.description) for t in topics]

@app.get("/topics/{topic_slug}/stats")
async def get_topic_stats(topic_slug: str, db: Session = Depends(get_db)):
    """Get statistics for a specific topic"""
    topic = db.query(DBTopic).filter(DBTopic.slug == topic_slug).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    from app.database.models import claim_topics
    
    # Get all claims for this topic
    claims = db.query(DBClaim)\
        .join(claim_topics, DBClaim.id == claim_topics.c.claim_id)\
        .filter(claim_topics.c.topic_id == topic.id)\
        .all()
    
    # Calculate stats
    total_claims = len(claims)
    verified_count = sum(1 for c in claims if c.status == DBVerificationStatus.VERIFIED)
    debunked_count = sum(1 for c in claims if c.status == DBVerificationStatus.DEBUNKED)
    misleading_count = sum(1 for c in claims if c.status == DBVerificationStatus.MISLEADING)
    unverified_count = sum(1 for c in claims if c.status == DBVerificationStatus.UNVERIFIED)
    
    return {
        "topic_id": topic.id,
        "topic_name": topic.name,
        "topic_slug": topic.slug,
        "total_claims": total_claims,
        "verified_count": verified_count,
        "debunked_count": debunked_count,
        "misleading_count": misleading_count,
        "unverified_count": unverified_count
    }

@app.get("/topics/{topic_slug}/claims", response_model=List[ClaimResponse])
async def get_claims_by_topic(
    topic_slug: str, 
    skip: int = 0, 
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get claims filtered by topic with optional status filter"""
    topic = db.query(DBTopic).filter(DBTopic.slug == topic_slug).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Use the many-to-many relationship through claim_topics table
    from app.database.models import claim_topics
    query = db.query(DBClaim)\
        .join(claim_topics, DBClaim.id == claim_topics.c.claim_id)\
        .filter(claim_topics.c.topic_id == topic.id)
    
    # Filter by status if provided
    if status:
        status_map = {
            "verified": DBVerificationStatus.VERIFIED,
            "debunked": DBVerificationStatus.DEBUNKED,
            "misleading": DBVerificationStatus.MISLEADING,
            "unverified": DBVerificationStatus.UNVERIFIED,
        }
        status_enum = status_map.get(status.lower())
        if status_enum:
            query = query.filter(DBClaim.status == status_enum)
    
    claims = query\
        .order_by(desc(DBClaim.created_at))\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return [map_db_claim_to_response(c) for c in claims]

@app.get("/entities")
async def get_entities(db: Session = Depends(get_db)):
    """Get all entities with their claim counts"""
    from sqlalchemy import func
    
    entities = db.query(
        DBEntity.id,
        DBEntity.name,
        DBEntity.entity_type,
        func.count(DBClaim.id).label('claim_count')
    ).outerjoin(
        DBClaim, DBClaim.claim_text.ilike(func.concat('%', DBEntity.name, '%'))
    ).group_by(
        DBEntity.id, DBEntity.name, DBEntity.entity_type
    ).order_by(
        func.count(DBClaim.id).desc()
    ).limit(50).all()
    
    return [
        {
            "id": e.id,
            "name": e.name,
            "type": e.entity_type,
            "claim_count": e.claim_count or 0
        }
        for e in entities
    ]

from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/login")
async def login(login_data: LoginRequest):
    """Simple login endpoint (in production, use proper password hashing)"""
    # For demo purposes - in production, verify against database with hashed passwords
    if login_data.username and login_data.password:
        access_token = create_access_token(data={"sub": login_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/claims/export")
@limiter.limit("10/minute")
async def export_claims(
    request: Request,
    format: str = "json",
    status: Optional[str] = None,
    limit: int = 1000,
    db: Session = Depends(get_db),
    user: Optional[dict] = Depends(get_optional_user)
):
    """Export claims in various formats"""
    query = db.query(DBClaim)
    
    if status:
        status_map = {
            "verified": DBVerificationStatus.VERIFIED,
            "debunked": DBVerificationStatus.DEBUNKED,
            "misleading": DBVerificationStatus.MISLEADING,
            "unverified": DBVerificationStatus.UNVERIFIED,
        }
        status_enum = status_map.get(status.lower())
        if status_enum:
            query = query.filter(DBClaim.status == status_enum)
    
    claims = query.order_by(desc(DBClaim.created_at)).limit(limit).all()
    claims_data = [map_db_claim_to_response(c) for c in claims]
    
    if format.lower() == "csv":
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Claim Text", "Status", "Explanation", "Platform", "Author", "Created At"])
        for claim in claims_data:
            writer.writerow([
                claim.id,
                claim.claim_text,
                claim.verification.status if claim.verification else "N/A",
                claim.verification.explanation if claim.verification else "N/A",
                claim.source_post.platform if claim.source_post else "N/A",
                claim.source_post.author if claim.source_post else "N/A",
                claim.source_post.timestamp if claim.source_post else "N/A"
            ])
        from fastapi.responses import Response
        return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=claims.csv"})
    
    return {"claims": claims_data, "count": len(claims_data)}

@app.get("/analytics")
async def get_analytics(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get detailed analytics for the dashboard"""
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Claims over time
    daily_claims = db.query(
        func.date(DBClaim.created_at).label('date'),
        func.count(DBClaim.id).label('count'),
        func.count(func.case((DBClaim.status == DBVerificationStatus.VERIFIED, 1))).label('verified'),
        func.count(func.case((DBClaim.status == DBVerificationStatus.DEBUNKED, 1))).label('debunked'),
    ).filter(
        DBClaim.created_at >= start_date
    ).group_by(
        func.date(DBClaim.created_at)
    ).order_by(
        func.date(DBClaim.created_at)
    ).all()
    
    # Platform distribution
    platform_stats = db.query(
        DBSource.platform,
        func.count(DBClaim.id).label('count')
    ).join(
        DBClaim, DBSource.id == DBClaim.source_id
    ).filter(
        DBClaim.created_at >= start_date
    ).group_by(
        DBSource.platform
    ).all()
    
    # Status distribution
    status_stats = db.query(
        DBClaim.status,
        func.count(DBClaim.id).label('count')
    ).filter(
        DBClaim.created_at >= start_date
    ).group_by(
        DBClaim.status
    ).all()
    
    return {
        "period_days": days,
        "daily_claims": [
            {
                "date": str(d.date),
                "total": d.count,
                "verified": d.verified,
                "debunked": d.debunked
            }
            for d in daily_claims
        ],
        "platforms": [
            {"platform": p.platform, "count": p.count}
            for p in platform_stats
        ],
        "status_distribution": [
            {"status": str(s.status), "count": s.count}
            for s in status_stats
        ]
    }

@app.get("/stats")
@limiter.limit("60/minute")
async def get_stats(request: Request, db: Session = Depends(get_db)):
    """Get real-time statistics from the database"""
    try:
        from sqlalchemy import func
        
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
        from app.database.models import Source
        active_sources = db.query(func.count(func.distinct(Source.id))).join(DBClaim, Source.id == DBClaim.source_id).scalar() or 0
        
        # Claims from last 24 hours
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_claims = db.query(func.count(DBClaim.id)).filter(DBClaim.created_at >= yesterday).scalar() or 0
        
        # Calculate trends (compare last 24h vs previous 24h)
        two_days_ago = datetime.utcnow() - timedelta(days=2)
        previous_period_claims = db.query(func.count(DBClaim.id)).filter(
            DBClaim.created_at >= two_days_ago,
            DBClaim.created_at < yesterday
        ).scalar() or 0
        
        trend_percentage = 0
        if previous_period_claims > 0:
            trend_percentage = round(((recent_claims - previous_period_claims) / previous_period_claims) * 100)
        
        return {
            "total_analyzed": total_claims,
            "fake_news_detected": fake_news_count,
            "verified": verified_count,
            "active_sources": active_sources,
            "recent_24h": recent_claims,
            "trend_percentage": trend_percentage,
            "trend_up": trend_percentage > 0
        }
    except (OperationalError, DatabaseError) as e:
        db.rollback()
        # Return default stats instead of error for better UX
        return {
            "total_analyzed": 0,
            "fake_news_detected": 0,
            "verified": 0,
            "active_sources": 0,
            "recent_24h": 0,
            "trend_percentage": 0,
            "trend_up": False
        }
    except Exception as e:
        db.rollback()
        # Return default stats on any error
        return {
            "total_analyzed": 0,
            "fake_news_detected": 0,
            "verified": 0,
            "active_sources": 0,
            "recent_24h": 0,
            "trend_percentage": 0,
            "trend_up": False
        }

@app.get("/sources", response_model=List[SourceResponse])
@limiter.limit("100/minute")
async def get_sources(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    platform: Optional[str] = None,
    processed: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get paginated sources with optional filtering"""
    try:
        query = db.query(DBSource)
        
        # Filter by platform if provided
        if platform:
            query = query.filter(DBSource.platform.ilike(f"%{platform}%"))
        
        # Filter by processing status if provided
        if processed is not None:
            query = query.filter(DBSource.processed == processed)
        
        # Search in content, author, or url
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    DBSource.content.ilike(search_term),
                    DBSource.author.ilike(search_term),
                    DBSource.url.ilike(search_term)
                )
            )
        
        # Get sources with claim counts
        sources = query\
            .order_by(desc(DBSource.timestamp))\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        # Map to response model with claim counts
        result = []
        for source in sources:
            claim_count = db.query(func.count(DBClaim.id))\
                .filter(DBClaim.source_id == source.id)\
                .scalar() or 0
            
            result.append(SourceResponse(
                id=source.id,
                platform=source.platform,
                content=source.content,
                author=source.author,
                url=source.url,
                timestamp=str(source.timestamp),
                scraped_at=str(source.scraped_at) if source.scraped_at else "",
                processed=source.processed or 0,
                claim_count=claim_count
            ))
        
        return result
    except (OperationalError, DatabaseError) as e:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching sources."
        )

@app.get("/sources/stats")
async def get_sources_stats(db: Session = Depends(get_db)):
    """Get statistics about sources"""
    try:
        from sqlalchemy import func
        
        # Total sources
        total_sources = db.query(func.count(DBSource.id)).scalar() or 0
        
        # Sources by platform
        platform_stats = db.query(
            DBSource.platform,
            func.count(DBSource.id).label('count')
        ).group_by(DBSource.platform).all()
        
        # Sources by processing status
        status_stats = db.query(
            DBSource.processed,
            func.count(DBSource.id).label('count')
        ).group_by(DBSource.processed).all()
        
        # Sources with claims
        sources_with_claims = db.query(func.count(func.distinct(DBClaim.source_id))).scalar() or 0
        
        return {
            "total_sources": total_sources,
            "sources_with_claims": sources_with_claims,
            "platforms": [
                {"platform": p.platform, "count": p.count}
                for p in platform_stats
            ],
            "processing_status": [
                {"status": s.processed, "count": s.count}
                for s in status_stats
            ]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching source statistics."
        )
