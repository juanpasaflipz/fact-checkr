# Temas Page Improvements & Algorithm Fixes

## Problems Identified & Fixed

### ❌ **Critical Issue: Topics Were Never Assigned to Claims**

**Problem:**
- The fact-checking pipeline extracted claims, verified them, and extracted entities
- **BUT topics were NEVER extracted or assigned to claims**
- Result: The `/temas` page would show empty or no data

**Root Causes:**
1. No `_extract_topics()` method in `FactChecker` class
2. No topic assignment in `fact_check.py` pipeline
3. No topics seeded in database
4. AI prompts didn't include topic classification

---

## ✅ Solutions Implemented

### 1. **Topic Seed Script** (`seed_topics.py`)

Created 15 predefined topics for Mexican political fact-checking:
- Reforma Judicial
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
- Tecnología

**Usage:**
```bash
cd backend
python seed_topics.py
```

### 2. **Topic Extraction Method** (`_extract_topics()`)

Added new AI-powered topic classification method to `FactChecker` class:

**Features:**
- Uses Anthropic Claude (primary) or OpenAI (fallback)
- Classifies claims into 1-3 relevant topics
- Matches topics to existing database topics
- Returns topic names for database linking

**New AI Prompt:**
```
System: You are a topic classification system for Mexican political news.
        Classify claims into relevant topics based on Mexican political context.

User: CLAIM: "{claim_text}"
      AVAILABLE TOPICS: [list of topics]
      
      INSTRUCTIONS:
      1. Classify into 1-3 most relevant topics
      2. Return only topic names that match the list
      3. Consider main subject: Executive, Legislative, Judicial, Economy, etc.
      
      RESPONSE: {"topics": ["Topic Name 1", "Topic Name 2"]}
```

### 3. **Updated Fact-Checking Pipeline** (`fact_check.py`)

Enhanced the pipeline to:
1. Extract topics from claim text
2. Match topics to database topics
3. Link topics to claims via many-to-many relationship
4. Log topic assignments for debugging

**New Flow:**
```
1. Extract Claim ✅
2. Search Evidence ✅
3. Verify Claim ✅
4. Extract Entities ✅
5. Extract Topics ✅ (NEW)
6. Store Claim ✅
7. Link Topics to Claim ✅ (NEW)
```

### 4. **AI Prompts Analysis Document** (`AI_PROMPTS_ANALYSIS.md`)

Created comprehensive documentation of:
- Current AI prompts used
- Issues identified
- Proposed improvements
- Implementation details

---

## 📋 How to Use

### Step 1: Seed Topics
```bash
cd backend
python seed_topics.py
```

Expected output:
```
🌱 Seeding topics...
✅ Created topic: Reforma Judicial
✅ Created topic: Ejecutivo
...
📊 Summary:
   Created: 15 topics
   Already existed: 0 topics
   Total: 15 topics
✅ Done!
```

### Step 2: Process Claims (Topics Will Be Auto-Assigned)

When new sources are processed:
- Topics are automatically extracted using AI
- Topics are linked to claims
- Claims appear in `/temas` page

### Step 3: Verify in Database

Check that topics are assigned:
```sql
SELECT c.id, c.claim_text, t.name as topic_name
FROM claims c
JOIN claim_topics ct ON c.id = ct.claim_id
JOIN topics t ON ct.topic_id = t.id
LIMIT 10;
```

### Step 4: View in Frontend

Navigate to `/temas`:
- Should show all topics with claim counts
- Click on a topic to see related claims
- Topics are automatically categorized

---

## 🔍 Algorithm Improvements

### Before:
```
Claim → Verify → Store
❌ No topic classification
❌ No topic assignment
❌ Temas page empty
```

### After:
```
Claim → Verify → Extract Topics → Link Topics → Store
✅ AI-powered topic classification
✅ Automatic topic assignment
✅ Temas page populated with data
```

---

## 🎯 Expected Results

### Temas Page (`/temas`)
- ✅ Shows all 15 topics
- ✅ Displays claim counts per topic
- ✅ Search and filter functionality
- ✅ Grid/list view options

### Topic Detail Page (`/temas/[slug]`)
- ✅ Shows all claims for that topic
- ✅ Topic-specific statistics
- ✅ Status filtering (Verified, Debunked, etc.)
- ✅ Pagination support

---

## 🐛 Troubleshooting

### Issue: Topics Not Appearing
**Solution:**
1. Run `seed_topics.py` to create topics
2. Reprocess existing claims (topics will be assigned to new claims)
3. Check logs for topic extraction errors

### Issue: Claims Not Linked to Topics
**Solution:**
1. Check AI API keys (ANTHROPIC_API_KEY or OPENAI_API_KEY)
2. Review logs: `logger.info(f"... with {len(linked_topics)} topics: {linked_topics}")`
3. Verify topics exist in database: `SELECT * FROM topics;`

### Issue: AI Not Classifying Topics Correctly
**Solution:**
1. Review `AI_PROMPTS_ANALYSIS.md` for prompt details
2. Adjust topic list in `seed_topics.py` if needed
3. Check AI response format in logs

---

## 📊 Testing

### Test Topic Extraction:
```python
from app.agent import FactChecker
import asyncio

async def test():
    checker = FactChecker()
    topics = await checker._extract_topics(
        "La reforma judicial permitirá elección popular de jueces"
    )
    print(topics)  # Should return: ["Reforma Judicial"]

asyncio.run(test())
```

### Test Full Pipeline:
1. Create a test source
2. Process it through fact-checking
3. Verify topics are assigned in database
4. Check `/temas` page displays the topic

---

## 🚀 Next Steps (Optional Enhancements)

1. **Topic Suggestions**: Allow AI to suggest new topics if none fit
2. **Topic Confidence Scores**: Add confidence levels to topic assignments
3. **Topic Trends**: Show topic popularity over time
4. **Auto-tagging**: Retroactively assign topics to existing claims
5. **Topic Merging**: Combine similar topics automatically

---

## 📝 Files Modified/Created

### Created:
- `backend/seed_topics.py` - Topic seeding script
- `backend/AI_PROMPTS_ANALYSIS.md` - Prompt documentation
- `TEMAS_IMPROVEMENTS.md` - This file

### Modified:
- `backend/app/agent.py` - Added `_extract_topics()` method
- `backend/app/tasks/fact_check.py` - Added topic extraction and linking

### Frontend (Already Complete):
- `frontend/src/app/temas/page.tsx` - Main topics page
- `frontend/src/app/temas/[slug]/page.tsx` - Topic detail page
- `frontend/src/components/TopicCard.tsx` - Topic card component

---

## ✅ Summary

**Fixed:** Topics are now automatically extracted and assigned during fact-checking
**Result:** Temas page will display topics with claims
**Impact:** Users can now browse and filter claims by topic

The algorithm now:
1. ✅ Extracts topics using AI
2. ✅ Links topics to claims
3. ✅ Populates the Temas page
4. ✅ Provides topic-based navigation

