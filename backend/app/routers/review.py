"""
Review Queue Router

Endpoints for managing claims that need human review.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from app.database import get_db
from app.database.models import Claim, User
from app.auth import get_current_user
from app.models import VerificationStatus
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/queue")
async def get_review_queue(
    priority: Optional[str] = Query(None, description="Filter by priority: high|medium|low"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get claims needing review"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = db.query(Claim).filter(Claim.needs_review == True)
    
    if priority:
        if priority not in ["high", "medium", "low"]:
            raise HTTPException(status_code=400, detail="Priority must be: high, medium, or low")
        query = query.filter(Claim.review_priority == priority)
    
    # Order by priority (high first) then by confidence (low first)
    claims = query.order_by(
        desc(Claim.review_priority == "high"),
        desc(Claim.review_priority == "medium"),
        Claim.confidence.asc()
    ).limit(limit).all()
    
    return {
        "total": len(claims),
        "claims": [
            {
                "id": c.id,
                "claim_text": c.claim_text,
                "original_text": c.original_text[:200] + "..." if len(c.original_text) > 200 else c.original_text,
                "status": c.status.value,
                "explanation": c.explanation,
                "confidence": c.confidence,
                "evidence_strength": c.evidence_strength,
                "priority": c.review_priority,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "evidence_sources": c.evidence_sources[:3] if c.evidence_sources else []  # First 3 sources
            }
            for c in claims
        ]
    }


@router.get("/stats")
async def get_review_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get statistics about review queue"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_pending = db.query(Claim).filter(Claim.needs_review == True).count()
    high_priority = db.query(Claim).filter(
        Claim.needs_review == True,
        Claim.review_priority == "high"
    ).count()
    medium_priority = db.query(Claim).filter(
        Claim.needs_review == True,
        Claim.review_priority == "medium"
    ).count()
    low_priority = db.query(Claim).filter(
        Claim.needs_review == True,
        Claim.review_priority == "low"
    ).count()
    
    # Average confidence of claims needing review
    avg_confidence_result = db.query(
        db.func.avg(Claim.confidence)
    ).filter(Claim.needs_review == True).scalar()
    avg_confidence = float(avg_confidence_result) if avg_confidence_result else 0.0
    
    return {
        "total_pending": total_pending,
        "high_priority": high_priority,
        "medium_priority": medium_priority,
        "low_priority": low_priority,
        "average_confidence": round(avg_confidence, 2)
    }


@router.post("/{claim_id}/approve")
async def approve_claim(
    claim_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Approve a reviewed claim (mark as reviewed)"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if not claim.needs_review:
        raise HTTPException(status_code=400, detail="Claim does not need review")
    
    claim.needs_review = False
    claim.review_priority = None
    db.commit()
    
    logger.info(f"Claim {claim_id} approved by admin {user.username}")
    
    return {
        "status": "approved",
        "claim_id": claim_id,
        "message": "Claim marked as reviewed"
    }


@router.post("/{claim_id}/update")
async def update_claim_verification(
    claim_id: str,
    new_status: str,
    new_explanation: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Update claim verification after human review"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if new_status not in ["Verified", "Debunked", "Misleading", "Unverified"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be: Verified, Debunked, Misleading, or Unverified"
        )
    
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Update status
    status_map = {
        "Verified": VerificationStatus.VERIFIED,
        "Debunked": VerificationStatus.DEBUNKED,
        "Misleading": VerificationStatus.MISLEADING,
        "Unverified": VerificationStatus.UNVERIFIED
    }
    claim.status = status_map[new_status]
    
    # Update explanation if provided
    if new_explanation:
        claim.explanation = new_explanation
    
    # Mark as reviewed
    claim.needs_review = False
    claim.review_priority = None
    # Increase confidence after human review
    claim.confidence = min(claim.confidence + 0.2, 1.0) if claim.confidence else 0.9
    
    db.commit()
    
    logger.info(f"Claim {claim_id} updated by admin {user.username}: {new_status}")
    
    return {
        "status": "updated",
        "claim_id": claim_id,
        "new_status": new_status,
        "new_confidence": claim.confidence
    }


@router.get("/{claim_id}")
async def get_claim_details(
    claim_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get detailed information about a claim for review"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Parse agent findings if available
    agent_findings = None
    if claim.agent_findings:
        try:
            import json
            agent_findings = json.loads(claim.agent_findings) if isinstance(claim.agent_findings, str) else claim.agent_findings
        except:
            agent_findings = claim.agent_findings
    
    return {
        "id": claim.id,
        "claim_text": claim.claim_text,
        "original_text": claim.original_text,
        "status": claim.status.value,
        "explanation": claim.explanation,
        "confidence": claim.confidence,
        "evidence_strength": claim.evidence_strength,
        "key_evidence_points": claim.key_evidence_points,
        "evidence_sources": claim.evidence_sources,
        "needs_review": claim.needs_review,
        "review_priority": claim.review_priority,
        "agent_findings": agent_findings,
        "created_at": claim.created_at.isoformat() if claim.created_at else None,
        "updated_at": claim.updated_at.isoformat() if claim.updated_at else None,
        "topics": [{"name": t.name, "slug": t.slug} for t in claim.topics] if hasattr(claim, 'topics') else []
    }

