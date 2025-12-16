"""
AI-Powered Market Insights Service

Uses AI to generate insights about prediction markets including:
- Key factors affecting probability
- Historical context
- Risk assessment
- Recommended actions
"""

from sqlalchemy.orm import Session
from app.database.models import Market, MarketTrade, Claim
from app.services.markets import yes_probability, no_probability, calculate_volume
from app.services.market_analytics import get_market_history
from typing import Dict, Optional, Any
import os
import anthropic
import openai
import json
from app.core.config import settings


def get_ai_client():
    """Get available AI client (Anthropic preferred, OpenAI as backup)"""
    anthropic_key = settings.ANTHROPIC_API_KEY
    if anthropic_key:
        try:
            return anthropic.Anthropic(api_key=anthropic_key), "anthropic"
        except Exception:
            pass
    
    openai_key = settings.OPENAI_API_KEY
    if openai_key:
        try:
            return openai.OpenAI(api_key=openai_key), "openai"
        except Exception:
            pass
    
    return None, None


def generate_market_insights(market_id: int, db: Session) -> Dict[str, Any]:
    """
    Generate AI-powered insights about a market.
    
    Args:
        market_id: Market ID
        db: Database session
        
    Returns:
        Dictionary with insights including key_factors, historical_context, risk_assessment, recommendation
    """
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise ValueError("Market not found")
    
    # Get market context
    current_prob = yes_probability(market)
    volume = calculate_volume(market, db)
    
    # Get recent history
    history = get_market_history(market_id, 7, db)  # Last 7 days
    
    # Get related claim if available
    related_claim = None
    if market.claim_id:
        related_claim = db.query(Claim).filter(Claim.id == market.claim_id).first()
    
    # Get trade statistics
    trades = db.query(MarketTrade).filter(MarketTrade.market_id == market_id).all()
    total_trades = len(trades)
    yes_trades = sum(1 for t in trades if t.outcome == "yes")
    no_trades = sum(1 for t in trades if t.outcome == "no")
    
    # Build context for AI
    context = {
        "question": market.question,
        "description": market.description or "",
        "category": market.category or "general",
        "current_probability": {
            "yes": current_prob,
            "no": 1 - current_prob
        },
        "volume": volume,
        "total_trades": total_trades,
        "yes_trades": yes_trades,
        "no_trades": no_trades,
        "resolution_criteria": market.resolution_criteria or "",
        "related_claim": related_claim.claim_text if related_claim else None,
        "recent_trend": _analyze_trend(history) if history else None
    }
    
    # Generate insights using AI
    client, client_type = get_ai_client()
    
    if not client:
        # Fallback to basic insights if no AI available
        return _generate_basic_insights(context)
    
    try:
        if client_type == "anthropic":
            return _generate_insights_anthropic(client, context)
        else:
            return _generate_insights_openai(client, context)
    except Exception as e:
        # Fallback on error
        return _generate_basic_insights(context)


def _analyze_trend(history: list) -> str:
    """Analyze probability trend from history"""
    if len(history) < 2:
        return "insufficient_data"
    
    first_prob = history[0].get("yes_probability", 0.5)
    last_prob = history[-1].get("yes_probability", 0.5)
    
    change = last_prob - first_prob
    
    if abs(change) < 0.05:
        return "stable"
    elif change > 0.1:
        return "strong_uptrend"
    elif change > 0.05:
        return "uptrend"
    elif change < -0.1:
        return "strong_downtrend"
    else:
        return "downtrend"


def _generate_insights_anthropic(client, context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate insights using Anthropic Claude"""
    prompt = f"""Analiza este mercado de predicción sobre política mexicana y proporciona insights profesionales.

MERCADO:
Pregunta: {context['question']}
Descripción: {context['description']}
Categoría: {context['category']}

ESTADO ACTUAL:
- Probabilidad SÍ: {context['current_probability']['yes']:.1%}
- Probabilidad NO: {context['current_probability']['no']:.1%}
- Volumen: {context['volume']:.2f} créditos
- Total de operaciones: {context['total_trades']}
- Operaciones SÍ: {context['yes_trades']}
- Operaciones NO: {context['no_trades']}

TENDENCIA: {context.get('recent_trend', 'N/A')}

CRITERIOS DE RESOLUCIÓN: {context['resolution_criteria']}

Proporciona un análisis estructurado en JSON con:
1. key_factors: Lista de factores clave que afectan la probabilidad
2. historical_context: Contexto histórico relevante sobre el tema
3. risk_assessment: Evaluación de riesgos (alto/medio/bajo) y razones
4. recommendation: Recomendación de acción (comprar_si, comprar_no, esperar, evitar)

Responde SOLO con JSON válido, sin texto adicional."""

    response = client.messages.create(
        model="claude-sonnet-3-5-20241022",
        max_tokens=1000,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        insights_text = response.content[0].text.strip()
        # Remove markdown code blocks if present
        if insights_text.startswith("```"):
            insights_text = insights_text.split("```")[1]
            if insights_text.startswith("json"):
                insights_text = insights_text[4:]
        insights = json.loads(insights_text)
        return insights
    except json.JSONDecodeError:
        return _generate_basic_insights(context)


def _generate_insights_openai(client, context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate insights using OpenAI"""
    prompt = f"""Analiza este mercado de predicción sobre política mexicana y proporciona insights profesionales.

MERCADO:
Pregunta: {context['question']}
Descripción: {context['description']}
Categoría: {context['category']}

ESTADO ACTUAL:
- Probabilidad SÍ: {context['current_probability']['yes']:.1%}
- Probabilidad NO: {context['current_probability']['no']:.1%}
- Volumen: {context['volume']:.2f} créditos
- Total de operaciones: {context['total_trades']}

Proporciona un análisis estructurado en JSON con:
1. key_factors: Lista de factores clave
2. historical_context: Contexto histórico
3. risk_assessment: Evaluación de riesgos
4. recommendation: Recomendación (comprar_si, comprar_no, esperar, evitar)

Responde SOLO con JSON válido."""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000
    )
    
    try:
        insights_text = response.choices[0].message.content.strip()
        if insights_text.startswith("```"):
            insights_text = insights_text.split("```")[1]
            if insights_text.startswith("json"):
                insights_text = insights_text[4:]
        insights = json.loads(insights_text)
        return insights
    except (json.JSONDecodeError, AttributeError):
        return _generate_basic_insights(context)


def _generate_basic_insights(context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate basic insights without AI (fallback)"""
    prob = context['current_probability']['yes']
    
    if prob > 0.7:
        recommendation = "comprar_si"
        risk = "medio"
    elif prob < 0.3:
        recommendation = "comprar_no"
        risk = "medio"
    else:
        recommendation = "esperar"
        risk = "alto"
    
    return {
        "key_factors": [
            f"Probabilidad actual: {prob:.1%}",
            f"Volumen de operaciones: {context['volume']:.2f} créditos",
            f"Total de operaciones: {context['total_trades']}"
        ],
        "historical_context": f"Mercado en categoría {context['category']} con {context['total_trades']} operaciones realizadas.",
        "risk_assessment": {
            "level": risk,
            "reasons": [
                "Mercado activo con volumen significativo" if context['volume'] > 1000 else "Volumen bajo, mayor volatilidad esperada"
            ]
        },
        "recommendation": recommendation
    }

