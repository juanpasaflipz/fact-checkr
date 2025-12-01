"""
RAG (Retrieval-Augmented Generation) Pipeline for Fact-Checking

This pipeline builds rich context for claim verification by:
1. Finding similar past claims (semantic search)
2. Retrieving known facts about entities
3. Searching for web evidence
4. Fetching content from evidence sources
"""
import os
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import logging

from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline for fact-checking context"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        
        # Mexican news source credibility tiers
        self.trusted_sources = {
            "tier1": [  # Highest credibility
                "animalpolitico.com",
                "verificado.mx",
                "ine.mx",
                "banxico.org.mx",
                "dof.gob.mx",
                "inegi.org.mx",
            ],
            "tier2": [  # High credibility
                "eluniversal.com.mx",
                "reforma.com",
                "proceso.com.mx",
                "aristeguinoticias.com",
                "expansion.mx",
                "forbes.com.mx",
            ],
            "tier3": [  # Medium credibility
                "milenio.com",
                "excelsior.com.mx",
                "jornada.com.mx",
                "elfinanciero.com.mx",
            ]
        }
        
        self.blacklisted_sources = [
            "deforma.com",  # Satire
            "elchiguire.com",  # Satire
        ]
    
    async def build_verification_context(
        self,
        claim_text: str,
        original_text: str = "",
        source_url: str = ""
    ) -> Dict:
        """Build comprehensive context for claim verification
        
        Args:
            claim_text: The extracted factual claim
            original_text: Original post/article text
            source_url: URL of the original source
        
        Returns:
            Dictionary with all retrieved context for agents
        """
        logger.info(f"Building verification context for: {claim_text[:100]}...")
        
        # Run all retrievals in parallel for speed
        similar_claims_task = self._get_similar_claims(claim_text)
        entity_facts_task = self._get_entity_knowledge(claim_text)
        web_evidence_task = self._search_web_evidence(claim_text)
        source_credibility_task = self._get_source_credibility(source_url)
        
        (
            similar_claims,
            entity_facts,
            web_evidence,
            source_credibility
        ) = await asyncio.gather(
            similar_claims_task,
            entity_facts_task,
            web_evidence_task,
            source_credibility_task,
            return_exceptions=True
        )
        
        # Handle any errors gracefully
        if isinstance(similar_claims, Exception):
            logger.error(f"Similar claims retrieval failed: {similar_claims}")
            similar_claims = []
        if isinstance(entity_facts, Exception):
            logger.error(f"Entity facts retrieval failed: {entity_facts}")
            entity_facts = []
        if isinstance(web_evidence, Exception):
            logger.error(f"Web evidence retrieval failed: {web_evidence}")
            web_evidence = []
        if isinstance(source_credibility, Exception):
            logger.error(f"Source credibility check failed: {source_credibility}")
            source_credibility = {}
        
        # Fetch full content from top evidence sources
        evidence_urls = [e["url"] for e in web_evidence[:5]]
        evidence_texts = await self._fetch_evidence_content(evidence_urls)
        
        # Build final context object
        context = {
            "claim_text": claim_text,
            "original_text": original_text[:1000] if original_text else "",
            "source_url": source_url,
            "source_credibility": source_credibility,
            "similar_claims": similar_claims,
            "entity_facts": entity_facts,
            "web_evidence": web_evidence,
            "evidence_texts": evidence_texts,
            "evidence_urls": evidence_urls,
            "has_prior_debunked": any(
                c.get("status") == "Debunked" 
                for c in similar_claims 
                if c.get("similarity", 0) > 0.85
            ),
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Context built: {len(similar_claims)} similar claims, "
            f"{len(entity_facts)} entity facts, {len(web_evidence)} web sources"
        )
        
        return context
    
    async def _get_similar_claims(
        self,
        claim_text: str,
        limit: int = 10
    ) -> List[Dict]:
        """Find similar past claims using semantic search"""
        return await self.embedding_service.find_similar_claims(
            query_text=claim_text,
            limit=limit,
            threshold=0.7
        )
    
    async def _get_entity_knowledge(
        self,
        claim_text: str
    ) -> List[str]:
        """Get known facts about entities mentioned in the claim"""
        from app.database.connection import SessionLocal
        from app.database.models import Entity
        
        db = SessionLocal()
        try:
            # Get all entities
            entities = db.query(Entity).all()
            relevant_facts = []
            
            # Check which entities are mentioned
            claim_lower = claim_text.lower()
            for entity in entities:
                # Check main name and aliases
                names_to_check = [entity.name.lower()]
                if hasattr(entity, 'aliases') and entity.aliases:
                    names_to_check.extend([a.lower() for a in entity.aliases])
                
                if any(name in claim_lower for name in names_to_check):
                    # Get verified facts about this entity
                    try:
                        facts = db.execute("""
                            SELECT fact_text, confidence, fact_type
                            FROM entity_knowledge
                            WHERE entity_id = :entity_id
                            AND confidence > 0.7
                            ORDER BY confidence DESC, verified_at DESC
                            LIMIT 5
                        """, {"entity_id": entity.id}).fetchall()
                        
                        for fact in facts:
                            fact_str = f"[{entity.name}] {fact.fact_text}"
                            if fact.fact_type:
                                fact_str += f" ({fact.fact_type})"
                            relevant_facts.append(fact_str)
                    except Exception as e:
                        # Table might not exist yet
                        logger.debug(f"Could not fetch entity knowledge: {e}")
            
            return relevant_facts
        except Exception as e:
            logger.error(f"Error getting entity knowledge: {e}")
            return []
        finally:
            db.close()
    
    async def _search_web_evidence(
        self,
        claim_text: str,
        num_results: int = 15
    ) -> List[Dict]:
        """Search for evidence using Serper API"""
        if not self.serper_api_key:
            logger.warning("Serper API key not found, skipping web search")
            return []
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Search for fact-checks and news
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": self.serper_api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": f"{claim_text} verificación fact-check",
                        "num": num_results,
                        "gl": "mx",  # Mexico
                        "hl": "es"   # Spanish
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("organic", []):
                    url = item.get("link", "")
                    domain = self._extract_domain(url)
                    
                    # Skip blacklisted sources
                    if any(bl in domain for bl in self.blacklisted_sources):
                        continue
                    
                    results.append({
                        "url": url,
                        "domain": domain,
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "credibility_tier": self._get_credibility_tier(domain)
                    })
                
                # Sort by credibility tier
                tier_order = {"tier1": 0, "tier2": 1, "tier3": 2, "unknown": 3}
                results.sort(key=lambda x: tier_order.get(x["credibility_tier"], 3))
                
                return results
                
        except Exception as e:
            logger.error(f"Error searching web evidence: {e}")
            return []
    
    async def _get_source_credibility(
        self,
        source_url: str
    ) -> Dict:
        """Get credibility information for a source"""
        if not source_url:
            return {"tier": "unknown", "score": 0.5}
        
        domain = self._extract_domain(source_url)
        
        # Check against known tiers
        tier = self._get_credibility_tier(domain)
        
        # Check database for historical data
        from app.database.connection import SessionLocal
        db = SessionLocal()
        
        try:
            result = db.execute("""
                SELECT credibility_score, total_claims, verified_count, 
                       debunked_count, bias_indicators
                FROM source_credibility
                WHERE source_domain = :domain
            """, {"domain": domain}).fetchone()
            
            if result:
                return {
                    "domain": domain,
                    "tier": tier,
                    "credibility_score": result.credibility_score,
                    "total_claims": result.total_claims,
                    "verified_count": result.verified_count,
                    "debunked_count": result.debunked_count,
                    "bias_indicators": result.bias_indicators,
                    "from_database": True
                }
            else:
                # Return default based on tier
                tier_scores = {"tier1": 0.9, "tier2": 0.75, "tier3": 0.6, "unknown": 0.5}
                return {
                    "domain": domain,
                    "tier": tier,
                    "credibility_score": tier_scores.get(tier, 0.5),
                    "from_database": False
                }
        except Exception as e:
            logger.debug(f"Could not fetch source credibility: {e}")
            tier_scores = {"tier1": 0.9, "tier2": 0.75, "tier3": 0.6, "unknown": 0.5}
            return {
                "domain": domain,
                "tier": tier,
                "credibility_score": tier_scores.get(tier, 0.5),
                "from_database": False
            }
        finally:
            db.close()
    
    async def _fetch_evidence_content(
        self,
        urls: List[str],
        max_length: int = 3000
    ) -> List[str]:
        """Fetch and extract text content from evidence URLs"""
        
        async def fetch_one(url: str) -> str:
            try:
                async with httpx.AsyncClient(
                    timeout=10.0,
                    follow_redirects=True
                ) as client:
                    response = await client.get(
                        url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (compatible; FactCheckr/1.0)"
                        }
                    )
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove non-content elements
                    for tag in soup(['script', 'style', 'nav', 'footer', 
                                    'header', 'aside', 'advertisement']):
                        tag.decompose()
                    
                    # Try to find main content
                    content = None
                    for selector in ['article', 'main', '.article-body', 
                                    '.post-content', '.entry-content', '.content']:
                        content = soup.select_one(selector)
                        if content:
                            break
                    
                    if not content:
                        content = soup.body
                    
                    if content:
                        text = content.get_text(separator=' ', strip=True)
                        # Clean up whitespace
                        text = ' '.join(text.split())
                        return text[:max_length]
                    
                    return ""
            except Exception as e:
                logger.debug(f"Error fetching {url}: {e}")
                return ""
        
        # Fetch all URLs in parallel
        tasks = [fetch_one(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors and empty results
        return [
            r for r in results 
            if isinstance(r, str) and len(r) > 100
        ]
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    def _get_credibility_tier(self, domain: str) -> str:
        """Get credibility tier for a domain"""
        for tier, domains in self.trusted_sources.items():
            if any(d in domain for d in domains):
                return tier
        return "unknown"


# Quick context builder for real-time verification
async def quick_context(claim_text: str) -> Dict:
    """Build minimal context for fast verification"""
    pipeline = RAGPipeline()
    
    # Only get similar claims and web evidence (skip slower operations)
    similar, evidence = await asyncio.gather(
        pipeline._get_similar_claims(claim_text, limit=5),
        pipeline._search_web_evidence(claim_text, num_results=10)
    )
    
    return {
        "claim_text": claim_text,
        "similar_claims": similar,
        "web_evidence": evidence,
        "evidence_urls": [e["url"] for e in evidence[:5]]
    }

