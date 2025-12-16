from datetime import datetime
from typing import List, Optional, Any
import json
import logging
from app.schemas import VerificationResult, VerificationStatus

logger = logging.getLogger(__name__)

class VerificationService:
    def __init__(self, anthropic_client: Any = None, openai_client: Any = None):
        self.anthropic_client = anthropic_client
        self.openai_client = openai_client

    def _call_ai_with_fallback(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> Optional[dict]:
        """
        Helper method to call AI with fallback logic.
        Tries Anthropic first, then OpenAI.
        Returns parsed JSON dict or None if both fail.
        """
        # Try Anthropic first (primary)
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=max_tokens,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                
                response_text = response.content[0].text.strip()
                return self._parse_json_response(response_text)
            except Exception as e:
                logger.warning(f"⚠️  Anthropic API error, falling back to OpenAI: {e}")

        # Fallback to OpenAI
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                
                response_text = response.choices[0].message.content.strip()
                return self._parse_json_response(response_text)
            except Exception as e:
                logger.warning(f"⚠️  OpenAI API error: {e}")
        
        return None

    def _parse_json_response(self, response_text: str) -> dict:
        """Extract and parse JSON from response text"""
        try:
            # Handle markdown code blocks
            if response_text.startswith("```"):
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    response_text = response_text[json_start:json_end]
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            raise e

    async def verify_claim(self, claim: str, evidence: List[str]) -> VerificationResult:
        if not self.anthropic_client and not self.openai_client:
            return VerificationResult(
                status=VerificationStatus.UNVERIFIED,
                explanation="No AI API keys configured.",
                sources=[]
            )
        
        current_date = datetime.now().strftime("%B %d, %Y")
        evidence_text = "\n".join([f"- {url}" for url in evidence]) if evidence else "No evidence sources provided."
        
        system_prompt = f"""You are a neutral, objective Ombudsman for Mexican News. You adhere to the principles of "Verificado MX" and "Animal Político".

Current Date: {current_date}.

You must analyze claims ONLY based on the provided EVIDENCE. Do not use your internal memory for facts unless they are universal constants. Be thorough, objective, and cite specific evidence in your analysis."""
        
        user_prompt = f"""CLAIM TO CHECK: "{claim}"

SEARCH RESULTS (EVIDENCE):
{evidence_text}

INSTRUCTIONS:
1. Analyze the claim solely based on the provided EVIDENCE.
2. If the EVIDENCE is contradictory or insufficient, the verdict must be "Unverified".
3. If the claim comes from a known satire site (like El Deforma), mark as "Unverified" with explanation.
4. "Misleading" applies if the facts are real but the context is manipulated.
5. Be precise and objective in your analysis.

RESPONSE FORMAT (JSON only, no markdown):
{{
    "status": "Verified" | "Debunked" | "Misleading" | "Unverified",
    "explanation": "A concise (max 280 chars) explanation in Mexican Spanish. Tone: informational, not scolding."
}}"""
        
        result = self._call_ai_with_fallback(system_prompt, user_prompt, max_tokens=300)
        
        if result:
            status_map = {
                "Verified": VerificationStatus.VERIFIED,
                "Debunked": VerificationStatus.DEBUNKED,
                "Misleading": VerificationStatus.MISLEADING,
                "Unverified": VerificationStatus.UNVERIFIED
            }
            return VerificationResult(
                status=status_map.get(result.get("status"), VerificationStatus.UNVERIFIED),
                explanation=result.get("explanation", "No se pudo verificar la información."),
                sources=evidence,
                confidence=0.5  # Default confidence for old method
            )
        
        return VerificationResult(
            status=VerificationStatus.UNVERIFIED,
            explanation="Error al verificar la información. No se pudo conectar con los servicios de verificación.",
            sources=evidence,
            confidence=0.0
        )
    
    async def verify_claim_with_evidence(
        self,
        claim: str,
        evidence_urls: List[str],
        evidence_texts: List[str],
        context: dict = None
    ) -> VerificationResult:
        """Enhanced verification with actual evidence content"""
        if not self.anthropic_client and not self.openai_client:
            return VerificationResult(
                status=VerificationStatus.UNVERIFIED,
                explanation="No AI API keys configured.",
                sources=evidence_urls,
                confidence=0.0
            )
        
        # Build evidence summary with actual content
        evidence_summary = []
        for i, (url, text) in enumerate(zip(evidence_urls[:5], evidence_texts[:5])):
            if text and len(text) > 100:
                # Truncate to 2000 chars per source to manage token usage
                evidence_summary.append(
                    f"FUENTE {i+1} ({url}):\n{text[:2000]}...\n"
                )
            elif url:
                # Fallback to URL only if no content
                evidence_summary.append(f"FUENTE {i+1} ({url}): [Contenido no disponible]\n")
        
        if not evidence_summary:
            evidence_summary = [f"- {url}" for url in evidence_urls[:5]]
        
        evidence_text = "\n\n".join(evidence_summary)
        
        # Add context about similar claims if available
        context_info = ""
        if context:
            similar = context.get("similar_claims", [])
            if similar:
                context_info = "\n\nAFIRMACIONES SIMILARES ANTERIORES:\n"
                for sc in similar[:3]:
                    context_info += f"- \"{sc.get('claim_text', '')[:100]}...\" "
                    context_info += f"(Estado: {sc.get('status', 'N/A')}, Similitud: {sc.get('similarity', 0):.2f})\n"
            
            # Add source credibility info
            source_cred = context.get("source_credibility", {})
            if source_cred:
                context_info += f"\nCREDIBILIDAD DE LA FUENTE ORIGINAL:\n"
                context_info += f"- Dominio: {source_cred.get('domain', 'Desconocido')}\n"
                context_info += f"- Tier: {source_cred.get('tier', 'unknown')}\n"
                context_info += f"- Score: {source_cred.get('credibility_score', 0.5):.2f}\n"
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        system_prompt = f"""You are a neutral, objective fact-checker for Mexican News.

Current Date: {current_date}.

You must analyze claims ONLY based on the provided EVIDENCE CONTENT. Be thorough, objective, and cite specific evidence."""
        
        user_prompt = f"""CLAIM TO CHECK: "{claim}"

EVIDENCE CONTENT:
{evidence_text}
{context_info}

INSTRUCTIONS:
1. Analyze the claim based on the ACTUAL EVIDENCE CONTENT provided above.
2. If evidence is contradictory or insufficient, verdict must be "Unverified".
3. "Misleading" applies if facts are real but context is manipulated.
4. Provide a confidence score (0.0-1.0) based on evidence strength.
5. Identify key evidence points that support or refute the claim.

RESPONSE FORMAT (JSON only, no markdown):
{{
    "status": "Verified" | "Debunked" | "Misleading" | "Unverified",
    "explanation": "A concise (max 280 chars) explanation in Mexican Spanish.",
    "confidence": 0.0-1.0,
    "evidence_strength": "strong|moderate|weak|insufficient",
    "key_evidence_points": ["point 1", "point 2"]
}}"""
        
        result = self._call_ai_with_fallback(system_prompt, user_prompt, max_tokens=400)
        
        if result:
            status_map = {
                "Verified": VerificationStatus.VERIFIED,
                "Debunked": VerificationStatus.DEBUNKED,
                "Misleading": VerificationStatus.MISLEADING,
                "Unverified": VerificationStatus.UNVERIFIED
            }
            
            return VerificationResult(
                status=status_map.get(result.get("status"), VerificationStatus.UNVERIFIED),
                explanation=result.get("explanation", "No se pudo verificar."),
                sources=evidence_urls,
                confidence=result.get("confidence", 0.5),
                evidence_strength=result.get("evidence_strength", "insufficient"),
                key_evidence_points=result.get("key_evidence_points", [])
            )
        
        # If both fail, return unverified
        return VerificationResult(
            status=VerificationStatus.UNVERIFIED,
            explanation="Error al verificar la información.",
            sources=evidence_urls,
            confidence=0.0
        )
