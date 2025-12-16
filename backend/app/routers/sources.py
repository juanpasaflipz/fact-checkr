from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.database.connection import get_db
from app.database.models import (
    Source as DBSource,
    Claim as DBClaim
)

router = APIRouter(prefix="/sources", tags=["sources"])

@router.get("")
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

@router.get("/stats")
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
