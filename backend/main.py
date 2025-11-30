import logging
import sys
import os
import traceback
from typing import List, Optional
from datetime import timedelta, datetime

from fastapi import FastAPI, Request, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func, case
from sqlalchemy.exc import OperationalError

# Import app modules
from app.database.connection import get_db
from app.database.models import (
    Claim as DBClaim, 
    Source as DBSource, 
    VerificationStatus as DBVerificationStatus, 
    Topic as DBTopic, 
    Entity as DBEntity,
    claim_topics
)
from app.models import (
    Claim as ClaimResponse, 
    VerificationResult, 
    SocialPost, 
    VerificationStatus, 
    Topic as TopicResponse, 
    Source as SourceResponse
)
from app.rate_limit import limiter, setup_rate_limiting
from app.auth import get_optional_user, create_access_token

# Configure logging FIRST before any imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True  # Override any existing configuration
)
logger = logging.getLogger(__name__)

logger.info("=" * 50)
logger.info("Initializing FactCheckr API...")
logger.info("=" * 50)

# Load environment variables
load_dotenv()
logger.info("✅ Environment variables loaded")

# Initialize FastAPI app
try:
    app = FastAPI(title="FactCheckr MX API", version="1.0.0")
    logger.info("✅ FastAPI app created")
except Exception as e:
    logger.error(f"❌ Failed to create FastAPI app: {e}")
    logger.error(traceback.format_exc())
    raise

# --- CORS Middleware (CRITICAL: Add BEFORE routes) ---
# Default CORS origins: localhost for dev, Railway domain, and custom domain
default_origins = "http://localhost:3000,https://factcheck.mx,https://www.factcheck.mx,https://fact-checkr-production.up.railway.app"
cors_origins = os.getenv("CORS_ORIGINS", default_origins).split(",")
# Clean up any empty strings from splitting
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"✅ CORS middleware configured with ALLOW ALL ORIGINS (Temporary Debug Mode)")

# --- Health Check (Priority) ---
@app.get("/debug/routes")
async def debug_routes():
    """List all registered routes for debugging"""
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, "methods") else None
        })
    return routes

@app.get("/health")
async def health_check():
    """Health check endpoint - always returns 200 for Railway health checks"""
    return {
        "status": "healthy",
        "message": "API is operational"
    }

logger.info("✅ Health check endpoint registered")

@app.on_event("startup")
async def startup_event():
    """Log when app starts"""
    logger.info("🚀 FactCheckr API starting up...")
    logger.info("✅ App initialized successfully")
    logger.info("✅ Health endpoint available at /health")
    logger.info("=" * 50)

# --- Rate Limiting ---
try:
    setup_rate_limiting(app)
except Exception as e:
    logger.error(f"Rate limiting setup failed: {e}")

# --- Routers ---
try:
    from app.routers import auth, subscriptions, usage, whatsapp, telegraph
    logger.info("✅ Router modules imported")
    
    app.include_router(auth.router, prefix="/api", tags=["auth"])
    app.include_router(subscriptions.router, prefix="/api", tags=["subscriptions"])
    app.include_router(usage.router, prefix="/api", tags=["usage"])
    app.include_router(whatsapp.router, prefix="/api", tags=["whatsapp"])
    app.include_router(telegraph.router, prefix="/api", tags=["telegraph"])
    logger.info("✅ All routers registered successfully")
except Exception as e:
    logger.warning(f"⚠️ Failed to register routers: {e}")
    logger.warning(traceback.format_exc())

# --- Helper Functions ---
def map_db_claim_to_response(db_claim: DBClaim) -> ClaimResponse:
    """Map database claim object to Pydantic response model"""
    
    # Parse verification status
    status_str = "Unverified"
    if isinstance(db_claim.status, DBVerificationStatus):
        status_str = db_claim.status.value
    else:
        status_str = str(db_claim.status)
        
    # Create VerificationResult
    verification = VerificationResult(
        status=status_str,
        explanation=db_claim.explanation or "No explanation provided",
        sources=db_claim.evidence_sources or []
    )
    
    # Create SocialPost from Source
    source_post = None
    if db_claim.source:
        source_post = SocialPost(
            id=str(db_claim.source.id),
            platform=db_claim.source.platform,
            content=db_claim.source.content,
            author=db_claim.source.author or "Unknown",
            timestamp=str(db_claim.source.timestamp),
            url=db_claim.source.url or ""
        )
        
    return ClaimResponse(
        id=str(db_claim.id),
        original_text=db_claim.original_text,
        claim_text=db_claim.claim_text,
        verification=verification,
        source_post=source_post
    )

# --- Exception Handlers ---
@app.exception_handler(OperationalError)
async def database_error_handler(request: Request, exc: OperationalError):
    """Handle database connection errors gracefully"""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable (Database Error)"},
    )

@app.get("/")
async def root():
    return {"message": "Fact Checkr API is running (Database Backed)"}

# --- Public Data Endpoints (Restored) ---

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
    except (OperationalError) as e:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching claims: {str(e)}"
        )

@app.get("/claims/search", response_model=List[ClaimResponse])
async def search_claims(
    query: str, 
    db: Session = Depends(get_db)
):
    """Search claims by text"""
    if not query:
        return []
        
    search_term = f"%{query}%"
    claims = db.query(DBClaim)\
        .filter(
            or_(
                DBClaim.claim_text.ilike(search_term),
                DBClaim.original_text.ilike(search_term)
            )
        )\
        .limit(50)\
        .all()
        
    return [map_db_claim_to_response(c) for c in claims]

@app.get("/stats")
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

@app.get("/topics", response_model=List[TopicResponse])
async def get_topics(db: Session = Depends(get_db)):
    """Get all topics"""
    topics = db.query(DBTopic).all()
    return [TopicResponse(id=t.id, name=t.name, slug=t.slug, description=t.description) for t in topics]

@app.get("/topics/{topic_slug}/stats")
async def get_topic_stats(topic_slug: str, db: Session = Depends(get_db)):
    """Get statistics for a specific topic"""
    topic = db.query(DBTopic).filter(DBTopic.slug == topic_slug).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
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
    
    query = db.query(DBClaim)\
        .join(claim_topics, DBClaim.id == claim_topics.c.claim_id)\
        .filter(claim_topics.c.topic_id == topic.id)
    
    if status:
        status_map = {
            "verified": DBVerificationStatus.VERIFIED,
            "debunked": DBVerificationStatus.DEBUNKED,
            "misleading": DBVerificationStatus.MISLEADING,
            "unverified": DBVerificationStatus.UNVERIFIED
        }
        status_enum = status_map.get(status.lower())
        if status_enum:
            query = query.filter(DBClaim.status == status_enum)
            
    claims = query.order_by(desc(DBClaim.created_at)).offset(skip).limit(limit).all()
    return [map_db_claim_to_response(c) for c in claims]

@app.get("/trends/summary")
async def get_trends_summary(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get summary of trending topics and activity"""
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

@app.get("/entities")
async def get_entities(db: Session = Depends(get_db)):
    """Get all entities"""
    entities = db.query(DBEntity).all()
    return [{"id": e.id, "name": e.name, "type": e.entity_type} for e in entities]

# Add explicit imports for datetime used in functions
from datetime import datetime
