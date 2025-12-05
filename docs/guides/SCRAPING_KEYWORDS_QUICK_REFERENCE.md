# Scraping Keywords - Quick Reference

## Current Scraping Criteria

### Decision Process

**How we decide what to scrape:**
1. **Hardcoded keywords** (now configurable) - Fixed list of important terms
2. **All platforms use same keywords** - Twitter, Google News, YouTube
3. **No dynamic selection** - Keywords don't change based on trends
4. **No topic-based selection** - Not linked to database topics yet

### Main Topics Covered

Based on the keyword list, we cover:

1. **Current Administration**
   - President: Sheinbaum
   - Ruling Party: Morena

2. **Major Current Topic**
   - Reforma Judicial (Judicial Reform)

3. **Key Institutions**
   - Congreso México (Congress)
   - INE (Electoral Institute)
   - Suprema Corte (Supreme Court)

4. **General Politics**
   - política mexicana (Mexican politics)

---

## Complete Keyword List

### High Priority (Always Active) - 5 keywords
```
1. Reforma Judicial
2. Sheinbaum
3. Claudia Sheinbaum
4. Morena
5. política mexicana
```

### Medium Priority (Core Topics) - 7 keywords
```
6. AMLO
7. López Obrador
8. Congreso México
9. INE
10. Suprema Corte
11. Senado México
12. Cámara Diputados
```

### Low Priority (Extended) - 12 keywords
```
13. PAN
14. PRI
15. PRD
16. Movimiento Ciudadano
17. Pemex
18. CFE
19. Banco de México
20. SHCP
21. Seguridad México
22. Economía México
23. Corrupción México
24. Migración México
```

**Total: 24 keywords** (10 used by default)

---

## How Keywords Are Used

### Twitter Search
```
Query: (keyword1 OR keyword2 OR ...) -is:retweet lang:es
- Language: Spanish only
- Excludes: Retweets
- Limit: Up to 112 posts per run (quota-limited)
```

### Google News Search
```
Query: keyword1 OR keyword2 ... when:1d
- Region: Mexico (MX)
- Language: Spanish (es-419)
- Time: Last 1 day
- Limit: 10 entries per query
```

### YouTube Search
```
Query: keyword + "política México"
- Region: Mexico (MX)
- Language: Spanish
- Time: Last 7 days
- Limit: 10 videos per search term
```

---

## API Endpoints

### View Keywords
```
GET /api/keywords/
GET /api/keywords/?priority=high
GET /api/keywords/?categories=executive,judicial
GET /api/keywords/statistics
GET /api/keywords/categories
```

### Examples

**Get all keywords:**
```bash
curl http://localhost:8000/api/keywords/
```

**Get high priority only:**
```bash
curl http://localhost:8000/api/keywords/?priority=high
```

**Get keywords by category:**
```bash
curl http://localhost:8000/api/keywords/?categories=executive,judicial
```

---

## Configuration

### Environment Variable

Control keyword priority via environment variable:

```bash
# In backend/.env
SCRAPING_KEYWORD_PRIORITY=high      # Only high priority (5 keywords)
SCRAPING_KEYWORD_PRIORITY=medium     # High + medium (12 keywords)
SCRAPING_KEYWORD_PRIORITY=low        # All priorities (24 keywords)
SCRAPING_KEYWORD_PRIORITY=all        # All keywords (24 keywords)
SCRAPING_KEYWORD_PRIORITY=default    # High + top 5 medium (10 keywords) - DEFAULT
```

---

## Keyword Categories

Keywords are organized by category for topic-based scraping:

- **executive**: Sheinbaum, AMLO, gobierno México
- **judicial**: Reforma Judicial, Suprema Corte, jueces
- **legislative**: Congreso, Senado, Cámara Diputados
- **parties**: Morena, PAN, PRI, PRD
- **institutions**: INE, Pemex, CFE, Banco de México
- **policy**: Seguridad, Economía, Salud, Educación, Corrupción
- **elections**: elecciones, INE, votaciones

---

## Recommendations

### Current State
- ✅ **Good**: Covers major current topics
- ⚠️ **Limited**: Only 7-10 keywords active
- ⚠️ **Static**: No dynamic keyword adjustment
- ⚠️ **Missing**: Opposition parties, policy areas

### Suggested Improvements

1. **Expand to 15-20 keywords** (add opposition, institutions, policy)
2. **Link to database topics** (use topic keywords dynamically)
3. **Add trending detection** (temporarily add trending keywords)
4. **Track keyword performance** (which keywords produce best claims?)

---

## Quick Answers

**Q: What are the main topics?**
A: Current administration (Sheinbaum, Morena), Judicial Reform, Congress, and general Mexican politics.

**Q: How do you decide what to scrape?**
A: Fixed keyword list - posts matching any keyword are scraped. No dynamic selection yet.

**Q: Can you provide a list of key terms?**
A: Yes - see above. 24 total keywords organized by priority. Default uses 10.

**Q: Are keywords configurable?**
A: Yes - via `SCRAPING_KEYWORD_PRIORITY` environment variable or API endpoints.

