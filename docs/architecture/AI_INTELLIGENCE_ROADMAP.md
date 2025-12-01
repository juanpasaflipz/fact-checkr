# FactCheckr AI Intelligence Roadmap

## Executive Summary

This document outlines a strategic roadmap to transform FactCheckr from a basic claim verification system into a **powerful AI-driven political intelligence platform** that creates demand from media, politicians, investigators, and researchers.

---

## Current State Analysis

### What You Have

| Component | Implementation | Strength |
|-----------|---------------|----------|
| **Claim Extraction** | Claude/GPT single-shot | ⭐⭐ Basic |
| **Verification** | Search + AI analysis | ⭐⭐ Basic |
| **Entity Extraction** | LLM-based NER | ⭐⭐ Basic |
| **Topic Classification** | LLM classification | ⭐⭐ Basic |
| **Data Sources** | Twitter, Google News, YouTube | ⭐⭐⭐ Good |
| **Storage** | PostgreSQL (Neon) | ⭐⭐⭐ Good |

### Critical Gaps

1. **No Memory/Learning** — System doesn't learn from past verifications
2. **No Semantic Search** — Can't find related claims by meaning
3. **No Contradiction Detection** — Can't identify conflicting claims over time
4. **No Source Credibility Tracking** — All sources treated equally
5. **No Network Analysis** — Can't track how misinformation spreads
6. **No Prediction** — Can't anticipate emerging narratives

---

## Phase 1: Knowledge Foundation (4-6 weeks)

### 1.1 Vector Database for Semantic Memory

Add **pgvector** to your existing Neon PostgreSQL for embeddings.

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Claim embeddings for semantic search
ALTER TABLE claims ADD COLUMN embedding vector(1536);
CREATE INDEX claims_embedding_idx ON claims USING ivfflat (embedding vector_cosine_ops);

-- Entity knowledge base
CREATE TABLE entity_knowledge (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER REFERENCES entities(id),
    fact_text TEXT NOT NULL,
    fact_embedding vector(1536),
    source_claim_id VARCHAR REFERENCES claims(id),
    confidence FLOAT DEFAULT 0.5,
    verified_at TIMESTAMP,
    contradicted_by VARCHAR[] -- Array of claim IDs that contradict this
);

-- Source credibility tracking
CREATE TABLE source_credibility (
    id SERIAL PRIMARY KEY,
    source_domain VARCHAR UNIQUE,
    total_claims INTEGER DEFAULT 0,
    verified_count INTEGER DEFAULT 0,
    debunked_count INTEGER DEFAULT 0,
    credibility_score FLOAT DEFAULT 0.5,
    bias_indicators JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Narrative clusters
CREATE TABLE narrative_clusters (
    id SERIAL PRIMARY KEY,
    cluster_name VARCHAR,
    centroid_embedding vector(1536),
    claim_ids VARCHAR[],
    first_seen TIMESTAMP,
    spread_velocity FLOAT,
    primary_sources VARCHAR[],
    is_coordinated BOOLEAN DEFAULT FALSE
);
```

### 1.2 Embedding Service

```python
# backend/app/services/embeddings.py
import os
from typing import List, Optional
import openai
from app.database import SessionLocal
from app.database.models import Claim

class EmbeddingService:
    def __init__(self):
        self.client = openai.OpenAI()
        self.model = "text-embedding-3-small"  # 1536 dimensions, cost-effective
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    def embed_claim(self, claim: Claim) -> List[float]:
        """Generate contextual embedding for a claim"""
        # Combine claim text with context for richer embedding
        context = f"""
        Claim: {claim.claim_text}
        Original: {claim.original_text[:500]}
        Status: {claim.status.value}
        Topics: {', '.join([t.name for t in claim.topics])}
        """
        return self.embed_text(context)
    
    async def find_similar_claims(
        self, 
        query_embedding: List[float], 
        limit: int = 10,
        threshold: float = 0.75
    ) -> List[dict]:
        """Find semantically similar claims using pgvector"""
        db = SessionLocal()
        try:
            # Cosine similarity search with pgvector
            results = db.execute("""
                SELECT id, claim_text, status, explanation,
                       1 - (embedding <=> :query_embedding) as similarity
                FROM claims
                WHERE embedding IS NOT NULL
                  AND 1 - (embedding <=> :query_embedding) > :threshold
                ORDER BY embedding <=> :query_embedding
                LIMIT :limit
            """, {
                "query_embedding": str(query_embedding),
                "threshold": threshold,
                "limit": limit
            }).fetchall()
            
            return [
                {
                    "id": r.id,
                    "claim_text": r.claim_text,
                    "status": r.status,
                    "similarity": r.similarity
                }
                for r in results
            ]
        finally:
            db.close()
```

### 1.3 Knowledge Graph Builder

```python
# backend/app/services/knowledge_graph.py
from typing import List, Dict, Tuple
from app.database import SessionLocal
from app.database.models import Entity, Claim
import networkx as nx

class KnowledgeGraphService:
    """Build and query a knowledge graph of Mexican political entities"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def build_entity_graph(self) -> nx.DiGraph:
        """Build graph from database relationships"""
        db = SessionLocal()
        try:
            # Load entities
            entities = db.query(Entity).all()
            for entity in entities:
                self.graph.add_node(
                    entity.name,
                    type=entity.entity_type,
                    data=entity.extra_data
                )
            
            # Extract relationships from claims
            claims = db.query(Claim).all()
            for claim in claims:
                entities_in_claim = self._extract_entities_from_claim(claim)
                # Create edges between co-occurring entities
                for i, e1 in enumerate(entities_in_claim):
                    for e2 in entities_in_claim[i+1:]:
                        if self.graph.has_edge(e1, e2):
                            self.graph[e1][e2]['weight'] += 1
                            self.graph[e1][e2]['claims'].append(claim.id)
                        else:
                            self.graph.add_edge(
                                e1, e2, 
                                weight=1, 
                                claims=[claim.id],
                                relationship_type="co-mentioned"
                            )
            
            return self.graph
        finally:
            db.close()
    
    def find_entity_connections(
        self, 
        entity_name: str, 
        depth: int = 2
    ) -> Dict:
        """Find all entities connected to a given entity"""
        if entity_name not in self.graph:
            return {"error": "Entity not found"}
        
        # BFS to find connected entities
        connections = {}
        visited = {entity_name}
        queue = [(entity_name, 0)]
        
        while queue:
            current, current_depth = queue.pop(0)
            if current_depth >= depth:
                continue
                
            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    edge_data = self.graph[current][neighbor]
                    connections[neighbor] = {
                        "depth": current_depth + 1,
                        "connection_strength": edge_data['weight'],
                        "through": current,
                        "shared_claims": len(edge_data['claims'])
                    }
                    queue.append((neighbor, current_depth + 1))
        
        return connections
    
    def detect_influence_networks(self) -> List[Dict]:
        """Detect potential influence/coordination networks"""
        # Find strongly connected components
        communities = list(nx.community.louvain_communities(
            self.graph.to_undirected()
        ))
        
        influential_networks = []
        for community in communities:
            if len(community) >= 3:
                subgraph = self.graph.subgraph(community)
                influential_networks.append({
                    "entities": list(community),
                    "density": nx.density(subgraph),
                    "central_entity": max(
                        community, 
                        key=lambda x: self.graph.degree(x)
                    )
                })
        
        return sorted(
            influential_networks, 
            key=lambda x: x['density'], 
            reverse=True
        )
```

---

## Phase 2: Advanced AI Agents (6-8 weeks)

### 2.1 Multi-Agent Verification System

Replace single-shot verification with a team of specialized agents.

```python
# backend/app/agents/verification_team.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pydantic import BaseModel
import anthropic
import asyncio

class AgentResult(BaseModel):
    agent_name: str
    confidence: float
    findings: str
    sources: List[str]
    verdict: Optional[str] = None

class BaseAgent(ABC):
    """Base class for verification agents"""
    
    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.model = "claude-sonnet-4-20250514"
    
    @abstractmethod
    async def analyze(self, claim: str, context: Dict) -> AgentResult:
        pass

class SourceCredibilityAgent(BaseAgent):
    """Evaluates the credibility of sources"""
    
    async def analyze(self, claim: str, context: Dict) -> AgentResult:
        sources = context.get("sources", [])
        
        prompt = f"""You are a source credibility analyst specializing in Mexican media.

Analyze these sources for credibility:
{chr(10).join([f'- {s}' for s in sources])}

Consider:
1. Is it a recognized news outlet? (Animal Político, Reforma, El Universal = high credibility)
2. Is it a government source? (INE, Banxico, DOF = official but check political bias)
3. Is it social media? (Lower credibility, needs corroboration)
4. Known satire sites? (El Deforma = satire, don't use as evidence)

Return JSON:
{{
    "credibility_scores": {{"source_url": score}},
    "most_credible": "url",
    "concerns": ["list of concerns"],
    "overall_source_quality": "high|medium|low"
}}"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return AgentResult(
            agent_name="SourceCredibilityAgent",
            confidence=0.8,
            findings=response.content[0].text,
            sources=sources
        )

class HistoricalContextAgent(BaseAgent):
    """Provides historical context and checks for contradictions"""
    
    async def analyze(self, claim: str, context: Dict) -> AgentResult:
        similar_claims = context.get("similar_claims", [])
        entity_facts = context.get("entity_facts", [])
        
        prompt = f"""You are a political historian specializing in Mexican politics.

CLAIM TO ANALYZE: "{claim}"

SIMILAR PAST CLAIMS:
{chr(10).join([f'- {c["claim_text"]} (Status: {c["status"]})' for c in similar_claims[:5]])}

KNOWN FACTS ABOUT ENTITIES:
{chr(10).join([f'- {f}' for f in entity_facts[:10]])}

Analyze:
1. Does this claim contradict known facts?
2. Is this claim a repeat of previously debunked information?
3. What historical context is relevant?
4. Are there patterns of similar misinformation?

Return JSON:
{{
    "contradictions_found": true/false,
    "contradicting_facts": ["list"],
    "historical_context": "explanation",
    "similar_debunked_patterns": ["list"],
    "confidence": 0.0-1.0
}}"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return AgentResult(
            agent_name="HistoricalContextAgent",
            confidence=0.85,
            findings=response.content[0].text,
            sources=[c["id"] for c in similar_claims[:5]]
        )

class LogicalConsistencyAgent(BaseAgent):
    """Checks for logical fallacies and internal consistency"""
    
    async def analyze(self, claim: str, context: Dict) -> AgentResult:
        prompt = f"""You are a logic and reasoning expert.

CLAIM: "{claim}"

Analyze for:
1. Internal logical consistency
2. Common logical fallacies (strawman, ad hominem, false dichotomy, etc.)
3. Statistical manipulation or cherry-picking
4. Misleading framing or context manipulation
5. Emotional manipulation vs factual claims

Return JSON:
{{
    "is_logically_consistent": true/false,
    "fallacies_detected": ["list with explanations"],
    "manipulation_techniques": ["list"],
    "factual_components": ["extractable facts that can be verified"],
    "opinion_components": ["parts that are opinion/interpretation"]
}}"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return AgentResult(
            agent_name="LogicalConsistencyAgent",
            confidence=0.75,
            findings=response.content[0].text,
            sources=[]
        )

class EvidenceAnalysisAgent(BaseAgent):
    """Deep analysis of evidence documents"""
    
    async def analyze(self, claim: str, context: Dict) -> AgentResult:
        evidence_texts = context.get("evidence_texts", [])
        
        prompt = f"""You are an investigative journalist analyzing evidence.

CLAIM: "{claim}"

EVIDENCE FOUND:
{chr(10).join([f'Source {i+1}: {e[:1000]}...' for i, e in enumerate(evidence_texts[:3])])}

Analyze:
1. Does the evidence directly support or refute the claim?
2. Is the evidence from primary sources or secondary reporting?
3. Are there gaps in the evidence?
4. What additional evidence would be needed for certainty?

Return JSON:
{{
    "supports_claim": true/false/partial,
    "evidence_strength": "strong|moderate|weak|insufficient",
    "key_supporting_points": ["list"],
    "key_refuting_points": ["list"],
    "evidence_gaps": ["list"],
    "verdict_confidence": 0.0-1.0
}}"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return AgentResult(
            agent_name="EvidenceAnalysisAgent",
            confidence=0.9,
            findings=response.content[0].text,
            sources=context.get("evidence_urls", [])
        )

class VerificationOrchestrator:
    """Orchestrates the multi-agent verification process"""
    
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.agents = [
            SourceCredibilityAgent(self.client),
            HistoricalContextAgent(self.client),
            LogicalConsistencyAgent(self.client),
            EvidenceAnalysisAgent(self.client),
        ]
    
    async def verify_claim(
        self, 
        claim: str, 
        context: Dict
    ) -> Dict:
        """Run all agents in parallel and synthesize results"""
        
        # Run all agents concurrently
        tasks = [agent.analyze(claim, context) for agent in self.agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_results = [r for r in results if isinstance(r, AgentResult)]
        
        # Synthesize final verdict
        final_verdict = await self._synthesize_verdict(claim, valid_results)
        
        return {
            "claim": claim,
            "agent_results": [r.dict() for r in valid_results],
            "final_verdict": final_verdict
        }
    
    async def _synthesize_verdict(
        self, 
        claim: str, 
        agent_results: List[AgentResult]
    ) -> Dict:
        """Final judge synthesizes all agent findings"""
        
        findings_summary = "\n\n".join([
            f"**{r.agent_name}** (Confidence: {r.confidence}):\n{r.findings}"
            for r in agent_results
        ])
        
        prompt = f"""You are the Chief Fact-Checker making the final verdict.

CLAIM: "{claim}"

AGENT ANALYSES:
{findings_summary}

Based on ALL agent findings, provide the final verdict.

Rules:
1. If agents disagree significantly, verdict should be "Unverified"
2. "Debunked" requires strong evidence of falsehood
3. "Misleading" for technically true but contextually deceptive
4. "Verified" requires corroboration from credible sources
5. Weight agent confidence scores in your decision

Return JSON:
{{
    "status": "Verified|Debunked|Misleading|Unverified",
    "confidence": 0.0-1.0,
    "explanation": "2-3 sentence explanation in Spanish for Mexican audience",
    "key_evidence": ["list of key evidence points"],
    "caveats": ["any important caveats"],
    "recommended_sources_for_readers": ["urls"]
}}"""
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        return json.loads(response.content[0].text)
```

### 2.2 RAG Pipeline for Context Retrieval

```python
# backend/app/services/rag_pipeline.py
from typing import List, Dict
from app.services.embeddings import EmbeddingService
from app.database import SessionLocal
from app.database.models import Claim, Entity
import httpx

class RAGPipeline:
    """Retrieval-Augmented Generation for fact-checking"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.serper_api_key = os.getenv("SERPER_API_KEY")
    
    async def build_context(self, claim_text: str) -> Dict:
        """Build rich context for verification agents"""
        
        # Generate embedding for the claim
        claim_embedding = self.embedding_service.embed_text(claim_text)
        
        # Parallel retrieval
        similar_claims, entity_facts, web_evidence = await asyncio.gather(
            self._get_similar_claims(claim_embedding),
            self._get_entity_knowledge(claim_text),
            self._search_web_evidence(claim_text)
        )
        
        # Fetch full text of top evidence sources
        evidence_texts = await self._fetch_evidence_content(
            [e["url"] for e in web_evidence[:5]]
        )
        
        return {
            "similar_claims": similar_claims,
            "entity_facts": entity_facts,
            "sources": [e["url"] for e in web_evidence],
            "evidence_texts": evidence_texts,
            "evidence_urls": [e["url"] for e in web_evidence[:5]]
        }
    
    async def _get_similar_claims(
        self, 
        embedding: List[float],
        limit: int = 10
    ) -> List[Dict]:
        """Find similar past claims"""
        return await self.embedding_service.find_similar_claims(
            embedding, limit=limit, threshold=0.7
        )
    
    async def _get_entity_knowledge(self, claim_text: str) -> List[str]:
        """Get known facts about entities in the claim"""
        db = SessionLocal()
        try:
            # Extract entities from claim (simple approach)
            entities = db.query(Entity).all()
            relevant_facts = []
            
            for entity in entities:
                if entity.name.lower() in claim_text.lower():
                    # Get facts about this entity
                    facts = db.execute("""
                        SELECT fact_text, confidence 
                        FROM entity_knowledge
                        WHERE entity_id = :entity_id
                        AND confidence > 0.7
                        ORDER BY confidence DESC
                        LIMIT 5
                    """, {"entity_id": entity.id}).fetchall()
                    
                    for fact in facts:
                        relevant_facts.append(f"{entity.name}: {fact.fact_text}")
            
            return relevant_facts
        finally:
            db.close()
    
    async def _search_web_evidence(
        self, 
        claim_text: str
    ) -> List[Dict]:
        """Search for evidence using Serper API"""
        if not self.serper_api_key:
            return []
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": self.serper_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "q": f"{claim_text} verificación fact-check México",
                    "num": 15,
                    "gl": "mx",
                    "hl": "es"
                }
            )
            data = response.json()
            
            results = []
            for item in data.get("organic", []):
                results.append({
                    "url": item.get("link"),
                    "title": item.get("title"),
                    "snippet": item.get("snippet")
                })
            
            return results
    
    async def _fetch_evidence_content(
        self, 
        urls: List[str]
    ) -> List[str]:
        """Fetch and extract text content from evidence URLs"""
        from bs4 import BeautifulSoup
        
        async def fetch_one(url: str) -> str:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove scripts, styles
                    for tag in soup(['script', 'style', 'nav', 'footer']):
                        tag.decompose()
                    
                    # Get main content
                    article = soup.find('article') or soup.find('main') or soup.body
                    if article:
                        return article.get_text(separator=' ', strip=True)[:3000]
                    return ""
            except:
                return ""
        
        tasks = [fetch_one(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]
```

---

## Phase 3: Learning & Feedback Loops (4-6 weeks)

### 3.1 Human Feedback Integration

```python
# backend/app/services/feedback_learning.py
from typing import Optional
from datetime import datetime
from app.database import SessionLocal
from app.database.models import Claim

class FeedbackLearningService:
    """Learn from human corrections and feedback"""
    
    async def record_correction(
        self,
        claim_id: str,
        original_status: str,
        corrected_status: str,
        correction_reason: str,
        corrector_id: Optional[int] = None
    ):
        """Record when a human corrects an AI verification"""
        db = SessionLocal()
        try:
            # Store correction
            db.execute("""
                INSERT INTO verification_corrections (
                    claim_id, original_status, corrected_status,
                    correction_reason, corrector_id, created_at
                ) VALUES (:claim_id, :original, :corrected, :reason, :corrector, :now)
            """, {
                "claim_id": claim_id,
                "original": original_status,
                "corrected": corrected_status,
                "reason": correction_reason,
                "corrector": corrector_id,
                "now": datetime.utcnow()
            })
            
            # Update claim
            db.execute("""
                UPDATE claims 
                SET status = :status, 
                    explanation = CONCAT(explanation, ' [Corregido: ', :reason, ']'),
                    updated_at = :now
                WHERE id = :claim_id
            """, {
                "status": corrected_status,
                "reason": correction_reason,
                "claim_id": claim_id,
                "now": datetime.utcnow()
            })
            
            db.commit()
            
            # Trigger learning pipeline
            await self._update_learning_signals(claim_id, corrected_status)
            
        finally:
            db.close()
    
    async def _update_learning_signals(self, claim_id: str, correct_status: str):
        """Update knowledge base with correction signals"""
        db = SessionLocal()
        try:
            claim = db.query(Claim).filter(Claim.id == claim_id).first()
            if not claim:
                return
            
            # Update entity knowledge confidence
            # If claim was about an entity and was corrected, adjust confidence
            for entity in claim.entities if hasattr(claim, 'entities') else []:
                # Lower confidence of facts that led to wrong verdict
                db.execute("""
                    UPDATE entity_knowledge
                    SET confidence = confidence * 0.9
                    WHERE entity_id = :entity_id
                    AND source_claim_id = :claim_id
                """, {"entity_id": entity.id, "claim_id": claim_id})
            
            # Update source credibility if correction indicates source unreliability
            if claim.source and correct_status in ["Debunked", "Misleading"]:
                source_domain = self._extract_domain(claim.source.url)
                db.execute("""
                    UPDATE source_credibility
                    SET debunked_count = debunked_count + 1,
                        credibility_score = (verified_count::float) / NULLIF(total_claims, 0)
                    WHERE source_domain = :domain
                """, {"domain": source_domain})
            
            db.commit()
        finally:
            db.close()
    
    async def get_accuracy_metrics(self, days: int = 30) -> Dict:
        """Calculate verification accuracy based on corrections"""
        db = SessionLocal()
        try:
            result = db.execute("""
                SELECT 
                    COUNT(*) as total_corrections,
                    COUNT(CASE WHEN original_status = 'Verified' AND corrected_status = 'Debunked' THEN 1 END) as false_positives,
                    COUNT(CASE WHEN original_status = 'Debunked' AND corrected_status = 'Verified' THEN 1 END) as false_negatives,
                    COUNT(CASE WHEN original_status = 'Unverified' THEN 1 END) as uncertainty_resolved
                FROM verification_corrections
                WHERE created_at >= NOW() - INTERVAL ':days days'
            """, {"days": days}).fetchone()
            
            total_claims = db.execute("""
                SELECT COUNT(*) FROM claims 
                WHERE created_at >= NOW() - INTERVAL ':days days'
            """, {"days": days}).scalar()
            
            return {
                "total_verifications": total_claims,
                "corrections_needed": result.total_corrections,
                "accuracy_rate": 1 - (result.total_corrections / max(total_claims, 1)),
                "false_positive_rate": result.false_positives / max(total_claims, 1),
                "false_negative_rate": result.false_negatives / max(total_claims, 1)
            }
        finally:
            db.close()
```

### 3.2 Continuous Knowledge Extraction

```python
# backend/app/tasks/knowledge_extraction.py
from celery import shared_task
from app.database import SessionLocal
from app.database.models import Claim, Entity
from app.services.embeddings import EmbeddingService
import anthropic

@shared_task
def extract_knowledge_from_verified_claims():
    """Extract facts from verified claims to build knowledge base"""
    db = SessionLocal()
    client = anthropic.Anthropic()
    embedding_service = EmbeddingService()
    
    try:
        # Get recently verified claims not yet processed for knowledge
        claims = db.execute("""
            SELECT c.* FROM claims c
            LEFT JOIN entity_knowledge ek ON ek.source_claim_id = c.id
            WHERE c.status IN ('Verified', 'Debunked')
            AND ek.id IS NULL
            AND c.created_at >= NOW() - INTERVAL '7 days'
            LIMIT 50
        """).fetchall()
        
        for claim in claims:
            # Extract facts using LLM
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""Extract verifiable facts from this verified claim:

Claim: "{claim.claim_text}"
Status: {claim.status}
Explanation: {claim.explanation}

Return JSON array of facts:
[
  {{"entity": "Entity Name", "fact": "Specific verifiable fact", "confidence": 0.0-1.0}}
]

Only include facts that are clearly established, not opinions or interpretations."""
                }]
            )
            
            import json
            facts = json.loads(response.content[0].text)
            
            for fact in facts:
                # Find or create entity
                entity = db.query(Entity).filter(
                    Entity.name.ilike(f"%{fact['entity']}%")
                ).first()
                
                if entity:
                    # Generate embedding for the fact
                    fact_embedding = embedding_service.embed_text(fact['fact'])
                    
                    # Store fact
                    db.execute("""
                        INSERT INTO entity_knowledge (
                            entity_id, fact_text, fact_embedding, 
                            source_claim_id, confidence, verified_at
                        ) VALUES (
                            :entity_id, :fact_text, :embedding,
                            :claim_id, :confidence, NOW()
                        )
                        ON CONFLICT (entity_id, fact_text) 
                        DO UPDATE SET confidence = GREATEST(entity_knowledge.confidence, :confidence)
                    """, {
                        "entity_id": entity.id,
                        "fact_text": fact['fact'],
                        "embedding": str(fact_embedding),
                        "claim_id": claim.id,
                        "confidence": fact['confidence']
                    })
            
            db.commit()
            
    finally:
        db.close()

@shared_task
def detect_contradictions():
    """Detect contradictions between new claims and known facts"""
    db = SessionLocal()
    embedding_service = EmbeddingService()
    
    try:
        # Get recent unverified claims
        unverified = db.execute("""
            SELECT * FROM claims 
            WHERE status = 'Unverified'
            AND created_at >= NOW() - INTERVAL '24 hours'
        """).fetchall()
        
        for claim in unverified:
            claim_embedding = embedding_service.embed_text(claim.claim_text)
            
            # Find contradicting facts
            contradictions = db.execute("""
                SELECT ek.*, e.name as entity_name,
                       1 - (ek.fact_embedding <=> :embedding) as similarity
                FROM entity_knowledge ek
                JOIN entities e ON e.id = ek.entity_id
                WHERE 1 - (ek.fact_embedding <=> :embedding) > 0.7
                AND ek.confidence > 0.8
                ORDER BY similarity DESC
                LIMIT 10
            """, {"embedding": str(claim_embedding)}).fetchall()
            
            if contradictions:
                # Mark claim for manual review with contradiction evidence
                db.execute("""
                    UPDATE claims 
                    SET explanation = CONCAT(
                        'POSIBLE CONTRADICCIÓN: Este claim puede contradecir hechos conocidos. ',
                        explanation
                    ),
                    evidence_sources = :evidence
                    WHERE id = :claim_id
                """, {
                    "evidence": [c.source_claim_id for c in contradictions],
                    "claim_id": claim.id
                })
        
        db.commit()
        
    finally:
        db.close()
```

---

## Phase 4: Advanced Analytics & Prediction (6-8 weeks)

### 4.1 Narrative Tracking & Early Warning

```python
# backend/app/services/narrative_intelligence.py
from typing import List, Dict
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.services.embeddings import EmbeddingService
import numpy as np
from sklearn.cluster import DBSCAN

class NarrativeIntelligenceService:
    """Track and predict misinformation narratives"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    async def detect_emerging_narratives(
        self, 
        time_window_hours: int = 24
    ) -> List[Dict]:
        """Detect new narrative clusters emerging"""
        db = SessionLocal()
        try:
            # Get recent claims with embeddings
            claims = db.execute("""
                SELECT id, claim_text, embedding, status, created_at
                FROM claims
                WHERE created_at >= NOW() - INTERVAL ':hours hours'
                AND embedding IS NOT NULL
            """, {"hours": time_window_hours}).fetchall()
            
            if len(claims) < 5:
                return []
            
            # Convert embeddings to numpy array
            embeddings = np.array([
                np.frombuffer(c.embedding, dtype=np.float32) 
                for c in claims
            ])
            
            # Cluster similar claims
            clustering = DBSCAN(eps=0.3, min_samples=3, metric='cosine')
            cluster_labels = clustering.fit_predict(embeddings)
            
            # Analyze clusters
            narratives = []
            for cluster_id in set(cluster_labels):
                if cluster_id == -1:  # Noise
                    continue
                
                cluster_claims = [
                    claims[i] for i, label in enumerate(cluster_labels) 
                    if label == cluster_id
                ]
                
                # Calculate cluster metrics
                debunked_ratio = sum(
                    1 for c in cluster_claims if c.status == 'Debunked'
                ) / len(cluster_claims)
                
                spread_velocity = len(cluster_claims) / time_window_hours
                
                # Get representative claim
                centroid = embeddings[cluster_labels == cluster_id].mean(axis=0)
                
                narratives.append({
                    "cluster_id": int(cluster_id),
                    "claim_count": len(cluster_claims),
                    "sample_claims": [c.claim_text for c in cluster_claims[:3]],
                    "debunked_ratio": debunked_ratio,
                    "spread_velocity": spread_velocity,
                    "first_seen": min(c.created_at for c in cluster_claims),
                    "risk_score": self._calculate_risk_score(
                        debunked_ratio, spread_velocity, len(cluster_claims)
                    ),
                    "is_emerging": spread_velocity > 2  # More than 2 claims/hour
                })
            
            return sorted(narratives, key=lambda x: x['risk_score'], reverse=True)
            
        finally:
            db.close()
    
    def _calculate_risk_score(
        self, 
        debunked_ratio: float, 
        spread_velocity: float, 
        claim_count: int
    ) -> float:
        """Calculate risk score for a narrative"""
        # Higher risk if:
        # - High debunked ratio (more false claims)
        # - High spread velocity (spreading fast)
        # - More claims (bigger reach)
        
        risk = (
            debunked_ratio * 0.4 +
            min(spread_velocity / 10, 1.0) * 0.3 +
            min(claim_count / 50, 1.0) * 0.3
        )
        return round(risk, 2)
    
    async def predict_narrative_spread(
        self, 
        narrative_id: int
    ) -> Dict:
        """Predict how a narrative will spread"""
        db = SessionLocal()
        try:
            # Get narrative history
            narrative = db.execute("""
                SELECT * FROM narrative_clusters
                WHERE id = :id
            """, {"id": narrative_id}).fetchone()
            
            # Analyze historical spread patterns
            historical = db.execute("""
                SELECT 
                    DATE_TRUNC('hour', c.created_at) as hour,
                    COUNT(*) as count
                FROM claims c
                WHERE c.id = ANY(:claim_ids)
                GROUP BY DATE_TRUNC('hour', c.created_at)
                ORDER BY hour
            """, {"claim_ids": narrative.claim_ids}).fetchall()
            
            # Simple trend analysis
            counts = [h.count for h in historical]
            if len(counts) >= 3:
                trend = (counts[-1] - counts[0]) / len(counts)
                predicted_24h = counts[-1] + (trend * 24)
            else:
                trend = 0
                predicted_24h = sum(counts)
            
            return {
                "narrative_id": narrative_id,
                "current_count": len(narrative.claim_ids),
                "trend": "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable",
                "predicted_claims_24h": max(0, int(predicted_24h)),
                "peak_hour": max(historical, key=lambda x: x.count).hour if historical else None,
                "recommendation": self._get_recommendation(trend, narrative.is_coordinated)
            }
            
        finally:
            db.close()
    
    def _get_recommendation(self, trend: float, is_coordinated: bool) -> str:
        if is_coordinated:
            return "ALTA PRIORIDAD: Posible campaña coordinada detectada. Se recomienda investigación profunda."
        elif trend > 5:
            return "ALERTA: Narrativa en rápida expansión. Considerar fact-check prioritario."
        elif trend > 0:
            return "MONITOREAR: Narrativa en crecimiento. Mantener vigilancia."
        else:
            return "BAJA PRIORIDAD: Narrativa estable o en declive."
```

### 4.2 API for Researchers & Media

```python
# backend/app/routers/intelligence.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.services.narrative_intelligence import NarrativeIntelligenceService
from app.services.knowledge_graph import KnowledgeGraphService
from app.auth import require_pro_subscription

router = APIRouter(prefix="/api/v1/intelligence", tags=["Intelligence"])

@router.get("/narratives/emerging")
async def get_emerging_narratives(
    hours: int = Query(24, ge=1, le=168),
    user = Depends(require_pro_subscription)
):
    """Get emerging misinformation narratives (Pro feature)"""
    service = NarrativeIntelligenceService()
    narratives = await service.detect_emerging_narratives(hours)
    return {
        "time_window_hours": hours,
        "narratives": narratives,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/entities/{entity_name}/network")
async def get_entity_network(
    entity_name: str,
    depth: int = Query(2, ge=1, le=4),
    user = Depends(require_pro_subscription)
):
    """Get entity connection network (Pro feature)"""
    service = KnowledgeGraphService()
    service.build_entity_graph()
    
    connections = service.find_entity_connections(entity_name, depth)
    if "error" in connections:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return {
        "entity": entity_name,
        "depth": depth,
        "connections": connections
    }

@router.get("/alerts/realtime")
async def get_realtime_alerts(
    user = Depends(require_pro_subscription)
):
    """Get real-time misinformation alerts"""
    service = NarrativeIntelligenceService()
    
    # Get high-risk narratives
    narratives = await service.detect_emerging_narratives(6)
    high_risk = [n for n in narratives if n['risk_score'] > 0.7]
    
    # Get contradiction alerts
    db = SessionLocal()
    contradictions = db.execute("""
        SELECT * FROM claims
        WHERE explanation LIKE '%POSIBLE CONTRADICCIÓN%'
        AND created_at >= NOW() - INTERVAL '6 hours'
    """).fetchall()
    
    return {
        "high_risk_narratives": high_risk,
        "contradiction_alerts": [
            {"claim_id": c.id, "claim_text": c.claim_text}
            for c in contradictions
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/export/research")
async def export_research_data(
    start_date: str,
    end_date: str,
    include_embeddings: bool = False,
    format: str = "json",
    user = Depends(require_pro_subscription)
):
    """Export data for research purposes (Pro feature)"""
    # Implementation for research data export
    pass
```

---

## Phase 5: Additional Data Sources (Ongoing)

### New Scrapers to Implement

```python
# Priority data sources for Mexican politics

class TikTokScraper:
    """Scrape TikTok political content (complex - may need API partnership)"""
    pass

class FacebookGroupScraper:
    """Monitor Facebook political groups"""
    pass

class TelegramChannelScraper:
    """Monitor Telegram channels spreading political content"""
    pass

class WhatsAppTipLine:
    """Receive user-submitted content for verification"""
    # Already partially implemented in your codebase
    pass

class CongressionalRecordScraper:
    """Scrape official congressional records for fact-checking"""
    # Diario de Debates, Gaceta Parlamentaria
    pass

class OfficialGazetteScraper:
    """Scrape DOF (Diario Oficial de la Federación)"""
    pass
```

---

## Implementation Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Vector DB + Embeddings | 🔥 High | Medium | **P0** |
| RAG Pipeline | 🔥 High | Medium | **P0** |
| Multi-Agent Verification | 🔥 High | High | **P1** |
| Feedback Learning | Medium | Low | **P1** |
| Knowledge Graph | Medium | Medium | **P2** |
| Narrative Intelligence | 🔥 High | High | **P2** |
| Research API | Medium | Low | **P2** |
| New Scrapers | Medium | High | **P3** |

---

## Success Metrics

### Technical KPIs
- Verification accuracy: >90% (measured by human corrections)
- Similar claim retrieval precision: >85%
- False positive rate: <5%
- Processing time: <10s per claim

### Business KPIs
- API subscriptions from media organizations
- Research citations
- User engagement (time on site, shares)
- Coverage in mainstream media

---

## Cost Estimates

| Component | Monthly Cost (Est.) |
|-----------|---------------------|
| OpenAI Embeddings | $50-200 |
| Claude API (verification) | $200-500 |
| Serper API | $50-100 |
| Neon PostgreSQL (Pro) | $50-100 |
| Redis (Upstash) | $10-30 |
| **Total** | **$360-930/month** |

Scale with usage - these are estimates for moderate traffic (~10K verifications/month).

---

## Next Steps

1. **Enable pgvector** on your Neon database
2. **Implement embedding service** and backfill existing claims
3. **Build RAG pipeline** for context retrieval
4. **Deploy multi-agent verification** for new claims
5. **Set up feedback collection** UI and learning pipeline
6. **Launch intelligence API** for Pro subscribers

This roadmap transforms FactCheckr from a basic fact-checker into a **Mexican Political Intelligence Platform** that media, researchers, and policymakers will depend on.

