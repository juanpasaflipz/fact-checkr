import pytest
from datetime import datetime
from app.core.whatsapp_utils import format_claim_for_whatsapp
from app.database.models import Claim, VerificationStatus

from unittest import mock
import os

@mock.patch("app.core.whatsapp_utils.settings")
def test_format_claim_verified(mock_settings):
    mock_settings.get_frontend_url.return_value = "https://factcheck.mx"
    claim = Claim(
        id=1,
        claim_text="El cielo es azul",
        status=VerificationStatus.VERIFIED,
        confidence=0.95,
        explanation="Es verdad porque la disperción de Rayleigh.",
        key_evidence_points=["Punto 1", "Punto 2"],
        created_at=datetime.utcnow()
    )
    msg = format_claim_for_whatsapp(claim)
    assert "🟢" in msg
    assert "Verdadero" in msg
    assert "factcheck.mx/receipts/1" in msg

def test_format_claim_debunked():
    claim = Claim(
        id=2,
        claim_text="La tierra es plana",
        status=VerificationStatus.DEBUNKED,
        confidence=0.99,
        explanation="Falso, es redonda.",
        key_evidence_points=["Fotos satelitales"],
        created_at=datetime.utcnow()
    )
    msg = format_claim_for_whatsapp(claim)
    assert "🔴" in msg
    assert "Engañoso" in msg # DEBUNKED maps to Engañoso in messages.py it seems

def test_format_claim_fallback_bullets():
    claim = Claim(
        id=3,
        claim_text="Dudoso",
        status=VerificationStatus.UNVERIFIED,
        confidence=0.5,
        explanation="No estamos seguros. Falta info.",
        key_evidence_points=None, # Should fallback to splitting explanation
        created_at=datetime.utcnow()
    )
    msg = format_claim_for_whatsapp(claim)
    assert "No verificable aún" in msg
    assert "No estamos seguros" in msg
