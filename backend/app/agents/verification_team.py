"""
Multi-Agent Verification Team

A team of specialized AI agents that analyze claims from different angles:
- Source Credibility Agent: Evaluates source reliability
- Historical Context Agent: Checks against known facts and past claims
- Logical Consistency Agent: Detects fallacies and manipulation
- Evidence Analysis Agent: Deep analysis of evidence documents

The Orchestrator runs agents in parallel and synthesizes their findings
into a final verdict with high confidence.
"""
import asyncio
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.agents.base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class SourceCredibilityAgent(BaseAgent):
    """Evaluates the credibility of sources cited or providing the claim"""
    
    @property
    def name(self) -> str:
        return "SourceCredibilityAgent"
    
    @property
    def description(self) -> str:
        return "Evaluates source reliability and potential bias"
    
    async def analyze(self, claim: str, context: Dict) -> AgentResult:
        try:
            sources = context.get("evidence_urls", [])
            source_credibility = context.get("source_credibility", {})
            web_evidence = context.get("web_evidence", [])
            
            # Build source info for prompt
            source_info = []
            for e in web_evidence[:10]:
                source_info.append(
                    f"- {e.get('url', 'N/A')} (Tier: {e.get('credibility_tier', 'unknown')})"
                )
            
            prompt = f"""Analiza la credibilidad de estas fuentes para verificar una afirmación sobre política mexicana.

AFIRMACIÓN: "{claim}"

FUENTES ENCONTRADAS:
{chr(10).join(source_info) if source_info else 'No se encontraron fuentes'}

INFORMACIÓN DEL ORIGEN:
- Dominio: {source_credibility.get('domain', 'Desconocido')}
- Tier de credibilidad: {source_credibility.get('tier', 'unknown')}
- Score histórico: {source_credibility.get('credibility_score', 'N/A')}

INSTRUCCIONES:
1. Evalúa si las fuentes son confiables para verificar esta afirmación
2. Identifica posibles sesgos políticos
3. Verifica si hay fuentes oficiales (gobierno, INE, etc.)
4. Detecta si hay fuentes de sátira o poco confiables

RESPONDE EN JSON:
{{
    "overall_source_quality": "high|medium|low|insufficient",
    "most_credible_sources": ["lista de URLs más confiables"],
    "concerns": ["lista de preocupaciones sobre las fuentes"],
    "bias_detected": "none|left|right|government|opposition",
    "has_official_sources": true/false,
    "recommendation": "texto breve sobre qué fuentes usar"
}}"""
            
            response = await self._call_llm(
                system_prompt="Eres un analista de medios especializado en fuentes mexicanas de noticias políticas.",
                user_prompt=prompt,
                max_tokens=400
            )
            
            findings = self._parse_json_response(response)
            
            # Calculate confidence based on source quality
            quality_scores = {"high": 0.9, "medium": 0.7, "low": 0.4, "insufficient": 0.2}
            confidence = quality_scores.get(findings.get("overall_source_quality", "low"), 0.5)
            
            return AgentResult(
                agent_name=self.name,
                confidence=confidence,
                findings=json.dumps(findings, ensure_ascii=False),
                sources_used=sources[:5]
            )
            
        except Exception as e:
            logger.error(f"SourceCredibilityAgent error: {e}")
            return AgentResult(
                agent_name=self.name,
                confidence=0.0,
                findings="{}",
                error=str(e)
            )


class HistoricalContextAgent(BaseAgent):
    """Checks claims against historical context and past verifications"""
    
    @property
    def name(self) -> str:
        return "HistoricalContextAgent"
    
    @property
    def description(self) -> str:
        return "Compares against known facts and past claims"
    
    async def analyze(self, claim: str, context: Dict) -> AgentResult:
        try:
            similar_claims = context.get("similar_claims", [])
            entity_facts = context.get("entity_facts", [])
            has_prior_debunked = context.get("has_prior_debunked", False)
            
            # Format similar claims for prompt
            similar_info = []
            for c in similar_claims[:5]:
                similar_info.append(
                    f"- \"{c.get('claim_text', '')[:150]}...\" "
                    f"(Estado: {c.get('status', 'N/A')}, Similitud: {c.get('similarity', 0):.2f})"
                )
            
            prompt = f"""Analiza el contexto histórico de esta afirmación sobre política mexicana.

AFIRMACIÓN ACTUAL: "{claim}"

AFIRMACIONES SIMILARES ANTERIORES:
{chr(10).join(similar_info) if similar_info else 'No se encontraron afirmaciones similares'}

HECHOS CONOCIDOS SOBRE ENTIDADES MENCIONADAS:
{chr(10).join(entity_facts[:10]) if entity_facts else 'No hay hechos registrados'}

ALERTA: {'⚠️ Se encontraron afirmaciones similares DESMENTIDAS anteriormente' if has_prior_debunked else 'No hay alertas previas'}

INSTRUCCIONES:
1. ¿Esta afirmación contradice hechos conocidos?
2. ¿Es repetición de desinformación ya desmentida?
3. ¿Qué contexto histórico es relevante?
4. ¿Hay patrones de desinformación similar?

RESPONDE EN JSON:
{{
    "contradicts_known_facts": true/false,
    "contradicting_facts": ["lista de hechos que contradicen"],
    "is_repeat_misinformation": true/false,
    "historical_context": "contexto relevante en 2-3 oraciones",
    "similar_debunked_patterns": ["patrones identificados"],
    "confidence_in_analysis": 0.0-1.0
}}"""
            
            response = await self._call_llm(
                system_prompt="Eres un historiador político especializado en México contemporáneo.",
                user_prompt=prompt,
                max_tokens=500
            )
            
            findings = self._parse_json_response(response)
            
            # Higher confidence if we have historical data
            base_confidence = findings.get("confidence_in_analysis", 0.5)
            if similar_claims:
                base_confidence = min(base_confidence + 0.2, 1.0)
            if entity_facts:
                base_confidence = min(base_confidence + 0.1, 1.0)
            
            return AgentResult(
                agent_name=self.name,
                confidence=base_confidence,
                findings=json.dumps(findings, ensure_ascii=False),
                sources_used=[c.get("id") for c in similar_claims[:5]]
            )
            
        except Exception as e:
            logger.error(f"HistoricalContextAgent error: {e}")
            return AgentResult(
                agent_name=self.name,
                confidence=0.0,
                findings="{}",
                error=str(e)
            )


class LogicalConsistencyAgent(BaseAgent):
    """Analyzes logical consistency and detects manipulation techniques"""
    
    @property
    def name(self) -> str:
        return "LogicalConsistencyAgent"
    
    @property
    def description(self) -> str:
        return "Detects fallacies and manipulation"
    
    async def analyze(self, claim: str, context: Dict) -> AgentResult:
        try:
            original_text = context.get("original_text", "")
            
            prompt = f"""Analiza la consistencia lógica de esta afirmación.

AFIRMACIÓN: "{claim}"

TEXTO ORIGINAL (si disponible):
"{original_text[:500] if original_text else 'No disponible'}"

INSTRUCCIONES:
1. Identifica falacias lógicas (hombre de paja, ad hominem, falsa dicotomía, etc.)
2. Detecta técnicas de manipulación (cherry-picking, descontextualización, etc.)
3. Separa hechos verificables de opiniones
4. Evalúa si hay manipulación emocional vs argumentación factual

RESPONDE EN JSON:
{{
    "is_logically_consistent": true/false,
    "fallacies_detected": [
        {{"type": "nombre de falacia", "explanation": "explicación breve"}}
    ],
    "manipulation_techniques": ["lista de técnicas detectadas"],
    "factual_claims": ["afirmaciones que SÍ se pueden verificar"],
    "opinion_claims": ["afirmaciones que son opinión"],
    "emotional_manipulation_level": "none|low|medium|high",
    "overall_assessment": "factual|mixed|manipulative"
}}"""
            
            response = await self._call_llm(
                system_prompt="Eres un experto en lógica y retórica, especializado en detectar desinformación.",
                user_prompt=prompt,
                max_tokens=500
            )
            
            findings = self._parse_json_response(response)
            
            # Calculate confidence based on assessment clarity
            assessment = findings.get("overall_assessment", "mixed")
            confidence_map = {"factual": 0.85, "mixed": 0.6, "manipulative": 0.8}
            confidence = confidence_map.get(assessment, 0.5)
            
            return AgentResult(
                agent_name=self.name,
                confidence=confidence,
                findings=json.dumps(findings, ensure_ascii=False),
                sources_used=[]
            )
            
        except Exception as e:
            logger.error(f"LogicalConsistencyAgent error: {e}")
            return AgentResult(
                agent_name=self.name,
                confidence=0.0,
                findings="{}",
                error=str(e)
            )


class EvidenceAnalysisAgent(BaseAgent):
    """Deep analysis of evidence documents"""
    
    @property
    def name(self) -> str:
        return "EvidenceAnalysisAgent"
    
    @property
    def description(self) -> str:
        return "Analyzes evidence strength and relevance"
    
    async def analyze(self, claim: str, context: Dict) -> AgentResult:
        try:
            evidence_texts = context.get("evidence_texts", [])
            evidence_urls = context.get("evidence_urls", [])
            
            # Prepare evidence for analysis
            evidence_summary = []
            for i, text in enumerate(evidence_texts[:3]):
                url = evidence_urls[i] if i < len(evidence_urls) else "Unknown"
                evidence_summary.append(f"FUENTE {i+1} ({url}):\n{text[:1500]}...")
            
            prompt = f"""Analiza la evidencia encontrada para verificar esta afirmación.

AFIRMACIÓN: "{claim}"

EVIDENCIA ENCONTRADA:
{chr(10).join(evidence_summary) if evidence_summary else 'No se encontró evidencia sustancial'}

INSTRUCCIONES:
1. ¿La evidencia apoya o refuta directamente la afirmación?
2. ¿Es evidencia de fuentes primarias o secundarias?
3. ¿Hay inconsistencias entre las fuentes?
4. ¿Qué evidencia adicional se necesitaría?

RESPONDE EN JSON:
{{
    "supports_claim": "yes|no|partial|insufficient",
    "evidence_strength": "strong|moderate|weak|insufficient",
    "key_supporting_points": ["puntos que apoyan"],
    "key_refuting_points": ["puntos que refutan"],
    "source_consistency": "consistent|mixed|contradictory",
    "evidence_gaps": ["qué falta para verificar"],
    "preliminary_verdict": "likely_true|likely_false|unclear",
    "verdict_confidence": 0.0-1.0
}}"""
            
            response = await self._call_llm(
                system_prompt="Eres un periodista de investigación experto en análisis de evidencia.",
                user_prompt=prompt,
                max_tokens=600
            )
            
            findings = self._parse_json_response(response)
            
            confidence = findings.get("verdict_confidence", 0.5)
            
            return AgentResult(
                agent_name=self.name,
                confidence=confidence,
                findings=json.dumps(findings, ensure_ascii=False),
                verdict=findings.get("preliminary_verdict"),
                sources_used=evidence_urls[:5]
            )
            
        except Exception as e:
            logger.error(f"EvidenceAnalysisAgent error: {e}")
            return AgentResult(
                agent_name=self.name,
                confidence=0.0,
                findings="{}",
                error=str(e)
            )


class VerificationOrchestrator:
    """
    Orchestrates the multi-agent verification process.
    
    Runs all agents in parallel and synthesizes their findings
    into a final verdict with confidence scores.
    """
    
    def __init__(self):
        self.agents = [
            SourceCredibilityAgent(),
            HistoricalContextAgent(),
            LogicalConsistencyAgent(),
            EvidenceAnalysisAgent(),
        ]
    
    async def verify_claim(
        self,
        claim: str,
        context: Dict
    ) -> Dict:
        """
        Run all verification agents and synthesize results.
        
        Args:
            claim: The factual claim to verify
            context: Context from RAG pipeline
        
        Returns:
            Complete verification result with agent findings and final verdict
        """
        logger.info(f"Starting multi-agent verification for: {claim[:100]}...")
        start_time = datetime.utcnow()
        
        # Run all agents in parallel
        tasks = [agent.analyze(claim, context) for agent in self.agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        valid_results = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({
                    "agent": self.agents[i].name,
                    "error": str(result)
                })
            elif isinstance(result, AgentResult):
                if result.error:
                    errors.append({
                        "agent": result.agent_name,
                        "error": result.error
                    })
                else:
                    valid_results.append(result)
        
        # Synthesize final verdict
        final_verdict = await self._synthesize_verdict(claim, valid_results)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "claim": claim,
            "agent_results": [
                {
                    "agent": r.agent_name,
                    "confidence": r.confidence,
                    "findings": json.loads(r.findings) if r.findings else {},
                    "verdict": r.verdict,
                    "sources_used": r.sources_used
                }
                for r in valid_results
            ],
            "errors": errors,
            "final_verdict": final_verdict,
            "processing_time_seconds": processing_time,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _synthesize_verdict(
        self,
        claim: str,
        agent_results: List[AgentResult]
    ) -> Dict:
        """
        Final judge synthesizes all agent findings into verdict.
        """
        if not agent_results:
            return {
                "status": "Unverified",
                "confidence": 0.0,
                "explanation": "No se pudieron ejecutar los agentes de verificación.",
                "key_evidence": [],
                "caveats": ["Error en el sistema de verificación"]
            }
        
        # Build findings summary
        findings_parts = []
        for r in agent_results:
            try:
                findings = json.loads(r.findings) if isinstance(r.findings, str) else r.findings
                findings_parts.append(
                    f"**{r.agent_name}** (Confianza: {r.confidence:.2f}):\n"
                    f"{json.dumps(findings, ensure_ascii=False, indent=2)}"
                )
            except:
                findings_parts.append(f"**{r.agent_name}**: {r.findings}")
        
        findings_summary = "\n\n---\n\n".join(findings_parts)
        
        # Calculate weighted average confidence
        avg_confidence = sum(r.confidence for r in agent_results) / len(agent_results)
        
        # Final synthesis prompt
        prompt = f"""Eres el Editor en Jefe de Fact-Checking. Sintetiza los análisis de los agentes y emite el veredicto final.

AFIRMACIÓN: "{claim}"

ANÁLISIS DE AGENTES:
{findings_summary}

REGLAS PARA EL VEREDICTO:
1. "Verified" - Solo si hay evidencia CLARA y CONSISTENTE que confirma
2. "Debunked" - Solo si hay evidencia CLARA de que es FALSO
3. "Misleading" - Si los hechos son reales pero el contexto/interpretación es engañoso
4. "Unverified" - Si la evidencia es insuficiente o contradictoria

PRIORIDADES:
- Si los agentes tienen confianza <0.5 en promedio → Unverified
- Si hay contradicciones significativas entre agentes → Unverified
- Si se detectó manipulación pero hechos parcialmente verdaderos → Misleading
- Ser conservador: ante la duda, Unverified

RESPONDE EN JSON:
{{
    "status": "Verified|Debunked|Misleading|Unverified",
    "confidence": 0.0-1.0,
    "explanation": "Explicación de 2-3 oraciones en español mexicano neutral",
    "key_evidence": ["puntos clave de evidencia"],
    "source_types": ["Gobierno", "Medios", "Académico", "Redes Sociales", "Sátira"],
    "caveats": ["advertencias importantes si las hay"],
    "agent_agreement": "high|medium|low",
    "recommended_action": "publish|review|investigate_more"
}}"""
        
        try:
            # Use the first agent's LLM connection for synthesis
            synthesizer = self.agents[0]
            response = await synthesizer._call_llm(
                system_prompt="Eres el Editor en Jefe de un medio de fact-checking reconocido en México.",
                user_prompt=prompt,
                max_tokens=500,
                temperature=0.1  # Low temperature for consistent verdicts
            )
            
            verdict = synthesizer._parse_json_response(response)
            
            # Adjust confidence based on agent agreement
            if verdict.get("agent_agreement") == "low":
                verdict["confidence"] = min(verdict.get("confidence", 0.5), 0.5)
            
            return verdict
            
        except Exception as e:
            logger.error(f"Verdict synthesis error: {e}")
            return {
                "status": "Unverified",
                "confidence": avg_confidence,
                "explanation": "Error al sintetizar el veredicto. Se requiere revisión manual.",
                "key_evidence": [],
                "caveats": ["Error en síntesis de veredicto"],
                "error": str(e)
            }


# Convenience function for quick verification
async def verify_claim_with_agents(claim: str, context: Dict) -> Dict:
    """Quick verification using multi-agent system"""
    orchestrator = VerificationOrchestrator()
    return await orchestrator.verify_claim(claim, context)

