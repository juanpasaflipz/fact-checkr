# Twitter Scraping Schedule Configuration

## ✅ Implementation Summary

### Schedule Configuration
- **Frequency**: 4 times per day (every 6 hours)
- **Times**: 
  - 6:00 AM (Mexico City time)
  - 12:00 PM (noon)
  - 6:00 PM
  - 12:00 AM (midnight)
- **Timezone**: America/Mexico_City

### Quota Management
- **Monthly Quota**: 15,000 posts (Twitter Basic tier)
- **Daily Quota**: ~500 posts/day (15,000 / 30 days)
- **Per-Run Limit**: ~112 posts per run (with 10% safety margin)
- **Safety Margin**: 90% of quota to leave buffer

### Automatic Quota Tracking
- Tracks Twitter posts collected in current month
- Automatically limits `max_results` based on remaining quota
- Skips Twitter scraping if quota exhausted
- Logs quota usage and warnings

---

## Configuration Details

### Celery Beat Schedule

The schedule is configured in `backend/app/worker.py`:

```python
beat_schedule={
    "scrape-twitter-6am": {
        "task": "app.tasks.scraper.scrape_all_sources",
        "schedule": crontab(hour=6, minute=0),  # 6:00 AM
    },
    "scrape-twitter-12pm": {
        "task": "app.tasks.scraper.scrape_all_sources",
        "schedule": crontab(hour=12, minute=0),  # 12:00 PM
    },
    "scrape-twitter-6pm": {
        "task": "app.tasks.scraper.scrape_all_sources",
        "schedule": crontab(hour=18, minute=0),  # 6:00 PM
    },
    "scrape-twitter-midnight": {
        "task": "app.tasks.scraper.scrape_all_sources",
        "schedule": crontab(hour=0, minute=0),  # 12:00 AM
    },
}
```

### Quota Manager

New service: `backend/app/services/quota_manager.py`

**Features**:
- Tracks monthly usage from database
- Calculates remaining quota
- Enforces per-run limits
- Provides quota status API

**Usage**:
```python
from app.services.quota_manager import quota_manager

# Check if we can fetch posts
can_fetch, allowed_count = quota_manager.can_fetch_posts(100, db)

# Get quota status
status = quota_manager.get_quota_status(db)
```

---

## Quota Calculations

### Monthly Distribution
- **Total Quota**: 15,000 posts/month
- **Days per Month**: 30 (average)
- **Daily Quota**: 500 posts/day
- **Runs per Day**: 4
- **Posts per Run**: 125 posts (theoretical)
- **Safe Posts per Run**: 112 posts (90% safety margin)

### Why Safety Margin?
- Accounts for variations in month length (28-31 days)
- Leaves buffer for unexpected spikes
- Prevents quota exhaustion mid-month
- Allows for manual/emergency scraping if needed

---

## API Endpoints

### Quota Status
```
GET /api/quota/twitter
```

**Response**:
```json
{
  "monthly_quota": 15000,
  "used": 3250,
  "remaining": 11750,
  "percentage_used": 21.67,
  "posts_per_run": 112,
  "runs_per_day": 4,
  "daily_quota": 500,
  "status": "ok"
}
```

### Usage Details
```
GET /api/quota/twitter/usage
```

**Response**:
```json
{
  "used": 3250,
  "remaining": 11750,
  "percentage_used": 21.67,
  "monthly_quota": 15000,
  "posts_per_run": 112
}
```

---

## How It Works

### 1. Before Each Scrape
- Quota manager checks current month's usage
- Calculates remaining quota
- Determines max posts allowed for this run
- Limits `max_results` parameter

### 2. During Scrape
- Twitter scraper receives quota-limited `max_results`
- Fetches up to allowed number of posts
- Logs quota usage and warnings

### 3. After Scrape
- Posts stored in database
- Quota usage automatically tracked (counted from database)
- Next run will see updated usage

### 4. Quota Exhausted
- If quota exhausted, Twitter scraping is skipped
- Other sources (Google News, YouTube) still run
- Warning logged
- Status API shows "critical" status

---

## Monitoring

### Log Messages
- `"Twitter quota: X/15000 (Y% used). Fetching up to Z posts."`
- `"Quota limit: requested X, allowed Y (remaining: Z, per-run limit: W)"`
- `"Twitter quota exhausted. Skipping fetch."`

### Status Levels
- **"ok"**: < 80% used
- **"warning"**: 80-95% used
- **"critical"**: > 95% used

---

## Testing

### Check Schedule
```bash
# View Celery beat schedule
celery -A app.worker beat --loglevel=info --dry-run
```

### Check Quota Status
```bash
# Via API
curl http://localhost:8000/api/quota/twitter

# Or via Python
python -c "
from app.services.quota_manager import quota_manager
from app.database.connection import SessionLocal
db = SessionLocal()
status = quota_manager.get_quota_status(db)
print(status)
"
```

### Test Quota Limit
```python
from app.services.quota_manager import quota_manager
from app.database.connection import SessionLocal

db = SessionLocal()
can_fetch, allowed = quota_manager.can_fetch_posts(100, db)
print(f"Can fetch: {can_fetch}, Allowed: {allowed}")
```

---

## Troubleshooting

### Issue: Scraping not running at scheduled times
- **Check**: Celery beat is running
- **Check**: Timezone is set to "America/Mexico_City"
- **Check**: Beat schedule file exists and is writable

### Issue: Quota exhausted too early
- **Check**: Actual usage via `/api/quota/twitter`
- **Check**: No duplicate scraping tasks
- **Check**: Safety margin is working (should be ~90%)

### Issue: Not enough posts per run
- **Current**: ~112 posts per run (safe limit)
- **Maximum**: Can increase to 125 if needed (removes safety margin)
- **Trade-off**: Less buffer, higher risk of quota exhaustion

---

## Adjusting Limits

### Change Posts per Run
Edit `backend/app/services/quota_manager.py`:
```python
SAFETY_MARGIN = 0.9  # Change to 1.0 to use full quota
SAFE_POSTS_PER_RUN = int(TWITTER_POSTS_PER_RUN * SAFETY_MARGIN)
```

### Change Schedule Times
Edit `backend/app/worker.py`:
```python
"scrape-twitter-6am": {
    "schedule": crontab(hour=6, minute=0),  # Change hour/minute
}
```

### Change Monthly Quota
Edit `backend/app/services/quota_manager.py`:
```python
TWITTER_MONTHLY_QUOTA = 15000  # Update if tier changes
```

---

## Files Modified

1. `backend/app/worker.py` - Updated beat schedule to crontab format
2. `backend/app/scraper.py` - Added quota checking and max_results parameter
3. `backend/app/tasks/scraper.py` - Integrated quota management
4. `backend/app/services/quota_manager.py` - New quota management service
5. `backend/app/routers/quota.py` - New quota status API
6. `backend/main.py` - Added quota router

---

## Next Steps

1. **Restart Celery Beat** to apply new schedule
2. **Monitor quota usage** via API endpoints
3. **Adjust limits** if needed based on actual usage
4. **Set up alerts** for quota warnings (>80% used)

---

## Expected Behavior

### Daily Pattern
- **6 AM**: Scrapes up to 112 posts
- **12 PM**: Scrapes up to 112 posts
- **6 PM**: Scrapes up to 112 posts
- **Midnight**: Scrapes up to 112 posts
- **Total**: ~448 posts/day (well under 500/day limit)

### Monthly Pattern
- **Week 1**: ~3,136 posts (22% of quota)
- **Week 2**: ~6,272 posts (42% of quota)
- **Week 3**: ~9,408 posts (63% of quota)
- **Week 4**: ~12,544 posts (84% of quota)
- **Buffer**: ~2,456 posts remaining (16% safety margin)

This ensures we never exceed the 15,000 posts/month limit while maintaining consistent data collection throughout the month.

