# Scraping Issues - Action Plan

**Date:** 2025-11-25  
**Status:** Issues Identified - Action Required

---

## Current Issues Summary

Based on the scraping report:

1. **Low Coverage:** Only 8.3% (2/24 hours) - Expected 100%
2. **Missing Platforms:** Only Google News working - Twitter & YouTube not active
3. **Celery Workers:** Were crashing, now restarted

---

## Issues Found

### 1. Celery Workers Not Running Consistently ✅ FIXED
- **Problem:** Workers were crashing due to import errors
- **Status:** Workers restarted successfully
- **Action:** Monitor for next 24 hours

### 2. Twitter Scraper Not Working
- **Problem:** No Twitter sources in last 24 hours
- **Possible Causes:**
  - Twitter API credentials not configured
  - API rate limits exceeded
  - Scraper errors not being logged

**Check:**
```bash
cd backend
source venv/bin/activate
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('TWITTER_BEARER_TOKEN')
print(f'Twitter Bearer Token: {\"SET\" if key else \"NOT SET\"}')
"
```

### 3. YouTube Scraper Not Working
- **Problem:** No YouTube sources despite credentials being valid
- **Status:** ✅ Credentials verified and working
- **Possible Causes:**
  - Scraper not being called in Celery task
  - Errors during scraping not visible
  - Transcript fetching issues blocking videos

**Test:**
```bash
cd backend
source venv/bin/activate
python -c "
import asyncio
from app.scraper_youtube import YouTubeScraper

async def test():
    scraper = YouTubeScraper()
    if scraper.youtube:
        results = await scraper.fetch_posts(['México'])
        print(f'YouTube scraper found {len(results)} videos')
    else:
        print('YouTube client not initialized')

asyncio.run(test())
"
```

---

## Immediate Actions

### ✅ Completed
1. Fixed YouTube credentials (verified working)
2. Fixed environment variable loading in YouTube scraper
3. Restarted Celery workers
4. Verified worker imports successfully

### ⏳ Next Steps

1. **Monitor Worker Logs** (Next 1-2 hours)
   ```bash
   tail -f backend/worker.log
   ```
   Look for:
   - Successful hourly scraping runs
   - Any error messages
   - Twitter/YouTube scraper activity

2. **Check Twitter Credentials**
   ```bash
   cd backend
   source venv/bin/activate
   python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print('TWITTER_BEARER_TOKEN:', 'SET' if os.getenv('TWITTER_BEARER_TOKEN') else 'NOT SET')
   print('TWITTER_API_KEY:', 'SET' if os.getenv('TWITTER_API_KEY') else 'NOT SET')
   "
   ```

3. **Test Manual Scrape** (Verify all scrapers work)
   ```bash
   cd backend
   source venv/bin/activate
   python trigger_scrape.py
   ```

4. **Run Scraping Report Again** (After 24 hours)
   ```bash
   cd backend
   source venv/bin/activate
   python scraping_report.py
   ```

---

## Expected Results After Fixes

### Within 1 Hour
- ✅ Celery workers running without crashes
- ✅ At least one successful scraping run logged

### Within 24 Hours
- ✅ 24 hourly scraping runs (100% coverage)
- ✅ Sources from all 3 platforms (Google News, Twitter, YouTube)
- ✅ 50+ sources scraped (currently only 5)

---

## Troubleshooting Commands

### Check Celery Worker Status
```bash
ps aux | grep celery | grep -v grep
```

### Check Worker Logs
```bash
tail -50 backend/worker.log
```

### Check Redis Connection
```bash
redis-cli ping
```

### Test Individual Scrapers
```bash
# Test Twitter
cd backend && source venv/bin/activate
python -c "
from app.scraper import TwitterScraper
import asyncio
scraper = TwitterScraper()
results = asyncio.run(scraper.fetch_posts(['México']))
print(f'Twitter: {len(results)} posts')
"

# Test YouTube
python -c "
from app.scraper_youtube import YouTubeScraper
import asyncio
scraper = YouTubeScraper()
results = asyncio.run(scraper.fetch_posts(['México']))
print(f'YouTube: {len(results)} videos')
"
```

### Check Database for Recent Sources
```bash
cd backend && source venv/bin/activate
python -c "
from app.database import SessionLocal, Source
from datetime import datetime, timedelta, timezone
db = SessionLocal()
last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
sources = db.query(Source).filter(Source.scraped_at >= last_24h).all()
print(f'Total sources last 24h: {len(sources)}')
for platform in ['Google News', 'X (Twitter)', 'YouTube']:
    count = len([s for s in sources if s.platform == platform])
    print(f'  {platform}: {count}')
"
```

---

## Monitoring

### Real-time Monitoring
```bash
# Watch worker logs
tail -f backend/worker.log | grep -E "scrape|error|Scraped"

# Watch for new sources
watch -n 60 'cd backend && source venv/bin/activate && python -c "from app.database import SessionLocal, Source; from datetime import datetime, timedelta, timezone; db = SessionLocal(); count = db.query(Source).filter(Source.scraped_at >= datetime.now(timezone.utc) - timedelta(hours=1)).count(); print(f\"Sources last hour: {count}\")"'
```

---

## Success Criteria

✅ **Scraping is working correctly when:**
1. Hourly coverage = 100% (24/24 hours)
2. All 3 platforms active (Google News, Twitter, YouTube)
3. 50+ sources scraped per 24 hours
4. No errors in worker logs
5. Sources being processed (not stuck in "pending")

---

**Next Review:** Run `scraping_report.py` in 24 hours to verify improvements.

