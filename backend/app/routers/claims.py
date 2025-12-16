from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
import logging

from app.database.connection import get_db
from app.database.models import (
    Claim as DBClaim, 
    VerificationStatus as DBVerificationStatus
)
from app.schemas import Claim as ClaimResponse
from app.utils.mappers import map_db_claim_to_response
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/claims", tags=["claims"])

@router.get("", response_model=List[ClaimResponse])
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
            
        result = []
        for c in claims:
            try:
                result.append(map_db_claim_to_response(c, db))
            except Exception as e:
                logger.error(f"Error mapping claim {c.id} to response: {e}")
                # Skip this claim but continue with others
                continue
        
        return result
    except Exception as e:
        logger.error(f"Unexpected error in get_claims: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching claims: {str(e)}"
        )

@router.get("/search", response_model=List[ClaimResponse])
async def search_claims(
    query: str, 
    db: Session = Depends(get_db)
):
    """Search claims by text"""
    try:
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
            
        result = []
        for c in claims:
            try:
                result.append(map_db_claim_to_response(c, db))
            except Exception as e:
                logger.error(f"Error mapping claim {c.id} to response: {e}")
                continue
        
        return result
    except Exception as e:
        logger.error(f"Error searching claims: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error searching claims: {str(e)}"
        )

@router.get("/trending", response_model=List[ClaimResponse])
async def get_trending_claims(
    days: int = 7,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get trending/recent claims"""
    from datetime import datetime, timedelta
    
    today = datetime.utcnow()
    start_date = today - timedelta(days=days)
    
    claims = db.query(DBClaim)\
        .filter(DBClaim.created_at >= start_date)\
        .order_by(desc(DBClaim.created_at))\
        .limit(limit)\
        .all()
    
    return [map_db_claim_to_response(c, db) for c in claims]

@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific claim by ID"""
    try:
        claim = db.query(DBClaim).filter(DBClaim.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
            
        return map_db_claim_to_response(claim, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching claim {claim_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching claim: {str(e)}"
        )
