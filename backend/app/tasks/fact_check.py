import asyncio
from celery import shared_task
from app.database import SessionLocal, Source, Claim, VerificationStatus
from app.agent import FactChecker
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

        # Initialize FactChecker
        checker = FactChecker()
        
        # 1. Extract Claim
        claim_text = await checker._extract_claim(source.content)
        
        if claim_text == "SKIP":
            source.processed = 2 # Skipped
            db.commit()
            return
            
        # 2. Search Evidence (using checker's method if available or direct search)
        # We need to access search_web from agent.py or utils
        from app.agent import search_web
        evidence_links = await search_web(claim_text)
        filtered_evidence = checker._filter_sources(evidence_links)
        
        # 3. Verify
        verification = await checker._verify_claim(claim_text, filtered_evidence)
        
        # 4. Extract Entities
        from app.database.models import Entity as DBEntity
        entities = await checker._extract_entities(claim_text)
        
        # 5. Store Claim
        claim = Claim(
            id=f"claim_{source.id}",
            source_id=source.id,
            original_text=source.content,
            claim_text=claim_text,
            status=VerificationStatus(verification.status),
            explanation=verification.explanation,
            evidence_sources=verification.sources
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
        
        source.processed = 1 # Processed
        db.commit()
        
        logger.info(f"Verified claim for source {source_id}: {verification.status} with {len(entities)} entities")
        return claim.id
        
    except Exception as e:
        logger.error(f"Error verifying source {source_id}: {e}")
        db.rollback()
    finally:
        db.close()

@shared_task
def process_source(source_id: str):
    """Celery task to process a single source"""
    # Run async function in sync Celery task
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(verify_source(source_id))
