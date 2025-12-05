# Verification Enhancement Implementation Guide

## Quick Start: Phase 1 Critical Fixes

### Fix 1: Integrate RAG Pipeline (Highest Priority)

**Problem**: LLM only sees evidence URLs, not actual content
**Solution**: Use existing `RAGPipeline` to fetch and analyze evidence

#### Step 1: Update `tasks/fact_check.py`

```python
# Add import
from app.services.rag_pipeline import RAGPipeline

async def verify_source(source_id: str):
    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            logger.error(f"Source {source_id} not found")
            return
            
        if source.processed != 0:
            logger.info(f"Source {source_id} already processed")
            return

        checker = FactChecker()
        
        # 1. Extract Claim
        claim_text = await checker._extract_claim(source.content)
        
        if claim_text == "SKIP":
            source.processed = 2
            db.commit()
            return
        
        # 2. Build rich context using RAG pipeline
        rag = RAGPipeline()
        context = await rag.build_verification_context(
            claim_text=claim_text,
            original_text=source.content,
            source_url=source.url
        )
        
        # 3. Check for similar claims (deduplication)
        similar_claims = context.get("similar_claims", [])
        if similar_claims and similar_claims[0].get("similarity", 0) > 0.95:
            # Very similar claim exists - check if we can reuse
            similar_claim_id = similar_claims[0].get("claim_id")
            if similar_claim_id:
                existing_claim = db.query(Claim).filter(
                    Claim.id == similar_claim_id
                ).first()
                if existing_claim:
                    # Link to existing claim
                    source.processed = 1
                    db.commit()
                    logger.info(f"Linked source {source_id} to existing claim {similar_claim_id}")
                    return existing_claim.id
        
        # 4. Verify with enhanced context
        evidence_urls = context.get("evidence_urls", [])
        evidence_texts = context.get("evidence_texts", [])
        
        # Use enhanced verification that includes evidence content
        verification = await checker._verify_claim_with_evidence(
            claim_text, 
            evidence_urls,
            evidence_texts,
            context
        )
        
        # ... rest of existing code ...
```

#### Step 2: Add Enhanced Verification Method

Add to `agent.py`:

```python
async def _verify_claim_with_evidence(
    self, 
    claim: str, 
    evidence_urls: List[str],
    evidence_texts: List[str],
    context: Dict = None
) -> VerificationResult:
    """Enhanced verification with actual evidence content"""
    
    if not self.anthropic_client and not self.openai_client:
        return VerificationResult(
            status=VerificationStatus.UNVERIFIED,
            explanation="No AI API keys configured.",
            sources=evidence_urls,
            confidence=0.0
        )
    
    # Build evidence summary with actual content
    evidence_summary = []
    for i, (url, text) in enumerate(zip(evidence_urls[:5], evidence_texts[:5])):
        if text and len(text) > 100:
            evidence_summary.append(
                f"FUENTE {i+1} ({url}):\n{text[:2000]}...\n"
            )
    
    if not evidence_summary:
        evidence_summary = [f"- {url}" for url in evidence_urls[:5]]
    
    evidence_text = "\n\n".join(evidence_summary)
    
    # Add context about similar claims if available
    context_info = ""
    if context:
        similar = context.get("similar_claims", [])
        if similar:
            context_info = f"\n\nAFIRMACIONES SIMILARES ANTERIORES:\n"
            for sc in similar[:3]:
                context_info += f"- \"{sc.get('claim_text', '')[:100]}...\" "
                context_info += f"(Estado: {sc.get('status', 'N/A')}, Similitud: {sc.get('similarity', 0):.2f})\n"
    
    current_date = datetime.now().strftime("%B %d, %Y")
    
    system_prompt = f"""You are a neutral, objective fact-checker for Mexican News.

Current Date: {current_date}.

You must analyze claims ONLY based on the provided EVIDENCE CONTENT. Be thorough, objective, and cite specific evidence."""
    
    user_prompt = f"""CLAIM TO CHECK: "{claim}"

EVIDENCE CONTENT:
{evidence_text}
{context_info}

INSTRUCTIONS:
1. Analyze the claim based on the ACTUAL EVIDENCE CONTENT provided above.
2. If evidence is contradictory or insufficient, verdict must be "Unverified".
3. "Misleading" applies if facts are real but context is manipulated.
4. Provide a confidence score (0.0-1.0) based on evidence strength.

RESPONSE FORMAT (JSON only):
{{
    "status": "Verified" | "Debunked" | "Misleading" | "Unverified",
    "explanation": "A concise (max 280 chars) explanation in Mexican Spanish.",
    "confidence": 0.0-1.0,
    "evidence_strength": "strong|moderate|weak|insufficient",
    "key_evidence_points": ["point 1", "point 2"]
}}"""
    
    # Try Anthropic first
    if self.anthropic_client:
        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-3-5-20241022",
                max_tokens=400,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            response_text = response.content[0].text.strip()
            
            # Parse JSON
            if response_text.startswith("```"):
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    response_text = response_text[json_start:json_end]
            
            result = json.loads(response_text)
            status_map = {
                "Verified": VerificationStatus.VERIFIED,
                "Debunked": VerificationStatus.DEBUNKED,
                "Misleading": VerificationStatus.MISLEADING,
                "Unverified": VerificationStatus.UNVERIFIED
            }
            
            return VerificationResult(
                status=status_map.get(result.get("status"), VerificationStatus.UNVERIFIED),
                explanation=result.get("explanation", "No se pudo verificar."),
                sources=evidence_urls,
                confidence=result.get("confidence", 0.5),
                evidence_strength=result.get("evidence_strength", "insufficient")
            )
        except Exception as e:
            logger.error(f"Anthropic verification error: {e}")
    
    # Fallback to OpenAI or return unverified
    # ... (similar implementation)
    
    return VerificationResult(
        status=VerificationStatus.UNVERIFIED,
        explanation="Error al verificar.",
        sources=evidence_urls,
        confidence=0.0
    )
```

#### Step 3: Update VerificationResult Model

Update `app/models.py`:

```python
class VerificationResult(BaseModel):
    status: VerificationStatus
    explanation: str
    sources: List[str]
    confidence: float = 0.5  # NEW
    evidence_strength: Optional[str] = None  # NEW
    key_evidence_points: Optional[List[str]] = None  # NEW
```

#### Step 4: Update Claim Model

Update `app/database/models.py`:

```python
class Claim(Base):
    # ... existing fields ...
    
    # Add new fields
    confidence = Column(Float, nullable=True)
    evidence_strength = Column(String, nullable=True)
    needs_review = Column(Boolean, default=False)
    review_priority = Column(String, nullable=True)  # "high|medium|low"
```

#### Step 5: Create Migration

```bash
cd backend
alembic revision -m "add_confidence_and_review_fields"
```

```python
def upgrade():
    op.add_column('claims', sa.Column('confidence', sa.Float(), nullable=True))
    op.add_column('claims', sa.Column('evidence_strength', sa.String(), nullable=True))
    op.add_column('claims', sa.Column('needs_review', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('claims', sa.Column('review_priority', sa.String(), nullable=True))
```

---

### Fix 2: Add Confidence-Based Review Queue

#### Step 1: Flag Low-Confidence Claims

In `tasks/fact_check.py`, after verification:

```python
# Store claim with confidence
claim = Claim(
    # ... existing fields ...
    confidence=verification.confidence,
    evidence_strength=verification.evidence_strength,
    needs_review=verification.confidence < 0.6,  # Flag low confidence
    review_priority="high" if verification.confidence < 0.4 else "medium"
)
```

#### Step 2: Create Review Queue Endpoint

Create `backend/app/routers/review.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.database.models import Claim, VerificationStatus
from app.auth import get_current_user, User

router = APIRouter(prefix="/review", tags=["review"])

@router.get("/queue")
async def get_review_queue(
    priority: str = None,  # "high|medium|low"
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get claims needing review"""
    if not user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    query = db.query(Claim).filter(Claim.needs_review == True)
    
    if priority:
        query = query.filter(Claim.review_priority == priority)
    
    claims = query.order_by(Claim.confidence.asc()).limit(50).all()
    
    return {
        "claims": [
            {
                "id": c.id,
                "claim_text": c.claim_text,
                "status": c.status.value,
                "confidence": c.confidence,
                "priority": c.review_priority,
                "explanation": c.explanation
            }
            for c in claims
        ]
    }

@router.post("/{claim_id}/approve")
async def approve_claim(
    claim_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Approve a reviewed claim"""
    if not user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(404, "Claim not found")
    
    claim.needs_review = False
    db.commit()
    
    return {"status": "approved", "claim_id": claim_id}
```

---

### Fix 3: Integrate Multi-Agent System (Optional but Recommended)

#### Step 1: Update Verification to Use Orchestrator

In `tasks/fact_check.py`:

```python
from app.agents.verification_team import VerificationOrchestrator

async def verify_source(source_id: str):
    # ... build context with RAG ...
    
    # Option 1: Use multi-agent system (more accurate but slower)
    orchestrator = VerificationOrchestrator()
    agent_result = await orchestrator.verify_claim(claim_text, context)
    
    final_verdict = agent_result["final_verdict"]
    
    # Store with agent findings
    claim = Claim(
        # ... existing fields ...
        status=VerificationStatus(final_verdict["status"]),
        explanation=final_verdict["explanation"],
        confidence=final_verdict["confidence"],
        agent_findings=json.dumps(agent_result["agent_results"])  # Store agent analysis
    )
    
    # Option 2: Use single-agent (faster, less accurate)
    # verification = await checker._verify_claim_with_evidence(...)
```

---

## Testing Checklist

- [ ] RAG pipeline fetches evidence content
- [ ] LLM receives actual article text (not just URLs)
- [ ] Confidence scores are generated (0.0-1.0)
- [ ] Low-confidence claims flagged for review
- [ ] Similar claims detected (deduplication)
- [ ] Historical context used in verification
- [ ] Source credibility tiers applied
- [ ] Multi-agent system integrated (if implemented)
- [ ] Review queue endpoint working
- [ ] Database migration successful

---

## Performance Considerations

### API Costs
- **Current**: ~2-3 LLM calls per claim
- **With RAG**: ~2-3 LLM calls + content fetching (HTTP)
- **With Multi-Agent**: ~5-6 LLM calls per claim (4 agents + synthesis)

### Processing Time
- **Current**: ~5-10 seconds per claim
- **With RAG**: ~10-15 seconds (content fetching adds time)
- **With Multi-Agent**: ~20-30 seconds (parallel agents)

### Optimization Tips
1. Cache evidence content (avoid re-fetching)
2. Use parallel processing for agents
3. Limit evidence content length (2000 chars per source)
4. Skip multi-agent for high-confidence simple claims

---

## Monitoring

Track these metrics:
- **Average Confidence**: Should increase with improvements
- **Review Queue Size**: Claims needing human review
- **Evidence Quality**: % of claims with "strong" evidence
- **Deduplication Rate**: % of duplicate claims caught
- **Processing Time**: Time per claim
- **API Costs**: LLM calls per claim

---

## Next Steps After Phase 1

1. **Measure Impact**: Compare accuracy before/after
2. **Tune Thresholds**: Adjust confidence thresholds based on data
3. **Add Monitoring**: Dashboard for review queue
4. **Phase 2**: Integrate multi-agent system if Phase 1 shows improvement

