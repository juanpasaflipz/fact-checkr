import logging
import sys
import os
import traceback
from typing import List, Optional
from datetime import timedelta, datetime
from dotenv import load_dotenv

# Load environment variables FIRST before any imports that might use them
load_dotenv()

from fastapi import FastAPI, Request, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func, case
from sqlalchemy.exc import OperationalError

# Configure logging FIRST before any imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True  # Override any existing configuration
)
logger = logging.getLogger(__name__)

logger.info("✅ Environment variables loaded")

# Import app modules
from app.database.connection import get_db
from app.database.models import (
    Claim as DBClaim, 
    Source as DBSource, 
    VerificationStatus as DBVerificationStatus, 
    Topic as DBTopic, 
    Entity as DBEntity,
    Market as DBMarket,
    MarketStatus,
    claim_topics
)
from app.models import (
    Claim as ClaimResponse, 
    VerificationResult, 
    SocialPost, 
    VerificationStatus, 
    Topic as TopicResponse, 
    Source as SourceResponse,
    MarketSummary
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

# Import routers (with error handling)
try:
    from app.routers import auth, subscriptions, usage, whatsapp, telegraph, intelligence, markets, review, quota, trending, analytics
    ROUTERS_AVAILABLE = True
    INTELLIGENCE_ROUTER_AVAILABLE = True
    MARKETS_ROUTER_AVAILABLE = True
    REVIEW_ROUTER_AVAILABLE = True
    QUOTA_ROUTER_AVAILABLE = True
    TRENDING_ROUTER_AVAILABLE = True
    ANALYTICS_ROUTER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some routers not available: {e}")
    try:
        from app.routers import auth, subscriptions, usage, whatsapp, telegraph, markets, review, quota, trending, analytics
        ROUTERS_AVAILABLE = True
        INTELLIGENCE_ROUTER_AVAILABLE = False
        MARKETS_ROUTER_AVAILABLE = True
        REVIEW_ROUTER_AVAILABLE = True
        QUOTA_ROUTER_AVAILABLE = True
        TRENDING_ROUTER_AVAILABLE = True
        ANALYTICS_ROUTER_AVAILABLE = True
    except ImportError:
        try:
            from app.routers import auth, subscriptions, usage, whatsapp, telegraph, review, quota, trending, analytics
            ROUTERS_AVAILABLE = True
            INTELLIGENCE_ROUTER_AVAILABLE = False
            MARKETS_ROUTER_AVAILABLE = False
            REVIEW_ROUTER_AVAILABLE = True
            QUOTA_ROUTER_AVAILABLE = True
            TRENDING_ROUTER_AVAILABLE = True
            ANALYTICS_ROUTER_AVAILABLE = True
        except ImportError:
            try:
                from app.routers import auth, subscriptions, usage, whatsapp, telegraph, quota, trending, analytics
                ROUTERS_AVAILABLE = True
                INTELLIGENCE_ROUTER_AVAILABLE = False
                MARKETS_ROUTER_AVAILABLE = False
                REVIEW_ROUTER_AVAILABLE = False
                QUOTA_ROUTER_AVAILABLE = True
                TRENDING_ROUTER_AVAILABLE = True
                ANALYTICS_ROUTER_AVAILABLE = True
            except ImportError:
                try:
                    from app.routers import auth, subscriptions, usage, whatsapp, telegraph, trending, analytics
                    ROUTERS_AVAILABLE = True
                    INTELLIGENCE_ROUTER_AVAILABLE = False
                    MARKETS_ROUTER_AVAILABLE = False
                    REVIEW_ROUTER_AVAILABLE = False
                    QUOTA_ROUTER_AVAILABLE = False
                    TRENDING_ROUTER_AVAILABLE = True
                    ANALYTICS_ROUTER_AVAILABLE = True
                except ImportError:
                    try:
                        from app.routers import auth, subscriptions, usage, whatsapp, telegraph
                        ROUTERS_AVAILABLE = True
                        INTELLIGENCE_ROUTER_AVAILABLE = False
                        MARKETS_ROUTER_AVAILABLE = False
                        REVIEW_ROUTER_AVAILABLE = False
                        QUOTA_ROUTER_AVAILABLE = False
                        TRENDING_ROUTER_AVAILABLE = False
                        ANALYTICS_ROUTER_AVAILABLE = False
                    except ImportError:
                        ROUTERS_AVAILABLE = False
                        INTELLIGENCE_ROUTER_AVAILABLE = False
                        MARKETS_ROUTER_AVAILABLE = False
                        REVIEW_ROUTER_AVAILABLE = False
                        QUOTA_ROUTER_AVAILABLE = False
                        TRENDING_ROUTER_AVAILABLE = False
                        ANALYTICS_ROUTER_AVAILABLE = False

logger.info("=" * 50)
logger.info("Initializing FactCheckr API...")
logger.info("=" * 50)

# Initialize FastAPI app
try:
    app = FastAPI(title="FactCheckr MX API", version="1.0.0")
    logger.info("✅ FastAPI app created")
except Exception as e:
    logger.error(f"❌ Failed to create FastAPI app: {e}")
    logger.error(traceback.format_exc())
    raise

# --- CORS Middleware (CRITICAL: Add BEFORE routes) ---
# Default CORS origins: localhost for dev, Railway domain, Vercel, and custom domain
default_origins = ",".join([
    "http://localhost:3000",
    "http://localhost:3001",
    "https://factcheck.mx",
    "https://www.factcheck.mx",
    "https://fact-checkr-production.up.railway.app",
    "https://fact-checkr.vercel.app",
    "https://fact-checkr-juanpasa.vercel.app",
])
cors_origins = os.getenv("CORS_ORIGINS", default_origins).split(",")
# Clean up any empty strings from splitting
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://fact-checkr.*\.vercel\.app",  # All Vercel preview deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"✅ CORS middleware configured with origins: {cors_origins} + Vercel regex")

# --- Health Check (Priority) ---
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
    
    # Validate Stripe configuration
    try:
        from app.config.stripe_config import log_stripe_config_status
        log_stripe_config_status()
    except Exception as e:
        logger.warning(f"⚠️  Stripe configuration validation failed: {e}")
    
    logger.info("✅ App initialized successfully")
    logger.info("✅ Health endpoint available at /health")
    logger.info("=" * 50)

# --- Rate Limiting ---
try:
    setup_rate_limiting(app)
except Exception as e:
    logger.error(f"Rate limiting setup failed: {e}")

# --- Routers ---
if ROUTERS_AVAILABLE:
    try:
        app.include_router(auth.router, prefix="/api", tags=["auth"])
        app.include_router(subscriptions.router, prefix="/api", tags=["subscriptions"])
        app.include_router(usage.router, prefix="/api", tags=["usage"])
        app.include_router(whatsapp.router, prefix="/api", tags=["whatsapp"])
        app.include_router(telegraph.router, prefix="/api", tags=["telegraph"])
        logger.info("✅ Base routers registered successfully")
        
        if QUOTA_ROUTER_AVAILABLE:
            app.include_router(quota.router, prefix="/api", tags=["quota"])
            logger.info("✅ Quota management router registered")
        
        # Keywords router (always available - no external dependencies)
        try:
            from app.routers import keywords
            app.include_router(keywords.router, prefix="/api", tags=["keywords"])
            logger.info("✅ Keywords management router registered")
        except ImportError as e:
            logger.warning(f"Keywords router not available: {e}")
        
        if REVIEW_ROUTER_AVAILABLE:
            app.include_router(review.router, prefix="/api", tags=["review"])
            logger.info("✅ Review queue router registered")
        
        if MARKETS_ROUTER_AVAILABLE:
            app.include_router(markets.router, prefix="/api", tags=["markets"])
            logger.info("✅ Markets API router registered")
        
        if INTELLIGENCE_ROUTER_AVAILABLE:
            app.include_router(intelligence.router)
            logger.info("✅ Intelligence API router registered")
        
        if TRENDING_ROUTER_AVAILABLE:
            app.include_router(trending.router)
            logger.info("✅ Trending Topics API router registered")
        
        if ANALYTICS_ROUTER_AVAILABLE:
            app.include_router(analytics.router, prefix="/api", tags=["analytics"])
            logger.info("✅ Analytics API router registered")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register routers: {e}")
        logger.warning(traceback.format_exc())

# --- Helper Functions ---
def map_db_claim_to_response(db_claim: DBClaim, db: Optional[Session] = None) -> ClaimResponse:
    """Map database claim object to Pydantic response model"""
    
    # Parse verification status
    status_str = "Unverified"
    if isinstance(db_claim.status, DBVerificationStatus):
        status_str = db_claim.status.value
    else:
        status_str = str(db_claim.status)
    
    # Convert string to VerificationStatus enum
    try:
        status_enum = VerificationStatus(status_str)
    except ValueError:
        status_enum = VerificationStatus.UNVERIFIED
        
    # Create VerificationResult
    evidence_sources = getattr(db_claim, 'evidence_sources', None)
    sources_list = []
    if evidence_sources is not None:
        if isinstance(evidence_sources, list):
            sources_list = evidence_sources
        else:
            sources_list = list(evidence_sources) if hasattr(evidence_sources, '__iter__') else []
    
    verification = VerificationResult(
        status=status_enum,
        explanation=str(db_claim.explanation) if db_claim.explanation is not None else "No explanation provided",
        sources=sources_list
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
    
    # Get primary market for this claim (most recent open, or most recent resolved)
    market_summary = None
    if db is not None:
        # Try to get most recent open market first
        market = db.query(DBMarket).filter(
            DBMarket.claim_id == db_claim.id,
            DBMarket.status == MarketStatus.OPEN
        ).order_by(desc(DBMarket.created_at)).first()
        
        # If no open market, get most recent resolved market
        if not market:
            market = db.query(DBMarket).filter(
                DBMarket.claim_id == db_claim.id,
                DBMarket.status == MarketStatus.RESOLVED
            ).order_by(desc(DBMarket.created_at)).first()
        
        if market:
            from app.services.markets import yes_probability, no_probability, calculate_volume
            yes_prob = yes_probability(market)
            no_prob = no_probability(market)
            volume = calculate_volume(market, db)
            
            # Access actual values from ORM instance
            market_id = getattr(market, 'id', None)
            market_slug = getattr(market, 'slug', None)
            market_question = getattr(market, 'question', None)
            market_closes_at = getattr(market, 'closes_at', None)
            market_claim_id = getattr(market, 'claim_id', None)
            market_category = getattr(market, 'category', None)
            market_status = getattr(market, 'status', None)
            
            # Determine status string
            status_str = "open"
            if market_status is not None:
                if hasattr(market_status, 'value'):
                    status_str = market_status.value
                else:
                    status_str = str(market_status)
            
            market_summary = MarketSummary(
                id=int(market_id) if market_id is not None else 0,
                slug=str(market_slug) if market_slug is not None else "",
                question=str(market_question) if market_question is not None else "",
                yes_probability=yes_prob,
                no_probability=no_prob,
                volume=volume,
                closes_at=market_closes_at if market_closes_at is not None else None,
                status=status_str,
                claim_id=str(market_claim_id) if market_claim_id is not None else None,
                category=str(market_category) if market_category is not None else None
            )
        
    return ClaimResponse(
        id=str(db_claim.id),
        original_text=str(db_claim.original_text),
        claim_text=str(db_claim.claim_text),
        verification=verification,
        source_post=source_post,
        market=market_summary
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
            
        return [map_db_claim_to_response(c, db) for c in claims]
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
        
    return [map_db_claim_to_response(c, db) for c in claims]

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
    result = []
    for t in topics:
        topic_id = getattr(t, 'id', None)
        topic_name = getattr(t, 'name', None)
        topic_slug = getattr(t, 'slug', None)
        topic_description = getattr(t, 'description', None)
        result.append(TopicResponse(
            id=int(topic_id) if topic_id is not None else 0,
            name=str(topic_name) if topic_name is not None else "",
            slug=str(topic_slug) if topic_slug is not None else "",
            description=str(topic_description) if topic_description is not None else None
        ))
    return result

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
    verified_count = 0
    debunked_count = 0
    misleading_count = 0
    unverified_count = 0
    
    for c in claims:
        claim_status = getattr(c, 'status', None)
        if claim_status == DBVerificationStatus.VERIFIED:
            verified_count += 1
        elif claim_status == DBVerificationStatus.DEBUNKED:
            debunked_count += 1
        elif claim_status == DBVerificationStatus.MISLEADING:
            misleading_count += 1
        elif claim_status == DBVerificationStatus.UNVERIFIED:
            unverified_count += 1
    
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
    return [map_db_claim_to_response(c, db) for c in claims]

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

@app.get("/trends/topics")
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


@app.get("/trends/entities")
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


@app.get("/trends/platforms")
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


@app.get("/claims/trending", response_model=List[ClaimResponse])
async def get_trending_claims(
    days: int = 7,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get trending/recent claims"""
    today = datetime.utcnow()
    start_date = today - timedelta(days=days)
    
    claims = db.query(DBClaim)\
        .filter(DBClaim.created_at >= start_date)\
        .order_by(desc(DBClaim.created_at))\
        .limit(limit)\
        .all()
    
    return [map_db_claim_to_response(c, db) for c in claims]


@app.get("/sources")
async def get_sources(
    skip: int = 0,
    limit: int = 20,
    platform: Optional[str] = None,
    processed: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get paginated sources"""
    query = db.query(DBSource)
    
    if platform:
        query = query.filter(DBSource.platform == platform)
    
    if processed is not None:
        query = query.filter(DBSource.processed == processed)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                DBSource.content.ilike(search_term),
                DBSource.author.ilike(search_term)
            )
        )
    
    sources = query.order_by(desc(DBSource.timestamp))\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    result = []
    for s in sources:
        # Count claims for this source
        claim_count = db.query(func.count(DBClaim.id))\
            .filter(DBClaim.source_id == s.id)\
            .scalar() or 0
        
        result.append({
            "id": str(s.id),
            "platform": s.platform,
            "content": s.content,
            "author": s.author,
            "url": s.url,
            "timestamp": s.timestamp.isoformat() if s.timestamp is not None else None,
            "scraped_at": s.scraped_at.isoformat() if s.scraped_at is not None else None,
            "processed": s.processed,
            "claim_count": claim_count
        })
    
    return result


@app.get("/sources/stats")
async def get_source_stats(db: Session = Depends(get_db)):
    """Get source statistics"""
    total = db.query(func.count(DBSource.id)).scalar() or 0
    
    # Sources that have claims
    sources_with_claims = db.query(func.count(func.distinct(DBClaim.source_id))).scalar() or 0
    
    # Platform breakdown
    platforms = db.query(
        DBSource.platform,
        func.count(DBSource.id).label('count')
    ).group_by(DBSource.platform).all()
    
    # Processing status breakdown
    processing_status = db.query(
        DBSource.processed,
        func.count(DBSource.id).label('count')
    ).group_by(DBSource.processed).all()
    
    return {
        "total_sources": total,
        "sources_with_claims": sources_with_claims,
        "platforms": [{"platform": p.platform or "Unknown", "count": p.count} for p in platforms],
        "processing_status": [{"status": s.processed, "count": s.count} for s in processing_status]
    }


@app.get("/analytics")
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


@app.get("/entities")
async def get_entities(db: Session = Depends(get_db)):
    """Get all entities"""
    entities = db.query(DBEntity).all()
    return [{"id": e.id, "name": e.name, "type": e.entity_type} for e in entities]
