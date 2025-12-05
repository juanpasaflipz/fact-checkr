# Scraping Criteria & Keyword Strategy

## Current Scraping Criteria

### How It Works

The system uses **configurable keywords** organized by priority that are searched across all platforms (Twitter, Google News, YouTube). Posts matching these keywords are collected and fact-checked.

### Keyword Configuration

**Location**: `backend/app/config/scraping_keywords.py`

Keywords are now organized by priority:
- **High Priority** (5 keywords): Always active
- **Medium Priority** (7 keywords): Core political topics
- **Low Priority** (12 keywords): Important but less frequent

**Default**: Uses High + Top 5 Medium Priority (10 keywords total)

### Current Keywords

#### High Priority (Always Active)
1. `Reforma Judicial` - Judicial reform (major current topic)
2. `Sheinbaum` - Current President
3. `Claudia Sheinbaum` - Full name variant
4. `Morena` - Ruling party
5. `política mexicana` - General Mexican politics

#### Medium Priority (Core Topics)
6. `AMLO` - Previous President
7. `López Obrador` - Full name variant
8. `Congreso México` - Mexican Congress
9. `INE` - National Electoral Institute
10. `Suprema Corte` - Supreme Court
11. `Senado México` - Senate
12. `Cámara Diputados` - Chamber of Deputies

#### Low Priority (Extended Coverage)
13. `PAN` - Opposition party
14. `PRI` - Opposition party
15. `PRD` - Opposition party
16. `Pemex` - State oil company
17. `CFE` - State electricity company
18. `Seguridad México` - Security
19. `Economía México` - Economy
20. `Corrupción México` - Corruption
21. `Migración México` - Migration
22. ... (see full list in config file)

### Search Strategy

1. **Twitter**: Searches for tweets containing any of these keywords
   - Query: `(keyword1 OR keyword2 OR ...) -is:retweet lang:es`
   - Filters: Spanish language, excludes retweets
   - Limit: Up to 112 posts per run (quota-limited)

2. **Google News**: RSS feed search
   - Query: `keyword1 OR keyword2 ... when:1d`
   - Region: Mexico (MX)
   - Language: Spanish (es-419)
   - Limit: 10 entries per query

3. **YouTube**: Video search
   - Combines keywords with additional Mexico political terms
   - Region: Mexico (MX)
   - Language: Spanish
   - Time: Last 7 days
   - Limit: 10 videos per search term (5 terms max)

---

## Current Limitations

### ❌ Static Keywords
- Keywords are hardcoded in code
- No way to add/remove keywords without code changes
- No trending topic detection
- No seasonal/temporal keyword adjustment

### ❌ Limited Coverage
- Only 7 keywords
- Missing many important political topics
- No coverage of specific issues (economy, security, etc.)
- No coverage of opposition parties

### ❌ No Prioritization
- All keywords treated equally
- No weighting for important vs. less important topics
- No dynamic adjustment based on news cycles

---

## Recommended Keyword List

### Core Political Figures

**Current Administration:**
- `Sheinbaum` - President
- `Claudia Sheinbaum` - Full name
- `AMLO` - Previous President (still relevant)
- `López Obrador` - Previous President full name

**Political Parties:**
- `Morena` - Ruling party
- `PAN` - Opposition party
- `PRI` - Opposition party
- `PRD` - Opposition party
- `Movimiento Ciudadano` - Opposition party

**Key Government Officials:**
- `Marcelo Ebrard` - Key figure
- `Ricardo Monreal` - Senate leader
- `Ernesto Cordero` - Opposition leader

### Major Political Topics

**Institutional:**
- `Reforma Judicial` - Judicial reform (current major topic)
- `Reforma Electoral` - Electoral reform
- `Suprema Corte` - Supreme Court
- `INE` - National Electoral Institute
- `Congreso México` - Congress
- `Senado México` - Senate
- `Cámara Diputados` - Chamber of Deputies

**Policy Areas:**
- `Seguridad México` - Security
- `Economía México` - Economy
- `Salud México` - Health
- `Educación México` - Education
- `Energía México` - Energy
- `Migración México` - Migration
- `Corrupción México` - Corruption

**Current Events:**
- `Elecciones México` - Elections
- `Presupuesto México` - Budget
- `Deuda pública` - Public debt
- `Pemex` - State oil company
- `CFE` - State electricity company

### General Terms

- `política mexicana` - Mexican politics
- `México política` - Mexico politics
- `gobierno México` - Mexico government
- `noticias México` - Mexico news

---

## Enhanced Keyword Strategy

### Proposed Categories

#### 1. **High Priority** (Always Active)
- Current President: `Sheinbaum`, `Claudia Sheinbaum`
- Major current topic: `Reforma Judicial`
- Ruling party: `Morena`
- General: `política mexicana`

#### 2. **Medium Priority** (Rotate Weekly)
- Opposition parties: `PAN`, `PRI`, `PRD`
- Key institutions: `INE`, `Suprema Corte`, `Congreso México`
- Policy areas: `Seguridad México`, `Economía México`

#### 3. **Trending Topics** (Dynamic)
- Detect trending topics from recent claims
- Add temporarily (e.g., for 1 week)
- Remove when trend dies down

#### 4. **Seasonal/Temporal**
- Election periods: `Elecciones México`, `votaciones`
- Budget season: `Presupuesto México`
- Specific events: Add as needed

---

## Recommended Improvements

### 1. **Configurable Keywords** (Priority: High)

Move keywords to database or config file:

```python
# backend/app/config/keywords.py
SCRAPING_KEYWORDS = {
    "high_priority": [
        "Sheinbaum",
        "Reforma Judicial",
        "Morena",
        "política mexicana"
    ],
    "medium_priority": [
        "AMLO",
        "Congreso México",
        "INE",
        "Suprema Corte"
    ],
    "low_priority": [
        "PAN",
        "PRI",
        "Seguridad México",
        "Economía México"
    ]
}
```

### 2. **Topic-Based Keywords** (Priority: Medium)

Link keywords to database topics:

```python
# Get keywords from active topics
topics = db.query(Topic).filter(Topic.is_active == True).all()
keywords = [topic.search_keywords for topic in topics]  # Each topic has search keywords
```

### 3. **Trending Topic Detection** (Priority: Medium)

- Analyze recent claims to find trending topics
- Automatically add trending keywords
- Remove after trend dies down

### 4. **Keyword Performance Tracking** (Priority: Low)

- Track which keywords produce most claims
- Track which keywords produce most verified/debunked claims
- Adjust keyword list based on performance

---

## Implementation Plan

### Phase 1: Expand Keyword List

**Immediate Action**: Add more keywords to current hardcoded list

**Recommended Keywords** (20 total):
```python
keywords = [
    # High Priority (Always)
    "Reforma Judicial",
    "Sheinbaum",
    "Claudia Sheinbaum",
    "Morena",
    "política mexicana",
    
    # Medium Priority
    "AMLO",
    "López Obrador",
    "Congreso México",
    "INE",
    "Suprema Corte",
    
    # Institutions
    "Senado México",
    "Cámara Diputados",
    "Pemex",
    "CFE",
    
    # Opposition
    "PAN",
    "PRI",
    "PRD",
    
    # Policy Areas
    "Seguridad México",
    "Economía México",
    "Corrupción México"
]
```

### Phase 2: Make Keywords Configurable

Create `backend/app/config/scraping_keywords.py`:
- Load from environment variables or config file
- Allow runtime updates
- Support different keyword sets per platform

### Phase 3: Topic-Based Keywords

- Link keywords to database topics
- Allow admins to manage keywords via API
- Support keyword rotation based on topic activity

---

## Current Search Query Examples

### Twitter Query
```
(Reforma Judicial OR Sheinbaum OR México OR Morena OR política mexicana OR AMLO OR Congreso México) -is:retweet lang:es
```

### Google News Query
```
Reforma Judicial OR Sheinbaum OR México OR Morena OR política mexicana OR AMLO OR Congreso México when:1d
```

### YouTube Query
```
política mexicana OR México política OR Sheinbaum OR AMLO OR Morena OR Reforma Judicial México OR Congreso México OR elecciones México
```

---

## Keyword Selection Criteria

### What Should Be Scraped?

1. **Factual Claims** (Not Opinions)
   - ✅ "Sheinbaum anunció X"
   - ✅ "Reforma Judicial elimina Y"
   - ❌ "Morena es malo" (opinion)
   - ❌ "AMLO debería hacer X" (opinion)

2. **Verifiable Information**
   - ✅ Specific dates, numbers, policies
   - ✅ Official statements
   - ✅ Legislative actions
   - ❌ Vague complaints
   - ❌ Personal attacks

3. **Relevant to Mexican Politics**
   - ✅ National politics
   - ✅ Federal government
   - ✅ Major institutions
   - ❌ International news (unless directly related)
   - ❌ Local politics (unless major)

4. **Current/Recent Events**
   - ✅ Last 7 days (Twitter/Google News)
   - ✅ Last 7 days (YouTube)
   - ❌ Historical events (unless trending)

---

## Recommendations

### Immediate Actions

1. **Expand keyword list** to 15-20 keywords
2. **Add opposition parties**: PAN, PRI, PRD
3. **Add key institutions**: INE, Suprema Corte, Senado
4. **Add policy areas**: Seguridad, Economía, Corrupción

### Short-term Improvements

1. **Make keywords configurable** (database or config file)
2. **Add keyword performance tracking**
3. **Create keyword management API**

### Long-term Enhancements

1. **Trending topic detection**
2. **AI-powered keyword suggestions**
3. **Dynamic keyword rotation**
4. **Platform-specific keyword optimization**

---

## Monitoring Keywords

### Metrics to Track

- **Posts per keyword**: Which keywords produce most posts?
- **Claims per keyword**: Which keywords produce most claims?
- **Verification rate**: Which keywords produce most verified/debunked claims?
- **Engagement**: Which keywords produce high-engagement posts?

### SQL Queries

```sql
-- Posts per keyword (approximate - would need keyword tracking)
SELECT platform, COUNT(*) as post_count
FROM sources
WHERE platform = 'X (Twitter)'
GROUP BY platform;

-- Claims by topic (if topics linked to keywords)
SELECT t.name, COUNT(c.id) as claim_count
FROM topics t
JOIN claim_topics ct ON t.id = ct.topic_id
JOIN claims c ON ct.claim_id = c.id
GROUP BY t.name
ORDER BY claim_count DESC;
```

---

## Next Steps

1. **Review current keywords** - Are they still relevant?
2. **Add missing keywords** - Opposition, institutions, policy areas
3. **Test expanded list** - Monitor quota usage and claim quality
4. **Make configurable** - Move to database/config file
5. **Add monitoring** - Track keyword performance

