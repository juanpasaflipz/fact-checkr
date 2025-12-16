
import asyncio
import logging
import os
import hashlib
import httpx
from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.database.models import (
    WhatsAppMessage as DBWhatsAppMessage,
    WhatsAppUser as DBWhatsAppUser,
    Claim as DBClaim,
    Verdict as DBVerdict,
    Evidence as DBEvidence,
    VerificationStatus
)
# from app.worker import celery_app # REMOVED
from app.core.whatsapp_utils import send_whatsapp_message, format_claim_for_whatsapp
from app.services.claim_extraction import ClaimExtractionService
from app.services.verification import VerificationService
from app.services.search_service import search_web_rich

# Initialize AI clients
from anthropic import Anthropic
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize clients lazily or globally? 
# Better to initialize inside task or global if thread-safe. 
# API clients are usually thread-safe.
anthropic_client = None
openai_client = None

if os.getenv("ANTHROPIC_API_KEY"):
    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

if os.getenv("OPENAI_API_KEY"):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Logic moved from Celery task, now a plain async function
async def process_message_logic(message_id: int, phone_number: str):
    """
    Logic to process incoming WhatsApp messages.
    """
    logger.info(f"Processing message {message_id} from {phone_number}")
    db = SessionLocal()
    try:
        await process_message_async(message_id, phone_number, db)
    except Exception as e:
        logger.error(f"Error in process_message_logic for msg {message_id}: {e}", exc_info=True)
        # We re-raise to let Cloud Tasks retry (non-2xx response)
        raise
    finally:
        db.close()

async def process_message_async(message_id: int, phone_number: str, db: Session):
    # 1. Retrieve message with strict idempotency
    message = db.query(DBWhatsAppMessage).filter(DBWhatsAppMessage.id == message_id).first()
    if not message:
        logger.error(f"Message {message_id} not found")
        return

    # Normalize phone number for Mexico: 521XXXXXXXXXX -> 52XXXXXXXXXX
    # Meta sends 521... but requires 52... for the allowed list check in Dev mode
    if phone_number.startswith("521") and len(phone_number) == 13:
        phone_number = "52" + phone_number[3:]
        logger.info(f"Normalized Mexico phone number to: {phone_number}")

    # IDEMPOTENCY CHECK
    if message.status in ["completed", "failed", "skipped"]:
        logger.info(f"Message {message_id} already processed with status: {message.status}. Skipping.")
        return

    if message.status == "processing":
        # Check if it's been processing for too long (stale) could be an enhancement,
        # but for now we assume a retry might be valid if it failed mid-flight without updating DB.
        # However, to be safe during simple retries, we might want to allow re-processing if it crashed.
        # But if we want strict exactly-once for user replies, we need to be careful.
        # Let's proceed, logging re-entry.
        logger.info(f"Resuming processing for message {message_id}")

    # Update status
    message.status = "processing"
    db.commit()

    try:
        # 2. Extract Claim
        extraction_service = ClaimExtractionService(anthropic_client=anthropic_client, openai_client=openai_client)
        claim_text = await extraction_service.extract_claim(message.content)

        if claim_text == "SKIP" or not claim_text:
            # Fallback: Treat as a general news query/topic search
            # This allows the bot to answer "Qué pasa con la reforma judicial?"
            logger.info(f"No specific claim found in message {message_id}. Treating as news query.")
            
            # Send "Searching news" placeholder
            await send_whatsapp_message(
                phone_number, 
                "📰 No detecté una afirmación específica para verificar, así que buscaré noticias recientes sobre este tema..."
            )
            
            from app.services.search_service import search_news
            news_results = await search_news(message.content)
            
            if not news_results:
                await send_whatsapp_message(
                    phone_number, 
                    "No encontré noticias recientes sobre ese tema. Intenta ser más específico o preguntar sobre otro asunto."
                )
            else:
                # Format news results
                response = "📢 *Noticias Recientes:*\n\n"
                for item in news_results[:3]:
                    response += f"🔹 *{item.get('title')}*\n"
                    response += f"{item.get('snippet', '')[:100]}...\n"
                    response += f"🔗 {item.get('link')}\n\n"
                
                await send_whatsapp_message(phone_number, response)

            message.status = "completed"
            db.commit()
            return

        # 3. Check DB for existing claim (Phase 1/2 constraint: ilike)
        existing_claim = db.query(DBClaim).filter(
            DBClaim.claim_text.ilike(f"%{claim_text[:50]}%")
        ).order_by(desc(DBClaim.created_at)).first()

        if existing_claim:
            logger.info(f"Found existing claim {existing_claim.id} for message {message_id}")
            response_text = format_claim_for_whatsapp(existing_claim)
            await send_whatsapp_message(phone_number, response_text)
            
            message.status = "completed"
            db.commit()
            return

        # 4. If new, verify with AI + Search
        # Only send generic "checking" message if this is the first attempt
        # (Naive check: if we haven't created a claim yet)
        await send_whatsapp_message(
            phone_number, 
            "🔎 Estamos verificando esta información. Te enviaremos el resultado en breve..."
        )

        search_results = await search_web_rich(claim_text)
        evidence_urls = [r['link'] for r in search_results]
        evidence_texts = [r['snippet'] for r in search_results]
        
        verification_service = VerificationService(anthropic_client=anthropic_client, openai_client=openai_client)
        result = await verification_service.verify_claim_with_evidence(
            claim=claim_text,
            evidence_urls=evidence_urls,
            evidence_texts=evidence_texts
        )

        # 5. Save results
        new_claim = DBClaim(
            original_text=message.content,
            claim_text=claim_text,
            status=result.status,
            explanation=result.explanation,
            confidence=result.confidence,
            key_evidence_points=result.key_evidence_points,
            created_at=datetime.utcnow(),
            source_id="whatsapp" 
        )
        new_claim.source_id = None 
        
        db.add(new_claim)
        db.commit()
        db.refresh(new_claim)

        # Create Verdict 
        verdict = DBVerdict(
            claim_id=new_claim.id,
            label=result.status,
            confidence=result.confidence,
            explanation_short=[result.explanation],
            explanation_long=result.explanation,
            created_at=datetime.utcnow()
        )
        db.add(verdict)

        # Create Evidence
        for url, snippet in zip(evidence_urls, evidence_texts):
            evidence = DBEvidence(
                claim_id=new_claim.id,
                url=url,
                quote=snippet[:500],
                reliability="unknown",
                retrieved_at=datetime.utcnow()
            )
            db.add(evidence)
        
        db.commit()

        # 6. Reply to user
        response_text = format_claim_for_whatsapp(new_claim)
        await send_whatsapp_message(phone_number, response_text)

        message.status = "completed"
        db.commit()
        logger.info(f"Successfully processed message {message_id}")

    except Exception as e:
        logger.error(f"Error logic for message {message_id}: {e}", exc_info=True)
        # We allow exception to propagate so it can be retried or logged at higher level
        raise e
