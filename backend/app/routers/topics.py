from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

import logging

from app.database.connection import get_db
from app.database.models import (
    Claim as DBClaim, 
    Topic as DBTopic,
    VerificationStatus as DBVerificationStatus,
    claim_topics
)
from app.schemas import Topic as TopicResponse, Claim as ClaimResponse
from app.utils.mappers import map_db_claim_to_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/topics", tags=["topics"])

@router.get("", response_model=List[TopicResponse])
async def get_topics(db: Session = Depends(get_db)):
    """Get all topics"""
    try:
        topics = db.query(DBTopic).all()
        result = []
        for t in topics:
            try:
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
            except Exception as e:
                logger.error(f"Error mapping topic {getattr(t, 'id', 'unknown')} to response: {e}")
                continue
        return result
    except Exception as e:
        logger.error(f"Error fetching topics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching topics: {str(e)}"
        )

@router.get("/{topic_slug}/stats")
async def get_topic_stats(topic_slug: str, db: Session = Depends(get_db)):
    """Get statistics for a specific topic"""
    try:
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
    except HTTPException:
        raise  # Re-raise HTTP exceptions (like 404)
    except Exception as e:
        logger.error(f"Error fetching topic stats for {topic_slug}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching topic stats: {str(e)}"
        )

@router.get("/{topic_slug}/claims", response_model=List[ClaimResponse])
async def get_claims_by_topic(
    topic_slug: str, 
    skip: int = 0, 
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get claims filtered by topic with optional status filter"""
    try:
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
        
        result = []
        for c in claims:
            try:
                result.append(map_db_claim_to_response(c, db))
            except Exception as e:
                logger.error(f"Error mapping claim {c.id} to response: {e}")
                continue
        
        return result
    except HTTPException:
        raise  # Re-raise HTTP exceptions (like 404)
    except Exception as e:
        logger.error(f"Error fetching claims for topic {topic_slug}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching claims: {str(e)}"
        )
