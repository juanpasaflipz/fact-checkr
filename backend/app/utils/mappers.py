import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.models import (
    Claim as DBClaim, 
    VerificationStatus as DBVerificationStatus, 
    Market as DBMarket, 
    MarketStatus
)
from app.schemas import (
    Claim as ClaimResponse, 
    VerificationResult, 
    SocialPost, 
    VerificationStatus, 
    EvidenceDetail,
    MarketSummary
)

logger = logging.getLogger(__name__)

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
    
    # Get evidence_details if available
    evidence_details = getattr(db_claim, 'evidence_details', None)
    evidence_details_list = None
    if evidence_details:
        if isinstance(evidence_details, list):
            evidence_details_list = [
                EvidenceDetail(**ed) if isinstance(ed, dict) else ed
                for ed in evidence_details
            ]
    
    verification = VerificationResult(
        status=status_enum,
        explanation=str(db_claim.explanation) if db_claim.explanation is not None else "No explanation provided",
        sources=sources_list,
        evidence_details=evidence_details_list
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
            try:
                from app.services.markets import yes_probability, no_probability, calculate_volume
                yes_prob = yes_probability(market)
                no_prob = no_probability(market)
                volume = calculate_volume(market, db)
            except Exception as e:
                logger.warning(f"Error calculating market probabilities for claim {db_claim.id}: {e}")
                # Fallback to default values if market calculation fails
                yes_prob = 0.5
                no_prob = 0.5
                volume = 0.0
            
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
