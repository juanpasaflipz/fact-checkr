"""
Centralized repository for user-facing strings and message templates.
Implements the "Calm Observer" design system for WhatsApp (ES-MX).
"""
from typing import List, Optional, Dict
from enum import Enum
from app.database.models import VerificationStatus

# =============================================================================
# 1. Voice & Tone Constants
# =============================================================================

class Tone(str, Enum):
    CALM = "calm"
    NEUTRAL = "neutral"
    SHAREABLE = "shareable"

# Core rules implemented as format string templates or constants
FEEDBACK_POSITIVE = "Gracias por verificar antes de compartir. Ayudas a mantener limpia la conversación."
FEEDBACK_NEUTRAL = "Es normal que esta información cause confusión por cómo está presentada."
FEEDBACK_SHARE = "Al compartir información verificada, proteges a tus grupos."

# =============================================================================
# 2. Verdict Ladder Mapping
# =============================================================================

# Maps database internal status to external UI keys and emojis
VERDICT_MAP = {
    VerificationStatus.VERIFIED: {
        "label": "Verdadero",
        "emoji": "🟢",
        "tone": "Directo, confirmatorio",
        "description": "Los registros confirman esta información."
    },
    VerificationStatus.MOSTLY_TRUE: {
        "label": "Mayormente verdadero",
        "emoji": "🟢",
        "tone": "Matizado",
        "description": "Es correcto en lo principal, aunque con imprecisiones menores."
    },
    VerificationStatus.MIXED: {
        "label": "Mixto / Falta contexto",
        "emoji": "🟡",
        "tone": "Explicativo",
        "description": "Contiene elementos reales pero omite contexto clave."
    },
    VerificationStatus.MOSTLY_FALSE: {
        "label": "Mayormente engañoso",
        "emoji": "🟠",
        "tone": "Correctivo",
        "description": "Usa un dato real para llegar a una conclusión falsa."
    },
    VerificationStatus.DEBUNKED: {
        "label": "Engañoso",
        "emoji": "🔴",
        "tone": "Neutral",
        "description": "No existen registros que respalden esto."
    },
    VerificationStatus.UNVERIFIED: {
        "label": "No verificable aún",
        "emoji": "⚪️",
        "tone": "Honesto",
        "description": "La información está en desarrollo o es insuficiente."
    },
    # Legacy fallbacks
    VerificationStatus.MISLEADING: {
        "label": "Mayormente engañoso",
        "emoji": "🟠",
        "tone": "Correctivo",
        "description": "Podría inducir a error."
    }
}

# =============================================================================
# 3. WhatsApp Message Templates
# =============================================================================

def msg_immediate_acknowledgement() -> str:
    """Template A: Immediate Acknowledgement"""
    return (
        "👋 *Hola.* Recibí tu consulta.\n\n"
        "Nuestro sistema está buscando información confiable sobre esto.\n\n"
        "⏳ *Dame un momento...*"
    )

def msg_processing_long() -> str:
    """For when it takes longer than expected"""
    return (
        "🔍 Sigo analizando la información...\n"
        "Estamos consultando múltiples fuentes para darte la mejor respuesta."
    )

def msg_verdict(
    status: VerificationStatus,
    confidence: float,
    bullets: List[str],
    receipt_url: str,
    share_link: str
) -> str:
    """
    Template B: Final Verdict
    
    Args:
        status: The verification status enum
        confidence: Float 0.0-1.0
        bullets: List of up to 3 explanation points
        receipt_url: URL to the web receipt
        share_link: Link to share this verification
    """
    verdict_info = VERDICT_MAP.get(status, VERDICT_MAP[VerificationStatus.UNVERIFIED])
    emoji = verdict_info["emoji"]
    label = verdict_info["label"]
    conf_percent = int(confidence * 100)
    
    # Format bullets
    bullet_text = "\n".join([f"• {b}" for b in bullets[:3]])
    
    return f"""{emoji} *Resultado: {label}*

*Confianza:* {conf_percent}%

*¿Por qué?*
{bullet_text}

🔗 *Ver fuentes y detalles:*
{receipt_url}

📤 *Compartir esta verificación:*
{share_link}"""

def msg_high_uncertainty(known_facts: List[str], missing_info: List[str]) -> str:
    """Template C: High-Uncertainty Case"""
    known_text = "\n".join([f"• {f}" for f in known_facts])
    missing_text = "\n".join([f"• {f}" for f in missing_info])
    
    return f"""⚪️ *Resultado: No verificable aún*

La información disponible es limitada o contradictoria en este momento.

*Lo que sabemos:*
{known_text}

*Lo que falta:*
{missing_text}

Te avisaremos si surge evidencia más clara."""

def msg_unsupported_type() -> str:
    return (
        "⚠️ Solo puedo procesar mensajes de texto por ahora.\n"
        "Por favor envía el texto o enlace que quieres verificar."
    )

def msg_readable_error() -> str:
    return (
        "❌ Tuve un problema técnico momentáneo.\n"
        "Por favor intenta reenviar tu mensaje en unos minutos."
    )

# =============================================================================
# 4. Truth Card Templates
# =============================================================================

def format_truth_card_political(claim: str, verdict: VerificationStatus, summary: str, url: str) -> str:
    """Variant 1: Political / Policy (Compact)"""
    v_label = VERDICT_MAP.get(verdict, VERDICT_MAP[VerificationStatus.UNVERIFIED])["label"]
    
    return f"""📌 *Verificado por FactCheck MX*

🗣️ *Dicho:* "{claim}"

⚖️ *Realidad:* {v_label}. {summary}

🔗 *Evidencia:* {url}"""

def format_truth_card_health(claim: str, verdict: VerificationStatus, correction: str, url: str) -> str:
    """Variant 2: Health / Safety (Urgent)"""
    v_label = VERDICT_MAP.get(verdict, VERDICT_MAP[VerificationStatus.UNVERIFIED])["label"]
    
    return f"""🛡️ *Información de Salud*

❌ *Circula:* "{claim}"

👩‍⚕️ *Datos médicos:* {v_label}. {correction}

📥 *Ver fuentes:* {url}"""

def format_truth_card_economy(claim: str, verdict: VerificationStatus, context: str, url: str) -> str:
    """Variant 3: Economy (Data-heavy)"""
    v_label = VERDICT_MAP.get(verdict, VERDICT_MAP[VerificationStatus.UNVERIFIED])["label"]
    
    return f"""📊 *Dato Verificado*

📉 *Afirmación:* "{claim}"

💡 *Contexto:* {v_label}. {context}

🔎 *Detalles:* {url}"""
