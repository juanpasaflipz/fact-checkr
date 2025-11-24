from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func, case
from typing import List, Optional
from dotenv import load_dotenv
import os

from app.database.connection import get_db
from app.database.models import Claim as DBClaim, Source as DBSource, VerificationStatus as DBVerificationStatus, Topic as DBTopic, Entity as DBEntity
from app.models import Claim as ClaimResponse, VerificationResult, SocialPost, VerificationStatus, Topic as TopicResponse
from app.rate_limit import limiter, setup_rate_limiting
from app.auth import get_optional_user, create_access_token
from datetime import timedelta

load_dotenv()

app = FastAPI(title="FactCheckr MX API", version="1.0.0")
setup_rate_limiting(app)

# CORS middleware - configurable via environment variable
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request
from fastapi.responses import JSONResponse

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
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to verify API and database connectivity"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.commit()
        return {
            "status": "healthy",
            "database": "connected",
            "message": "API and database are operational"
        }
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

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
async def get_trending_claims(db: Session = Depends(get_db)):
    """Get trending claims based on recency and verification status"""
    from datetime import datetime, timedelta
    
    # Get claims from last 7 days, prioritizing verified/debunked (more engagement)
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    # Weight: Verified and Debunked get priority (more interesting)
    from sqlalchemy import case
    claims = db.query(DBClaim)\
        .filter(DBClaim.created_at >= week_ago)\
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
        .limit(10)\
        .all()
    
    return [map_db_claim_to_response(c) for c in claims]

@app.get("/topics", response_model=List[TopicResponse])
async def get_topics(db: Session = Depends(get_db)):
    """Get all topics"""
    from app.database.models import Topic as DBTopic
    topics = db.query(DBTopic).all()
    return [TopicResponse(id=t.id, name=t.name, slug=t.slug, description=t.description) for t in topics]

@app.get("/topics/{topic_slug}/claims", response_model=List[ClaimResponse])
async def get_claims_by_topic(topic_slug: str, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get claims filtered by topic"""
    topic = db.query(DBTopic).filter(DBTopic.slug == topic_slug).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Use the many-to-many relationship through claim_topics table
    from app.database.models import claim_topics
    claims = db.query(DBClaim)\
        .join(claim_topics, DBClaim.id == claim_topics.c.claim_id)\
        .filter(claim_topics.c.topic_id == topic.id)\
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
