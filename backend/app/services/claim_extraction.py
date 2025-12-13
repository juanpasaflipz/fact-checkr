from datetime import datetime
from typing import List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

class ClaimExtractionService:
    def __init__(self, anthropic_client: Any = None, openai_client: Any = None):
        self.anthropic_client = anthropic_client
        self.openai_client = openai_client

    async def extract_claim(self, content: str) -> str:
        if not self.anthropic_client and not self.openai_client:
            return content  # Fallback to original content
        
        current_date = datetime.now().strftime("%B %d, %Y")
        system_prompt = f"""You are a data analyst processing Mexican political social media streams.
Current Date: {current_date}.
President of Mexico: Claudia Sheinbaum.

Your task is to extract ONLY factual claims that can be verified. Ignore opinions, insults, hashtags, and vague complaints."""
        
        user_prompt = f"""INPUT TEXT: "{content}"

INSTRUCTIONS:
1. Ignore insults, hashtags, opinions, or vague complaints (e.g., "Morena ruined everything").
2. Extract the specific *factual claim* that can be proven or disproven.
3. If the text is pure opinion or satire with no factual basis, return "SKIP".
4. Translate the claim to neutral, formal Spanish.

OUTPUT FORMAT (String only):
[The Claim] OR "SKIP"""
        
        # Try Anthropic first (primary)
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=150,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                claim = response.content[0].text.strip()
                # Handle SKIP with or without quotes
                if claim.replace('"', '').replace("'", "").strip() == "SKIP":
                    return "SKIP"
                return claim
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
                    max_tokens=150,
                    temperature=0.3
                )
                claim = response.choices[0].message.content.strip()
                # Handle SKIP with or without quotes
                if claim.replace('"', '').replace("'", "").strip() == "SKIP":
                    return "SKIP"
                return claim
            except Exception as e:
                logger.warning(f"⚠️  OpenAI API error: {e}")
        
        # If both fail, return original content
        return content

    async def extract_entities(self, claim_text: str) -> List[tuple]:
        """Extract entities (people, institutions, locations) from claim text"""
        if not self.anthropic_client and not self.openai_client:
            return []
        
        system_prompt = """You are an entity extraction system for Mexican political news.
Extract only: politicians, government institutions, political parties, and locations.
Return a JSON array of [name, type] pairs where type is "person", "institution", or "location"."""
        
        user_prompt = f"""Extract entities from this claim: "{claim_text}"

Return JSON format:
[["Entity Name", "person|institution|location"], ...]"""
        
        # Try Anthropic first
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=200,
                    temperature=0.2,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                response_text = response.content[0].text.strip()
                if response_text.startswith("```"):
                    json_start = response_text.find("[")
                    json_end = response_text.rfind("]") + 1
                    if json_start != -1 and json_end > json_start:
                        response_text = response_text[json_start:json_end]
                entities = json.loads(response_text)
                return [(e[0], e[1]) for e in entities if len(e) == 2]
            except Exception as e:
                logger.warning(f"⚠️  Entity extraction error (Anthropic): {e}")
        
        # Fallback to OpenAI
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=200,
                    temperature=0.2
                )
                response_text = response.choices[0].message.content.strip()
                # Extract JSON from markdown code block if present
                if response_text.startswith("```"):
                    json_start = response_text.find("[")
                    json_end = response_text.rfind("]") + 1
                    if json_start != -1 and json_end > json_start:
                        response_text = response_text[json_start:json_end]
                entities = json.loads(response_text)
                return [(e[0], e[1]) for e in entities if len(e) == 2]
            except Exception as e:
                logger.warning(f"⚠️  Entity extraction error (OpenAI): {e}")
        
        return []

    async def extract_topics(self, claim_text: str, available_topics: List[dict] = None) -> List[str]:
        """Extract topics from claim text. Returns list of topic names that match database topics."""
        if not self.anthropic_client and not self.openai_client:
            return []
        
        # Build topics list for prompt
        if available_topics:
            topics_list = "\n".join([f"- {t['name']}" for t in available_topics])
        else:
            # Default topics if none provided
            topics_list = """- Reforma Judicial
- Ejecutivo
- Legislativo
- Economía
- Seguridad
- Salud
- Educación
- Infraestructura
- Medio Ambiente
- Derechos Humanos
- Corrupción
- Relaciones Internacionales
- Energía
- Migración
- Tecnología"""
        
        system_prompt = """You are a topic classification system for Mexican political news.
Classify claims into relevant topics based on Mexican political and social context.
Return only topic names that match the provided list. If multiple topics apply, return all relevant ones."""
        
        user_prompt = f"""CLAIM: "{claim_text}"

AVAILABLE TOPICS:
{topics_list}

INSTRUCTIONS:
1. Classify this claim into 1-3 most relevant topics from the list above.
2. Return only topic names that exactly match the list (case-sensitive).
3. If no topic fits perfectly, choose the closest match.
4. Consider the main subject: Executive actions, Legislative bills, Judicial reforms, Economy, Security, Health, Education, Infrastructure, etc.

RESPONSE FORMAT (JSON only, no markdown):
{{
    "topics": ["Topic Name 1", "Topic Name 2"]
}}"""
        
        # Try Anthropic first
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=200,
                    temperature=0.2,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                response_text = response.content[0].text.strip()
                
                # Extract JSON from markdown code block if present
                if response_text.startswith("```"):
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    if json_start != -1 and json_end > json_start:
                        response_text = response_text[json_start:json_end]
                
                result = json.loads(response_text)
                topics = result.get("topics", [])
                # Ensure topics are strings and filter empty
                return [str(t).strip() for t in topics if t and str(t).strip()]
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️  Topic extraction JSON parse error (Anthropic): {e}")
            except Exception as e:
                logger.warning(f"⚠️  Topic extraction error (Anthropic): {e}")
        
        # Fallback to OpenAI
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=200,
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                response_text = response.choices[0].message.content.strip()
                
                # Extract JSON from markdown code block if present
                if response_text.startswith("```"):
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    if json_start != -1 and json_end > json_start:
                        response_text = response_text[json_start:json_end]
                
                result = json.loads(response_text)
                topics = result.get("topics", [])
                # Ensure topics are strings and filter empty
                return [str(t).strip() for t in topics if t and str(t).strip()]
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️  Topic extraction JSON parse error (OpenAI): {e}")
            except Exception as e:
                logger.warning(f"⚠️  Topic extraction error (OpenAI): {e}")
        
        return []
