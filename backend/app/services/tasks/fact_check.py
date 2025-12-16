
import asyncio
from app.core.config import settings
from app.database import SessionLocal, Source, Claim, VerificationStatus
from app.agents import FactChecker
from app.schemas import VerificationResult, EvidenceDetail
from app.services.rag_pipeline import RAGPipeline
import logging
import json

logger = logging.getLogger(__name__)

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

        # Initialize FactChecker and RAG Pipeline
        checker = FactChecker()
        rag = RAGPipeline()
        
        # 1. Extract Claim
        claim_text = await checker._extract_claim(source.content)
        
        if claim_text.replace('"', '').replace("'", "").strip() == "SKIP":
            source.processed = 2 # Skipped
            db.commit()
            return
        
        # 2. Build rich context using RAG pipeline
        logger.info(f"Building verification context for claim: {claim_text[:100]}...")
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
                    # Link to existing claim instead of re-verifying
                    source.processed = 1
                    db.commit()
                    logger.info(f"Linked source {source_id} to existing claim {similar_claim_id} (similarity: {similar_claims[0].get('similarity', 0):.2f})")
                    return existing_claim.id
        
        # 4. Get evidence with actual content
        evidence_urls = context.get("evidence_urls", [])
        evidence_texts = context.get("evidence_texts", [])
        web_evidence = context.get("web_evidence", [])  # Contains title, snippet, domain info
        
        # If no evidence texts, try to fetch them
        if not evidence_texts and evidence_urls:
            logger.info(f"Fetching content from {len(evidence_urls)} evidence URLs...")
            evidence_texts = await rag._fetch_evidence_content(evidence_urls[:5])
        
        # Build evidence_details with snippets
        evidence_details = []
        for i, url in enumerate(evidence_urls[:5]):  # Limit to top 5
            snippet = ""
            title = ""
            domain = ""
            
            # Try to get snippet from web_evidence first (has title/snippet from search)
            for evidence in web_evidence:
                if evidence.get("url") == url:
                    snippet = evidence.get("snippet", "")[:200]
                    title = evidence.get("title", "")
                    domain = evidence.get("domain", "")
                    break
            
            # If no snippet from search, extract from fetched content
            if not snippet and i < len(evidence_texts) and evidence_texts[i]:
                snippet = evidence_texts[i][:200]
            
            # Extract domain if not found
            if not domain:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    domain = parsed.netloc.lower().replace("www.", "")
                except:
                    domain = ""
            
            evidence_details.append({
                "url": url,
                "snippet": snippet,
                "timestamp": None,  # Could be extracted from page if available
                "relevance_score": 1.0 - (i * 0.1),  # Higher relevance for earlier results
                "title": title,
                "domain": domain
            })
        
        # 5. Verify with enhanced context and evidence content
        # Option: Use multi-agent system for higher accuracy (can be toggled)
        use_multi_agent = settings.USE_MULTI_AGENT_VERIFICATION
        
        if use_multi_agent:
            logger.info(f"Using multi-agent verification system...")
            from app.agents.verification_team import VerificationOrchestrator
            
            orchestrator = VerificationOrchestrator()
            agent_result = await orchestrator.verify_claim(claim_text, context)
            
            final_verdict = agent_result["final_verdict"]
            
            # Convert to VerificationResult format
            status_map = {
                "Verified": VerificationStatus.VERIFIED,
                "Debunked": VerificationStatus.DEBUNKED,
                "Misleading": VerificationStatus.MISLEADING,
                "Unverified": VerificationStatus.UNVERIFIED
            }
            
            # Map final verdict to VerificationResult
            verdict_status = final_verdict.get("status", "Unverified")
            # Handle case where status might be full enum value
            if isinstance(verdict_status, str):
                verdict_status = status_map.get(verdict_status, VerificationStatus.UNVERIFIED)
            else:
                verdict_status = VerificationStatus.UNVERIFIED
            
            # Convert evidence_details dicts to EvidenceDetail objects
            evidence_details_objects = None
            if evidence_details:
                evidence_details_objects = [
                    EvidenceDetail(**ed) for ed in evidence_details
                ]
            
            verification = VerificationResult(
                status=verdict_status,
                explanation=final_verdict.get("explanation", "No se pudo verificar."),
                sources=evidence_urls,
                evidence_details=evidence_details_objects,
                confidence=final_verdict.get("confidence", 0.5),
                evidence_strength="strong" if final_verdict.get("confidence", 0.5) > 0.7 else "moderate" if final_verdict.get("confidence", 0.5) > 0.5 else "weak",
                key_evidence_points=final_verdict.get("key_evidence", [])
            )
            
            # Store agent findings
            agent_findings = agent_result.get("agent_results", [])
        else:
            logger.info(f"Verifying claim with {len(evidence_texts)} evidence sources...")
            verification = await checker._verify_claim_with_evidence(
                claim_text,
                evidence_urls,
                evidence_texts,
                context
            )
            # Add evidence_details to verification result
            if evidence_details:
                verification.evidence_details = [EvidenceDetail(**ed) for ed in evidence_details]
            agent_findings = None
        
        # 4. Extract Entities
        from app.database.models import Entity as DBEntity
        entities = await checker._extract_entities(claim_text)
        
        # 5. Extract Topics
        from app.database.models import Topic as DBTopic
        # Get available topics from database
        available_topics = db.query(DBTopic).all()
        topics_list = [{"name": t.name, "slug": t.slug} for t in available_topics]
        
        # Extract topics using AI
        topic_names = await checker._extract_topics(claim_text, topics_list)
        
        # 6. Store Claim with enhanced fields
        # Determine if review is needed based on confidence
        needs_review = verification.confidence < 0.6
        review_priority = None
        if verification.confidence < 0.4:
            review_priority = "high"
        elif verification.confidence < 0.6:
            review_priority = "medium"
        
        # Convert evidence_details to JSON format for storage
        evidence_details_json = None
        source_domains = []
        if verification.evidence_details:
            evidence_details_json = []
            for ed in verification.evidence_details:
                evidence_details_json.append({
                    "url": ed.url,
                    "snippet": ed.snippet,
                    "timestamp": ed.timestamp,
                    "relevance_score": ed.relevance_score,
                    "title": ed.title,
                    "domain": ed.domain
                })
                if ed.domain:
                    source_domains.append(ed.domain)
        
        # Deduplicate domains
        source_domains = list(set(source_domains))

        # Generate Visual Verdict Card
        image_url = None
        try:
            from app.services.visual_generator import VisualGenerator
            visual_gen = VisualGenerator()
            # If we have agent findings with structured source types, use them? 
            # For now, we use the specific domains we found.
            image_path = visual_gen.generate_verdict_card(
                claim_text=claim_text,
                verdict=verification.status.value,  # Enum value
                explanation=verification.explanation,
                sources=source_domains
            )
            if image_path:
                # Store relative path for frontend serving
                image_url = "/" + os.path.relpath(image_path, "app")
        except Exception as e:
            logger.error(f"Failed to generate verdict card: {e}")

        claim = Claim(
            id=f"claim_{source.id}",
            source_id=source.id,
            original_text=source.content,
            claim_text=claim_text,
            status=VerificationStatus(verification.status),
            explanation=verification.explanation,
            evidence_sources=verification.sources,
            evidence_details=evidence_details_json,
            confidence=verification.confidence,
            evidence_strength=verification.evidence_strength,
            key_evidence_points=verification.key_evidence_points,
            needs_review=needs_review,
            review_priority=review_priority,
            agent_findings=json.dumps(agent_findings) if agent_findings else None,
            image_url=image_url
        )
        
        db.add(claim)
        db.flush()  # Flush to get claim ID
        
        # Link entities to database
        for entity_name, entity_type in entities:
            db_entity = db.query(DBEntity).filter(DBEntity.name == entity_name).first()
            if not db_entity:
                db_entity = DBEntity(name=entity_name, entity_type=entity_type)
                db.add(db_entity)
                db.flush()
            # Note: Would need junction table for many-to-many if implementing entity-claim links
        
        # Link topics to claim
        from app.database.models import claim_topics
        linked_topics = []
        for topic_name in topic_names:
            db_topic = db.query(DBTopic).filter(DBTopic.name == topic_name).first()
            if db_topic:
                # Use the relationship to link topics
                claim.topics.append(db_topic)
                linked_topics.append(topic_name)
            else:
                logger.warning(f"Topic '{topic_name}' not found in database. Skipping.")
        
        db.flush()
        
        source.processed = 1 # Processed
        db.commit()
        
        logger.info(
            f"Verified claim for source {source_id}: {verification.status} "
            f"(confidence: {verification.confidence:.2f}, evidence: {verification.evidence_strength}) "
            f"with {len(entities)} entities and {len(linked_topics)} topics: {linked_topics}"
        )
        if needs_review:
            logger.warning(f"Claim {claim.id} flagged for review (priority: {review_priority})")
        return claim.id
        
    except Exception as e:
        logger.error(f"Error verifying source {source_id}: {e}")
        db.rollback()
    finally:
        db.close()
