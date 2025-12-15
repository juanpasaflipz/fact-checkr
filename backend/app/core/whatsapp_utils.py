
import os
import logging
import httpx
from typing import List, Dict, Any, Optional
from app.database.models import Claim as DBClaim, VerificationStatus

logger = logging.getLogger(__name__)

# WhatsApp configuration
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")

from app.core import messages

async def send_whatsapp_message(to: str, message: str):
    """Send WhatsApp message using Meta Graph API"""
    if not WHATSAPP_PHONE_NUMBER_ID or not WHATSAPP_ACCESS_TOKEN:
        logger.warning("WhatsApp credentials not configured")
        return
    
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

def format_claim_for_whatsapp(claim: DBClaim) -> str:
    """Format claim verification result for WhatsApp message using new templates"""
    
    # Extract bullets from explanation or key_evidence_points
    # This is a heuristic until we have dedicated bullet fields
    bullets = []
    if claim.key_evidence_points:
        # Assuming list of strings or list of dicts
        if isinstance(claim.key_evidence_points, list):
            bullets = [str(p) for p in claim.key_evidence_points]
    
    if not bullets and claim.explanation:
        # Split explanation by sentences as fallback
        bullets = [s.strip() for s in claim.explanation.split('.') if s.strip()][:3]
        
    if not bullets:
        bullets = ["Verificación completa disponible en el enlace."]

    # Construct URLs
    frontend_url = os.getenv("FRONTEND_URL", "https://factcheck.mx")
    receipt_url = f"{frontend_url}/receipts/{claim.id}"
    share_link = f"https://wa.me/?text={receipt_url}"

    return messages.msg_verdict(
        status=claim.status,
        confidence=claim.confidence or 0.9, # Default to high if verified
        bullets=bullets,
        receipt_url=receipt_url,
        share_link=share_link
    )
