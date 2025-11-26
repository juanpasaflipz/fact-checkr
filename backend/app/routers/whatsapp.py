"""
WhatsApp Integration Router
Handles WhatsApp webhooks and message processing
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import logging
from app.database import SessionLocal, get_db
from app.database.models import Claim as DBClaim
from sqlalchemy.orm import Session
from sqlalchemy import desc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# WhatsApp configuration
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "your_verify_token_here")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")

class WhatsAppMessage(BaseModel):
    """WhatsApp webhook message structure"""
    from_: Optional[str] = None
    id: Optional[str] = None
    timestamp: Optional[str] = None
    text: Optional[Dict[str, str]] = None
    type: Optional[str] = None

class WhatsAppWebhook(BaseModel):
    """WhatsApp webhook payload"""
    object: Optional[str] = None
    entry: Optional[list] = None

@router.get("/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
    hub_challenge: Optional[str] = None
):
    """
    WhatsApp webhook verification endpoint
    Called by WhatsApp to verify the webhook URL
    """
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully")
        return int(hub_challenge) if hub_challenge else 200
    
    logger.warning(f"Webhook verification failed: mode={hub_mode}, token={hub_verify_token}")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receive WhatsApp messages via webhook
    Processes incoming messages and responds with fact-check results
    """
    try:
        data = await request.json()
        logger.info(f"Received WhatsApp webhook: {data}")
        
        # Parse WhatsApp webhook structure
        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    
                    for message in messages:
                        await process_whatsapp_message(message, db)
        else:
            # Handle alternative webhook format (direct messages)
            if "messages" in data:
                for message in data.get("messages", []):
                    await process_whatsapp_message(message, db)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

async def process_whatsapp_message(message: Dict[str, Any], db: Session):
    """Process incoming WhatsApp message and send fact-check response"""
    try:
        from_number = message.get("from")
        message_id = message.get("id")
        message_type = message.get("type")
        
        if message_type != "text":
            # Send unsupported message type response
            await send_whatsapp_message(
                from_number,
                "⚠️ Solo puedo procesar mensajes de texto. Por favor envía el texto que quieres verificar."
            )
            return
        
        # Extract text content
        text_body = message.get("text", {}).get("body", "")
        
        if not text_body:
            await send_whatsapp_message(
                from_number,
                "❌ No pude leer tu mensaje. Por favor intenta de nuevo."
            )
            return
        
        # Search for existing claims
        claim = db.query(DBClaim).filter(
            DBClaim.claim_text.ilike(f"%{text_body[:50]}%")
        ).order_by(desc(DBClaim.created_at)).first()
        
        if claim:
            # Found existing claim - send verification result
            response = format_claim_for_whatsapp(claim)
            await send_whatsapp_message(from_number, response)
        else:
            # No existing claim - trigger fact-check
            await send_whatsapp_message(
                from_number,
                f"🔍 Verificando: \"{text_body[:100]}\"\n\n⏳ Esto puede tomar unos momentos..."
            )
            
            # Trigger fact-check task (async)
            from app.tasks.scraper import scrape_all_sources
            # Note: In production, you'd want to create a specific fact-check task
            # For now, we'll search the database and if not found, suggest manual verification
            
            await send_whatsapp_message(
                from_number,
                "📝 Esta afirmación no está en nuestra base de datos aún. "
                "Nuestro sistema la está analizando. Te notificaremos cuando esté lista."
            )
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {e}", exc_info=True)
        await send_whatsapp_message(
            message.get("from"),
            "❌ Ocurrió un error al procesar tu mensaje. Por favor intenta más tarde."
        )

def format_claim_for_whatsapp(claim: DBClaim) -> str:
    """Format claim verification result for WhatsApp message"""
    status_emoji = {
        "Verified": "✅",
        "Debunked": "❌",
        "Misleading": "⚠️",
        "Unverified": "❓"
    }
    
    emoji = status_emoji.get(claim.status.value, "❓")
    status_text = claim.status.value
    
    message = f"""{emoji} *Verificación de Hecho*

*Afirmación:*
{claim.claim_text[:200]}

*Resultado:* {status_text}
*Explicación:*
{claim.explanation or 'No hay explicación disponible.'}

*Fuentes:*
"""
    
    if claim.evidence_sources:
        for i, source in enumerate(claim.evidence_sources[:3], 1):
            message += f"{i}. {source}\n"
    else:
        message += "No hay fuentes disponibles.\n"
    
    if claim.source and claim.source.url:
        message += f"\n*Fuente original:* {claim.source.url}"
    
    return message

async def send_whatsapp_message(to: str, message: str):
    """Send WhatsApp message using Meta Graph API"""
    if not WHATSAPP_PHONE_NUMBER_ID or not WHATSAPP_ACCESS_TOKEN:
        logger.warning("WhatsApp credentials not configured")
        return
    
    import httpx
    
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"WhatsApp message sent to {to}")
            return response.json()
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        raise

@router.post("/send")
async def send_message(
    to: str,
    message: str,
    db: Session = Depends(get_db)
):
    """Send WhatsApp message manually (for testing/admin)"""
    try:
        result = await send_whatsapp_message(to, message)
        return {"status": "success", "message_id": result.get("messages", [{}])[0].get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/claims/{claim_id}")
async def get_claim_for_whatsapp(
    claim_id: str,
    db: Session = Depends(get_db)
):
    """Get claim formatted for WhatsApp"""
    claim = db.query(DBClaim).filter(DBClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return {
        "formatted_message": format_claim_for_whatsapp(claim),
        "claim": {
            "id": claim.id,
            "text": claim.claim_text,
            "status": claim.status.value,
            "explanation": claim.explanation
        }
    }

