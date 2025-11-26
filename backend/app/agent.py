import os
from typing import List
from app.models import Claim, VerificationResult, VerificationStatus
from datetime import datetime

# Source filtering configuration
WHITELIST_SOURCES = [
    "animalpolitico.com",
    "aristeguinoticias.com",
    "eluniversal.com.mx",
    "proceso.com.mx",
    "reforma.com",
    "ine.mx",
    "banxico.org.mx",
    "dof.gob.mx"
]

BLACKLIST_SOURCES = [
    "deforma.com",  # Satire
    # "youtube.com",  # Now supported via YouTube scraper with transcription
    "tiktok.com",   # Hard to parse video content
]
from app.scraper import MockScraper, TwitterScraper, GoogleNewsScraper
import anthropic
import openai
import json
import asyncio

async def search_web(query: str) -> List[str]:
    """Search the web using Serper API for evidence gathering"""
    serper_api_key = os.getenv("SERPER_API_KEY")
    
    if not serper_api_key:
        print(f"Warning: SERPER_API_KEY not found. Using mock results for: {query}")
        return [
            "https://www.animalpolitico.com/verificacion-reforma-judicial",
            "https://www.eluniversal.com.mx/nacion/sheinbaum-metro"
        ]
    
    try:
        import httpx
        
        # Serper API endpoint
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
        }
        
        # Search query optimized for Mexican news sources
        payload = {
            "q": f"{query} site:mx OR site:com.mx",
            "num": 10,  # Get top 10 results
            "gl": "mx",  # Country: Mexico
            "hl": "es",  # Language: Spanish
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract URLs from search results
            urls = []
            if "organic" in data:
                for result in data["organic"]:
                    if "link" in result:
                        urls.append(result["link"])
            
            print(f"Serper API found {len(urls)} results for: {query}")
            return urls[:10]  # Return top 10 URLs
            
    except Exception as e:
        print(f"Error using Serper API: {e}. Falling back to mock results.")
        # Fallback to mock results on error
        return [
            "https://www.animalpolitico.com/verificacion-reforma-judicial",
            "https://www.eluniversal.com.mx/nacion/sheinbaum-metro"
        ]

class FactChecker:
    def __init__(self):
        self.mock_scraper = MockScraper()
        self.twitter_scraper = TwitterScraper()
        self.google_news_scraper = GoogleNewsScraper()
        
        # Initialize Anthropic (primary)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                print("✓ Anthropic API initialized (primary)")
            except Exception as e:
                print(f"Warning: Failed to initialize Anthropic client: {e}")
                self.anthropic_client = None
        else:
            self.anthropic_client = None
            print("Warning: Anthropic API key not found.")
        
        # Initialize OpenAI (backup)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                print("✓ OpenAI API initialized (backup)")
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
                self.openai_client = None
        else:
            self.openai_client = None
            print("Warning: OpenAI API key not found.")
        
        # Check if at least one client is available
        if not self.anthropic_client and not self.openai_client:
            print("⚠️  No AI API keys found. Fact-checking will use mock logic.")
    
    def _filter_sources(self, sources: List[str]) -> List[str]:
        """Filter sources based on whitelist/blacklist"""
        filtered = []
        for url in sources:
            # Check blacklist first
            if any(blocked in url.lower() for blocked in BLACKLIST_SOURCES):
                continue
            # Prioritize whitelist
            if any(trusted in url.lower() for trusted in WHITELIST_SOURCES):
                filtered.insert(0, url)  # Put whitelisted sources first
            else:
                filtered.append(url)
        return filtered[:5]  # Limit to top 5 sources
        
    async def process_recent_posts(self, keywords: List[str] = None) -> List[Claim]:
        if not keywords:
            keywords = ["Reforma Judicial", "Sheinbaum"]
        
        # Fetch from all sources concurrently
        results = await asyncio.gather(
            self.twitter_scraper.fetch_posts(keywords),
            self.google_news_scraper.fetch_posts(keywords),
            return_exceptions=True
        )
        
        twitter_posts = results[0] if isinstance(results[0], list) else []
        google_posts = results[1] if isinstance(results[1], list) else []
        
        all_posts = twitter_posts + google_posts
        
        if not all_posts:
            print("No live posts found (or keys missing). Using Mock data.")
            all_posts = await self.mock_scraper.fetch_posts(keywords)
            
        claims = []
        
        # Limit to first 1 post for instant response
        for post in all_posts[:1]:
            # 1. Extract Claim
            claim_text = await self._extract_claim(post.content)
            if claim_text == "SKIP":
                continue  # Skip non-factual content
            
            # 2. Search for Evidence
            evidence_links = await search_web(claim_text)
            filtered_evidence = self._filter_sources(evidence_links)
            
            # 3. Verify Claim
            verification = await self._verify_claim(claim_text, filtered_evidence)
            
            claims.append(Claim(
                id=post.id,
                original_text=post.content,
                claim_text=claim_text,
                verification=verification,
                source_post=post
            ))
            
        return claims
    
    async def process_recent_posts_streaming(self, keywords: List[str] = None):
        """Stream claims as they're processed (generator)"""
        if not keywords:
            keywords = ["Reforma Judicial", "Sheinbaum"]
        
        # Fetch from all sources concurrently
        results = await asyncio.gather(
            self.twitter_scraper.fetch_posts(keywords),
            self.google_news_scraper.fetch_posts(keywords),
            return_exceptions=True
        )
        
        twitter_posts = results[0] if isinstance(results[0], list) else []
        google_posts = results[1] if isinstance(results[1], list) else []
        
        all_posts = twitter_posts + google_posts
        
        if not all_posts:
            print("No live posts found (or keys missing). Using Mock data.")
            all_posts = await self.mock_scraper.fetch_posts(keywords)
        
        # Yield claims as they're processed
        for post in all_posts[:3]:
            claim_text = await self._extract_claim(post.content)
            if claim_text == "SKIP":
                continue
            
            evidence_links = await search_web(claim_text)
            filtered_evidence = self._filter_sources(evidence_links)
            verification = await self._verify_claim(claim_text, filtered_evidence)
            
            claim = Claim(
                id=post.id,
                original_text=post.content,
                claim_text=claim_text,
                verification=verification,
                source_post=post
            )
            
            yield claim  # Yield each claim as it's ready

    async def _extract_claim(self, content: str) -> str:
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
                    model="claude-sonnet-3-5-20241022",
                    max_tokens=150,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                claim = response.content[0].text.strip()
                return claim if claim != "SKIP" else "SKIP"
            except Exception as e:
                print(f"⚠️  Anthropic API error, falling back to OpenAI: {e}")
        
        # Fallback to OpenAI
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=150,
                    temperature=0.3
                )
                claim = response.choices[0].message.content.strip()
                return claim if claim != "SKIP" else "SKIP"
            except Exception as e:
                print(f"⚠️  OpenAI API error: {e}")
        
        # If both fail, return original content
        return content

    async def _verify_claim(self, claim: str, evidence: List[str]) -> VerificationResult:
        if not self.anthropic_client and not self.openai_client:
            # Fallback to mock logic if no API keys
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
        
        # Try Anthropic first (primary)
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-sonnet-3-5-20241022",
                    max_tokens=300,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                
                # Extract text from Anthropic response
                response_text = response.content[0].text.strip()
                
                # Try to parse JSON - handle cases where response might have markdown code blocks
                if response_text.startswith("```"):
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    if json_start != -1 and json_end > json_start:
                        response_text = response_text[json_start:json_end]
                
                result = json.loads(response_text)
                status_map = {
                    "Verified": VerificationStatus.VERIFIED,
                    "Debunked": VerificationStatus.DEBUNKED,
                    "Misleading": VerificationStatus.MISLEADING,
                    "Unverified": VerificationStatus.UNVERIFIED
                }
                
                return VerificationResult(
                    status=status_map.get(result.get("status"), VerificationStatus.UNVERIFIED),
                    explanation=result.get("explanation", "No se pudo verificar la información."),
                    sources=evidence
                )
            except json.JSONDecodeError as e:
                print(f"⚠️  Anthropic JSON parse error, falling back to OpenAI: {e}")
            except Exception as e:
                print(f"⚠️  Anthropic API error, falling back to OpenAI: {e}")
        
        # Fallback to OpenAI
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=300,
                    temperature=0.3,
                    response_format={"type": "json_object"}  # Request JSON format
                )
                
                response_text = response.choices[0].message.content.strip()
                
                # Handle markdown code blocks if present
                if response_text.startswith("```"):
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    if json_start != -1 and json_end > json_start:
                        response_text = response_text[json_start:json_end]
                
                result = json.loads(response_text)
                status_map = {
                    "Verified": VerificationStatus.VERIFIED,
                    "Debunked": VerificationStatus.DEBUNKED,
                    "Misleading": VerificationStatus.MISLEADING,
                    "Unverified": VerificationStatus.UNVERIFIED
                }
                
                return VerificationResult(
                    status=status_map.get(result.get("status"), VerificationStatus.UNVERIFIED),
                    explanation=result.get("explanation", "No se pudo verificar la información."),
                    sources=evidence
                )
            except json.JSONDecodeError as e:
                print(f"⚠️  OpenAI JSON parse error: {e}")
                print(f"Response was: {response.choices[0].message.content if hasattr(response, 'choices') else 'No response'}")
            except Exception as e:
                print(f"⚠️  OpenAI API error: {e}")
        
        # If both fail, return unverified
        return VerificationResult(
            status=VerificationStatus.UNVERIFIED,
            explanation="Error al verificar la información. No se pudo conectar con los servicios de verificación.",
            sources=evidence
        )
    
    async def _extract_entities(self, claim_text: str) -> List[tuple]:
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
                    model="claude-sonnet-3-5-20241022",
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
                print(f"⚠️  Entity extraction error (Anthropic): {e}")
        
        # Fallback to OpenAI
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
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
                print(f"⚠️  Entity extraction error (OpenAI): {e}")
        
        return []
    
    async def _extract_topics(self, claim_text: str, available_topics: List[dict] = None) -> List[str]:
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
                    model="claude-sonnet-3-5-20241022",
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
                print(f"⚠️  Topic extraction JSON parse error (Anthropic): {e}")
            except Exception as e:
                print(f"⚠️  Topic extraction error (Anthropic): {e}")
        
        # Fallback to OpenAI
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
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
                print(f"⚠️  Topic extraction JSON parse error (OpenAI): {e}")
            except Exception as e:
                print(f"⚠️  Topic extraction error (OpenAI): {e}")
        
        return []