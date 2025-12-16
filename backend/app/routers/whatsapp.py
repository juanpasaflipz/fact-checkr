"""
WhatsApp Integration Router
Handles WhatsApp webhooks and message processing
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import logging
import hmac
import hashlib
from app.database import SessionLocal, get_db
from app.database.models import Claim as DBClaim, WhatsAppMessage as DBWhatsAppMessage, WhatsAppUser as DBWhatsAppUser
# from app.worker import celery_app # Removed
from datetime import datetime
from app.core.whatsapp_utils import send_whatsapp_message, format_claim_for_whatsapp
from sqlalchemy.orm import Session
from sqlalchemy import desc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# WhatsApp configuration
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "my_secret")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET")

async def verify_signature(request: Request):
    """Verify that the payload came from WhatsApp"""
    if not WHATSAPP_APP_SECRET:
        logger.warning("WHATSAPP_APP_SECRET not set, skipping signature verification")
        return True
        
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=403, detail="Missing signature")
    
    body = await request.body()
    expected_signature = hmac.new(
        key=WHATSAPP_APP_SECRET.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(f"sha256={expected_signature}", signature):
        logger.warning(f"Invalid signature. Expected: {expected_signature}, Got: {signature}")
        raise HTTPException(status_code=403, detail="Invalid signature")

    return True

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
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """
    WhatsApp webhook verification endpoint
    Called by WhatsApp to verify the webhook URL
    """
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully")
        return PlainTextResponse(content=hub_challenge or "", status_code=200)
    
    logger.warning(f"Webhook verification failed: mode={hub_mode}, token={hub_verify_token}")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook", dependencies=[Depends(verify_signature)])
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
                        await process_incoming_message(message, db)
        else:
            # Handle alternative webhook format (direct messages)
            if "messages" in data:
                for message in data.get("messages", []):
                    await process_incoming_message(message, db)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# ... imports
from app.core import messages

# ... (keep existing imports)

# ... inside process_whatsapp_message

async def process_incoming_message(message: Dict[str, Any], db: Session):
    """Store message and enqueue for processing"""
    try:
        wa_message_id = message.get("id")
        if not wa_message_id:
            return

        # Idempotency check
        existing = db.query(DBWhatsAppMessage).filter(
            DBWhatsAppMessage.wa_message_id == wa_message_id
        ).first()
        
        if existing:
            logger.info(f"Skipping duplicate message {wa_message_id}")
            return

        from_number = message.get("from")
        # Simple hash of phone number for basic privacy/lookup
        phone_hash = hashlib.sha256(from_number.encode()).hexdigest()
        
        # Get or create user
        user = db.query(DBWhatsAppUser).filter(
            DBWhatsAppUser.phone_hash == phone_hash
        ).first()
        
        if not user:
            user = DBWhatsAppUser(phone_hash=phone_hash)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Store message
        content_body = message.get("text", {}).get("body", "")
        msg_type = message.get("type", "unknown")
        
        new_msg = DBWhatsAppMessage(
            user_id=user.id,
            wa_message_id=wa_message_id,
            message_type=msg_type,
            content=content_body,
            status="received"
        )
        db.add(new_msg)
        db.commit()
        db.refresh(new_msg)
        
        logger.info(f"Stored message {new_msg.id} from user {user.id}")

        # Enqueue for async processing
        # We pass the internal ID and the phone number (since we don't store raw number in DB)
        from app.infra.cloud_tasks import enqueue_task
        enqueue_task(
            task_name="process_whatsapp_message",
            payload={
                "task_type": "process_whatsapp_message",
                "whatsapp_message_id": str(new_msg.id),
                "from_number": from_number,
                "message_text": content_body,
                "timestamp": str(datetime.utcnow())
            },
            idempotency_key=f"wa_msg_{new_msg.id}" 
        )

        
    except Exception as e:
        logger.error(f"Error storing/enqueuing message: {e}", exc_info=True)
        # We don't raise here to ensure we return 200 OK to WhatsApp


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


@router.get("/users")
async def get_whatsapp_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List WhatsApp users (admin only)"""
    users = db.query(DBWhatsAppUser)\
        .order_by(desc(DBWhatsAppUser.created_at))\
        .offset(skip)\
        .limit(limit)\
        .all()
    return users

@router.get("/users/{user_id}")
async def get_whatsapp_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get specific WhatsApp user"""
    user = db.query(DBWhatsAppUser).filter(DBWhatsAppUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/messages/{user_id}")
async def get_user_messages(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get messages for a specific user"""
    messages = db.query(DBWhatsAppMessage)\
        .filter(DBWhatsAppMessage.user_id == user_id)\
        .order_by(desc(DBWhatsAppMessage.created_at))\
        .offset(skip)\
        .limit(limit)\
        .all()
    return messages

