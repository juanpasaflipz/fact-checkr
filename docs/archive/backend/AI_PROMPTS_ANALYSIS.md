# AI Prompts Analysis & Improvements

## Current AI Prompts Used in Fact-Checking

### 1. Claim Extraction Prompt (`_extract_claim`)

**System Prompt:**
```
You are a data analyst processing Mexican political social media streams.
Current Date: {current_date}.
President of Mexico: Claudia Sheinbaum.

Your task is to extract ONLY factual claims that can be verified. Ignore opinions, insults, hashtags, and vague complaints.
```

**User Prompt:**
```
INPUT TEXT: "{content}"

INSTRUCTIONS:
1. Ignore insults, hashtags, opinions, or vague complaints (e.g., "Morena ruined everything").
2. Extract the specific *factual claim* that can be proven or disproven.
3. If the text is pure opinion or satire with no factual basis, return "SKIP".
4. Translate the claim to neutral, formal Spanish.

OUTPUT FORMAT (String only):
[The Claim] OR "SKIP"
```

**Issues:**
- ✅ Good at filtering non-factual content
- ❌ Does NOT classify topics
- ❌ No topic extraction

---

### 2. Claim Verification Prompt (`_verify_claim`)

**System Prompt:**
```
You are a neutral, objective Ombudsman for Mexican News. You adhere to the principles of "Verificado MX" and "Animal Político".

Current Date: {current_date}.

You must analyze claims ONLY based on the provided EVIDENCE. Do not use your internal memory for facts unless they are universal constants. Be thorough, objective, and cite specific evidence in your analysis.
```

**User Prompt:**
```
CLAIM TO CHECK: "{claim}"

SEARCH RESULTS (EVIDENCE):
{evidence_text}

INSTRUCTIONS:
1. Analyze the claim solely based on the provided EVIDENCE.
2. If the EVIDENCE is contradictory or insufficient, the verdict must be "Unverified".
3. If the claim comes from a known satire site (like El Deforma), mark as "Unverified" with explanation.
4. "Misleading" applies if the facts are real but the context is manipulated.
5. Be precise and objective in your analysis.

RESPONSE FORMAT (JSON only, no markdown):
{
    "status": "Verified" | "Debunked" | "Misleading" | "Unverified",
    "explanation": "A concise (max 280 chars) explanation in Mexican Spanish. Tone: informational, not scolding."
}
```

**Issues:**
- ✅ Good evidence-based verification
- ✅ Clear status classification
- ❌ Does NOT extract topics
- ❌ No topic classification

---

### 3. Entity Extraction Prompt (`_extract_entities`)

**System Prompt:**
```
You are an entity extraction system for Mexican political news.
Extract only: politicians, government institutions, political parties, and locations.
Return a JSON array of [name, type] pairs where type is "person", "institution", or "location".
```

**User Prompt:**
```
Extract entities from this claim: "{claim_text}"

Return JSON format:
[["Entity Name", "person|institution|location"], ...]
```

**Issues:**
- ✅ Extracts entities
- ❌ Does NOT extract topics
- ❌ No topic classification

---

## Problems Identified

### Critical Issue: **Topics Are Never Extracted or Assigned**

1. **No Topic Extraction Method**: The `FactChecker` class has `_extract_entities()` but NO `_extract_topics()` method
2. **No Topic Assignment**: In `fact_check.py`, topics are never linked to claims
3. **No Topics in Database**: Seed files don't create any topics
4. **Temas Page Will Be Empty**: Without topics assigned to claims, the `/temas` page will show no data

---

## Proposed Improvements

### 1. Add Topic Extraction to AI Agent

**New Method: `_extract_topics()`**
- Classify claims into predefined topic categories
- Use existing topics from database or create new ones
- Return topic names/slugs that match database

### 2. Enhanced Prompt for Topic Classification

**System Prompt:**
```
You are a topic classification system for Mexican political news.
Classify claims into relevant topics based on Mexican political and social context.
```

**User Prompt:**
```
CLAIM: "{claim_text}"

AVAILABLE TOPICS:
{list_of_topics}

INSTRUCTIONS:
1. Classify this claim into 1-3 most relevant topics from the list above.
2. If no topic fits, suggest a new topic name (in Spanish).
3. Consider: Executive, Legislative, Judicial, Economy, Security, Health, Education, Infrastructure, etc.

RESPONSE FORMAT (JSON):
{
    "topics": ["Topic Name 1", "Topic Name 2"],
    "suggested_new_topics": ["New Topic Name"] // optional
}
```

### 3. Update Fact-Checking Pipeline

Add topic extraction and assignment in `fact_check.py`:
```python
# 6. Extract Topics (NEW)
topics = await checker._extract_topics(claim_text, db)

# 7. Link Topics to Claim (NEW)
for topic_name in topics:
    db_topic = db.query(Topic).filter(Topic.name == topic_name).first()
    if db_topic:
        claim.topics.append(db_topic)
```

### 4. Seed Topics in Database

Create common Mexican political topics:
- Reforma Judicial
- Ejecutivo
- Legislativo
- Economía
- Seguridad
- Salud
- Educación
- Infraestructura
- etc.

---

## Implementation Plan

1. ✅ Create topic seed script
2. ✅ Add `_extract_topics()` method to `FactChecker`
3. ✅ Update `fact_check.py` to extract and assign topics
4. ✅ Test with existing claims
5. ✅ Verify Temas page displays data

