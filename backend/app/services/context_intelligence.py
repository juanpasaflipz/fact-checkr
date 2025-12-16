"""
Context Intelligence Service

Assesses relevance of topics to Mexican political, economic, and social context.
Filters noise and prioritizes topics that matter.
"""
from app.core.config import settings
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import anthropic
import json

from app.database.connection import SessionLocal
from app.database.models import ContextIntelligence

logger = logging.getLogger(__name__)


class ContextIntelligenceService:
    """Assesses topic relevance to Mexican context"""
    
    def __init__(self):
        api_key = settings.ANTHROPIC_API_KEY
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = None
            logger.warning("ANTHROPIC_API_KEY not found. Context intelligence will be limited.")
        
        self.model = "claude-sonnet-4-20250514"
        
        # Mexican context indicators
        self.political_indicators = [
            "elecciones", "votación", "campaña", "partido político",
            "gobierno", "presidente", "congreso", "senado", "diputados",
            "reforma", "ley", "iniciativa", "decreto", "INE", "TEPJF"
        ]
        
        self.economic_indicators = [
            "inflación", "PIB", "economía", "presupuesto", "deuda",
            "Banxico", "peso", "dólar", "empleo", "desempleo",
            "salario", "pobreza", "crecimiento económico"
        ]
        
        self.social_indicators = [
            "seguridad", "violencia", "migración", "educación",
            "salud", "corrupción", "derechos humanos", "justicia",
            "desigualdad", "protesta", "manifestación"
        ]
    
    async def assess_topic_relevance(
        self,
        topic_name: str,
        topic_keywords: List[str],
        sample_content: List[str] = None
    ) -> Dict:
        """Assess relevance of a topic to Mexican context
        
        Args:
            topic_name: Name of the topic
            topic_keywords: Keywords associated with topic
            sample_content: Sample content from sources (optional)
        
        Returns:
            Dictionary with context assessment
        """
        # Check cache first
        topic_key = self._normalize_topic_key(topic_name, topic_keywords)
        cached = self._get_cached_intelligence(topic_key)
        
        if cached and (datetime.utcnow() - cached.last_updated) < timedelta(hours=24):
            logger.info(f"Using cached context intelligence for: {topic_name}")
            return {
                'political_context': cached.political_context,
                'economic_context': cached.economic_context,
                'social_context': cached.social_context,
                'relevance_score': cached.relevance_score,
                'noise_filter_score': cached.noise_filter_score,
                'from_cache': True
            }
        
        # If no API key, return default assessment
        if not self.client:
            return {
                'political_context': {'relevant': False, 'indicators': []},
                'economic_context': {'relevant': False, 'indicators': []},
                'social_context': {'relevant': False, 'indicators': []},
                'relevance_score': 0.5,
                'noise_filter_score': 0.5,
                'from_cache': False,
                'should_fact_check': True
            }
        
        # Build context assessment prompt
        prompt = self._build_assessment_prompt(
            topic_name, topic_keywords, sample_content
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            result_text = response.content[0].text
            
            # Try to parse JSON from response
            # Sometimes Claude wraps JSON in markdown code blocks
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            
            assessment = json.loads(result_text)
            
            # Cache the result
            self._cache_intelligence(topic_key, assessment)
            
            return {
                **assessment,
                'from_cache': False
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {e}")
            logger.debug(f"Response text: {result_text[:500]}")
            # Return default assessment
            return {
                'political_context': {'relevant': False, 'indicators': []},
                'economic_context': {'relevant': False, 'indicators': []},
                'social_context': {'relevant': False, 'indicators': []},
                'relevance_score': 0.5,
                'noise_filter_score': 0.5,
                'from_cache': False,
                'should_fact_check': True
            }
        except Exception as e:
            logger.error(f"Error assessing topic relevance: {e}", exc_info=True)
            # Return default assessment
            return {
                'political_context': {'relevant': False, 'indicators': []},
                'economic_context': {'relevant': False, 'indicators': []},
                'social_context': {'relevant': False, 'indicators': []},
                'relevance_score': 0.5,
                'noise_filter_score': 0.5,
                'from_cache': False,
                'should_fact_check': True
            }
    
    def _build_assessment_prompt(
        self,
        topic_name: str,
        topic_keywords: List[str],
        sample_content: List[str] = None
    ) -> str:
        """Build prompt for context assessment"""
        
        content_samples = ""
        if sample_content:
            content_samples = "\n\nSample Content:\n" + "\n---\n".join(
                sample_content[:3]  # First 3 samples
            )
        
        return f"""Eres un analista experto en política, economía y sociedad mexicana.

Analiza la relevancia de este tema en el contexto mexicano:

Tema: {topic_name}
Palabras clave: {', '.join(topic_keywords)}
{content_samples}

Evalúa:

1. CONTEXTO POLÍTICO:
   - ¿Es relevante para la política mexicana?
   - ¿Menciona instituciones, partidos, políticos, procesos electorales?
   - ¿Afecta la gobernabilidad o las instituciones?

2. CONTEXTO ECONÓMICO:
   - ¿Tiene implicaciones económicas?
   - ¿Menciona indicadores económicos, políticas fiscales, instituciones financieras?
   - ¿Afecta la economía mexicana?

3. CONTEXTO SOCIAL:
   - ¿Tiene impacto social?
   - ¿Menciona problemas sociales, derechos, seguridad, migración?
   - ¿Afecta a la sociedad mexicana?

4. FILTRO DE RUIDO:
   - ¿Es ruido (contenido viral pero irrelevante)?
   - ¿Es un tema importante aunque no sea viral?
   - ¿Merece fact-checking?

Retorna SOLO JSON válido (sin markdown, sin explicaciones adicionales):
{{
    "political_context": {{
        "relevant": true/false,
        "indicators": ["lista de indicadores encontrados"],
        "relevance_explanation": "explicación breve"
    }},
    "economic_context": {{
        "relevant": true/false,
        "indicators": ["lista de indicadores"],
        "relevance_explanation": "explicación breve"
    }},
    "social_context": {{
        "relevant": true/false,
        "indicators": ["lista de indicadores"],
        "relevance_explanation": "explicación breve"
    }},
    "relevance_score": 0.0-1.0,
    "noise_filter_score": 0.0-1.0,
    "should_fact_check": true/false,
    "reasoning": "razón breve para fact-check o no"
}}"""
    
    def _normalize_topic_key(self, topic_name: str, keywords: List[str]) -> str:
        """Create normalized key for caching"""
        # Use first keyword + topic name
        key_parts = [topic_name.lower()]
        if keywords:
            key_parts.append(keywords[0].lower())
        return "_".join(key_parts[:2])
    
    def _get_cached_intelligence(self, topic_key: str) -> Optional[ContextIntelligence]:
        """Get cached context intelligence"""
        db = SessionLocal()
        try:
            return db.query(ContextIntelligence).filter(
                ContextIntelligence.topic_key == topic_key
            ).first()
        finally:
            db.close()
    
    def _cache_intelligence(self, topic_key: str, assessment: Dict):
        """Cache context intelligence"""
        db = SessionLocal()
        try:
            existing = db.query(ContextIntelligence).filter(
                ContextIntelligence.topic_key == topic_key
            ).first()
            
            if existing:
                existing.political_context = assessment.get('political_context')
                existing.economic_context = assessment.get('economic_context')
                existing.social_context = assessment.get('social_context')
                existing.relevance_score = assessment.get('relevance_score', 0.5)
                existing.noise_filter_score = assessment.get('noise_filter_score', 0.5)
                existing.last_updated = datetime.utcnow()
            else:
                new_cache = ContextIntelligence(
                    topic_key=topic_key,
                    political_context=assessment.get('political_context'),
                    economic_context=assessment.get('economic_context'),
                    social_context=assessment.get('social_context'),
                    relevance_score=assessment.get('relevance_score', 0.5),
                    noise_filter_score=assessment.get('noise_filter_score', 0.5)
                )
                db.add(new_cache)
            
            db.commit()
        except Exception as e:
            logger.error(f"Error caching intelligence: {e}")
            db.rollback()
        finally:
            db.close()

