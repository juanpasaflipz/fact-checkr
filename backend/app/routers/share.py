"""
Share Router

Endpoints for generating shareable content from fact-checks.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import Claim as DBClaim
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/share", tags=["share"])


class ShareContentResponse(BaseModel):
    """Response containing shareable content"""
    tweet_text: str
    claim_id: str
    claim_text: str
    status: str
    explanation: str


def get_status_emoji(status: str) -> str:
    """Get emoji for verification status"""
    status_map = {
        "Verified": "✅",
        "Debunked": "❌",
        "Misleading": "⚠️",
        "Unverified": "❓"
    }
    return status_map.get(status, "❓")


def get_status_label(status: str) -> str:
    """Get Spanish label for verification status"""
    status_map = {
        "Verified": "VERIFICADO",
        "Debunked": "FALSO",
        "Misleading": "ENGAÑOSO",
        "Unverified": "SIN VERIFICAR"
    }
    return status_map.get(status, "SIN VERIFICAR")


@router.get("/claim/{claim_id}")
async def get_share_content(
    claim_id: str,
    db: Session = Depends(get_db)
):
    """Get shareable content for a claim"""
    claim = db.query(DBClaim).filter(DBClaim.id == claim_id).first()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    status = claim.status.value if hasattr(claim.status, 'value') else str(claim.status)
    emoji = get_status_emoji(status)
    label = get_status_label(status)
    
    # Build tweet text (280 chars max)
    claim_text_short = claim.claim_text[:100] + "..." if len(claim.claim_text) > 100 else claim.claim_text
    explanation_short = ""
    if claim.explanation:
        explanation_short = claim.explanation[:120] + "..." if len(claim.explanation) > 120 else claim.explanation
    
    # Construct tweet
    tweet_parts = [
        f"{emoji} {label}",
        f"\"{claim_text_short}\"",
    ]
    
    if explanation_short:
        tweet_parts.append(f"\n\n{explanation_short}")
    
    # Add source link if available
    if claim.source and claim.source.url:
        # Shorten URL for tweet (using placeholder - in production would use URL shortener)
        source_domain = claim.source.url.replace("https://", "").replace("http://", "").split("/")[0]
        tweet_parts.append(f"\n\nFuente: {source_domain}")
    
    tweet_text = "\n".join(tweet_parts)
    
    # Truncate to 280 chars if needed
    if len(tweet_text) > 280:
        # Remove explanation if too long
        tweet_parts = [
            f"{emoji} {label}",
            f"\"{claim_text_short}\"",
        ]
        if claim.source and claim.source.url:
            source_domain = claim.source.url.replace("https://", "").replace("http://", "").split("/")[0]
            tweet_parts.append(f"\n\nFuente: {source_domain}")
        tweet_text = "\n".join(tweet_parts)
        
        # Final truncate if still too long
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."
    
    return ShareContentResponse(
        tweet_text=tweet_text,
        claim_id=claim.id,
        claim_text=claim.claim_text,
        status=status,
        explanation=claim.explanation or ""
    )

