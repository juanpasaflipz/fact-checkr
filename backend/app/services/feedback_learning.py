"""
Feedback Learning Service

Enables the system to learn from human corrections:
- Records when AI verdicts are corrected
- Updates entity knowledge confidence
- Tracks source credibility over time
- Calculates accuracy metrics
"""
import os
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FeedbackLearningService:
    """Learn from human corrections and feedback to improve accuracy"""
    
    async def record_correction(
        self,
        claim_id: str,
        original_status: str,
        corrected_status: str,
        correction_reason: str,
        corrector_id: Optional[int] = None,
        corrector_type: str = "internal",
        evidence_provided: List[str] = None
    ) -> Dict:
        """
        Record when a human corrects an AI verification.
        
        Args:
            claim_id: ID of the claim being corrected
            original_status: AI's original verdict
            corrected_status: Human-corrected verdict
            correction_reason: Explanation for the correction
            corrector_id: User ID if authenticated
            corrector_type: "internal", "user", "expert", "partner"
            evidence_provided: URLs of evidence supporting correction
        
        Returns:
            Confirmation with learning signals triggered
        """
        from app.database.connection import SessionLocal
        from app.database.models import Claim
        
        db = SessionLocal()
        try:
            # Verify claim exists
            claim = db.query(Claim).filter(Claim.id == claim_id).first()
            if not claim:
                return {"error": "Claim not found", "claim_id": claim_id}
            
            # Calculate confidence delta
            confidence_delta = self._calculate_confidence_delta(
                original_status, corrected_status
            )
            
            # Store correction record
            db.execute("""
                INSERT INTO verification_corrections (
                    claim_id, original_status, corrected_status,
                    correction_reason, corrector_id, corrector_type,
                    confidence_delta, evidence_provided, created_at
                ) VALUES (
                    :claim_id, :original, :corrected, :reason,
                    :corrector_id, :corrector_type, :confidence_delta,
                    :evidence, :now
                )
            """, {
                "claim_id": claim_id,
                "original": original_status,
                "corrected": corrected_status,
                "reason": correction_reason,
                "corrector_id": corrector_id,
                "corrector_type": corrector_type,
                "confidence_delta": confidence_delta,
                "evidence": evidence_provided,
                "now": datetime.utcnow()
            })
            
            # Update the claim status
            db.execute("""
                UPDATE claims 
                SET status = :status,
                    explanation = CONCAT(
                        explanation, 
                        E'\n\n[Corrección: ', :reason, ']'
                    ),
                    updated_at = :now
                WHERE id = :claim_id
            """, {
                "status": corrected_status,
                "reason": correction_reason[:200],
                "claim_id": claim_id,
                "now": datetime.utcnow()
            })
            
            db.commit()
            
            # Trigger learning signals asynchronously
            learning_results = await self._update_learning_signals(
                db, claim, original_status, corrected_status
            )
            
            logger.info(
                f"Correction recorded: {claim_id} changed from "
                f"{original_status} to {corrected_status}"
            )
            
            return {
                "success": True,
                "claim_id": claim_id,
                "original_status": original_status,
                "corrected_status": corrected_status,
                "confidence_delta": confidence_delta,
                "learning_signals": learning_results
            }
            
        except Exception as e:
            logger.error(f"Error recording correction: {e}")
            db.rollback()
            return {"error": str(e), "claim_id": claim_id}
        finally:
            db.close()
    
    def _calculate_confidence_delta(
        self, 
        original: str, 
        corrected: str
    ) -> float:
        """Calculate how much confidence to adjust based on correction type"""
        # Major errors (opposite verdicts) get larger penalty
        if (original == "Verified" and corrected == "Debunked") or \
           (original == "Debunked" and corrected == "Verified"):
            return -0.3  # Significant confidence penalty
        
        # Partial errors
        if original in ["Verified", "Debunked"] and corrected == "Misleading":
            return -0.15
        
        if original == "Misleading" and corrected in ["Verified", "Debunked"]:
            return -0.1
        
        # Unverified being resolved
        if original == "Unverified":
            return 0.0  # No penalty, we were appropriately uncertain
        
        return -0.1  # Default small penalty
    
    async def _update_learning_signals(
        self,
        db,
        claim,
        original_status: str,
        corrected_status: str
    ) -> Dict:
        """Update knowledge base with correction signals"""
        signals = {
            "entity_knowledge_updated": 0,
            "source_credibility_updated": False
        }
        
        try:
            # Update source credibility if claim was incorrectly verified
            if claim.source and corrected_status in ["Debunked", "Misleading"]:
                source_domain = self._extract_domain(claim.source.url)
                if source_domain:
                    db.execute("""
                        INSERT INTO source_credibility (source_domain, total_claims, debunked_count)
                        VALUES (:domain, 1, 1)
                        ON CONFLICT (source_domain) DO UPDATE SET
                            debunked_count = source_credibility.debunked_count + 1,
                            total_claims = source_credibility.total_claims + 1,
                            credibility_score = (source_credibility.verified_count::float) / 
                                NULLIF(source_credibility.total_claims + 1, 0),
                            updated_at = NOW()
                    """, {"domain": source_domain})
                    signals["source_credibility_updated"] = True
            
            # Lower confidence of entity facts that led to wrong verdict
            if hasattr(claim, 'topics') and claim.topics:
                for topic in claim.topics:
                    db.execute("""
                        UPDATE entity_knowledge
                        SET confidence = confidence * 0.9
                        WHERE source_claim_id = :claim_id
                        AND confidence > 0.5
                    """, {"claim_id": claim.id})
                    signals["entity_knowledge_updated"] += 1
            
            db.commit()
            
        except Exception as e:
            logger.warning(f"Could not update learning signals: {e}")
            # Don't fail the main operation if learning signals fail
        
        return signals
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        if not url:
            return None
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except:
            return None
    
    async def get_accuracy_metrics(
        self, 
        days: int = 30
    ) -> Dict:
        """
        Calculate verification accuracy based on corrections.
        
        Returns metrics useful for:
        - System performance monitoring
        - Identifying problematic patterns
        - Reporting to stakeholders
        """
        from app.database.connection import SessionLocal
        
        db = SessionLocal()
        try:
            time_threshold = datetime.utcnow() - timedelta(days=days)
            
            # Get correction statistics
            corrections = db.execute("""
                SELECT 
                    COUNT(*) as total_corrections,
                    COUNT(CASE WHEN original_status = 'Verified' AND corrected_status = 'Debunked' THEN 1 END) as false_positives,
                    COUNT(CASE WHEN original_status = 'Debunked' AND corrected_status = 'Verified' THEN 1 END) as false_negatives,
                    COUNT(CASE WHEN original_status = 'Unverified' THEN 1 END) as uncertainty_resolved,
                    COUNT(CASE WHEN original_status IN ('Verified', 'Debunked') AND corrected_status = 'Misleading' THEN 1 END) as nuance_corrections
                FROM verification_corrections
                WHERE created_at >= :threshold
            """, {"threshold": time_threshold}).fetchone()
            
            # Get total claims in period
            total_claims = db.execute("""
                SELECT COUNT(*) FROM claims 
                WHERE created_at >= :threshold
            """, {"threshold": time_threshold}).scalar() or 0
            
            # Calculate accuracy
            if not corrections or total_claims == 0:
                return {
                    "period_days": days,
                    "total_verifications": total_claims,
                    "corrections_needed": 0,
                    "accuracy_rate": 1.0 if total_claims == 0 else None,
                    "message": "Insufficient data for metrics"
                }
            
            corrections_needed = corrections.total_corrections or 0
            accuracy_rate = 1 - (corrections_needed / max(total_claims, 1))
            
            # Get correction patterns by topic
            topic_patterns = db.execute("""
                SELECT 
                    t.name as topic,
                    COUNT(*) as correction_count,
                    AVG(vc.confidence_delta) as avg_confidence_delta
                FROM verification_corrections vc
                JOIN claims c ON c.id = vc.claim_id
                JOIN claim_topics ct ON c.id = ct.claim_id
                JOIN topics t ON t.id = ct.topic_id
                WHERE vc.created_at >= :threshold
                GROUP BY t.id, t.name
                ORDER BY correction_count DESC
                LIMIT 5
            """, {"threshold": time_threshold}).fetchall()
            
            return {
                "period_days": days,
                "total_verifications": total_claims,
                "corrections_needed": corrections_needed,
                "accuracy_rate": round(accuracy_rate, 4),
                "false_positive_count": corrections.false_positives or 0,
                "false_negative_count": corrections.false_negatives or 0,
                "false_positive_rate": round((corrections.false_positives or 0) / max(total_claims, 1), 4),
                "false_negative_rate": round((corrections.false_negatives or 0) / max(total_claims, 1), 4),
                "uncertainty_resolved": corrections.uncertainty_resolved or 0,
                "nuance_corrections": corrections.nuance_corrections or 0,
                "problematic_topics": [
                    {
                        "topic": p.topic,
                        "corrections": p.correction_count,
                        "avg_confidence_impact": round(p.avg_confidence_delta or 0, 3)
                    }
                    for p in topic_patterns
                ],
                "calculated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating accuracy metrics: {e}")
            return {
                "error": str(e),
                "period_days": days
            }
        finally:
            db.close()
    
    async def get_source_credibility_report(self, limit: int = 20) -> List[Dict]:
        """Get report on source credibility scores"""
        from app.database.connection import SessionLocal
        
        db = SessionLocal()
        try:
            sources = db.execute("""
                SELECT 
                    source_domain,
                    source_name,
                    source_type,
                    total_claims,
                    verified_count,
                    debunked_count,
                    misleading_count,
                    credibility_score,
                    is_whitelisted,
                    is_blacklisted
                FROM source_credibility
                ORDER BY total_claims DESC
                LIMIT :limit
            """, {"limit": limit}).fetchall()
            
            return [
                {
                    "domain": s.source_domain,
                    "name": s.source_name,
                    "type": s.source_type,
                    "total_claims": s.total_claims,
                    "verified": s.verified_count,
                    "debunked": s.debunked_count,
                    "misleading": s.misleading_count,
                    "credibility_score": round(s.credibility_score or 0, 3),
                    "whitelisted": s.is_whitelisted,
                    "blacklisted": s.is_blacklisted
                }
                for s in sources
            ]
        except Exception as e:
            logger.error(f"Error getting credibility report: {e}")
            return []
        finally:
            db.close()

