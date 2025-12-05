# Data Collection Quick Reference

## Current Status

### Active Sources
- ✅ **Twitter/X** - Basic tier (10 tweets/query, 7-day window)
- ✅ **Google News RSS** - Free (10 entries/query, 1-day window)
- ✅ **YouTube** - Free tier (10 videos/search, transcripts)

### Data Volume
- **Current**: ~50-100 sources/day
- **Target**: 1,000+ sources/day

---

## Immediate Recommendations

### 1. Upgrade Twitter to Basic Tier ⭐ **HIGHEST PRIORITY**
- **Cost**: $175/month (annual) or $200/month (monthly)
- **Benefits**:
  - 150x more data (15K posts/month vs 100 on free)
  - Engagement metrics (likes, retweets, views)
  - User metadata (username, verified status, followers)
  - Media attachments (images, videos)
  - 75K DM requests/month, 50K user requests/month

**Alternative: Pro Tier** ($4,500-5,000/month):
- 1M posts/month (10,000x increase from free)
- Realtime streaming API
- Only if scale justifies the cost

**Action**: Upgrade at https://developer.x.com/en/portal/products

### 2. Add Reddit Scraper ⭐ **FREE & EASY**
- **Cost**: $0
- **Benefits**:
  - High-quality political discussions
  - Engagement metrics (upvotes, comments)
  - Free API access
  - Easy to implement

**Action**: See `DATA_COLLECTION_IMPLEMENTATION.md` for code

### 3. Enhance Data Models
- Add `engagement_metrics` JSON field
- Add `author_metadata` JSON field
- Add `media_urls` JSON field
- Add `credibility_score` field

**Action**: Create Alembic migration

---

## Cost Comparison

| Option | Monthly Cost | Data Volume | Quality |
|--------|-------------|-------------|---------|
| **Current (Free)** | $0 | ~100 posts/month | Very Low |
| **Twitter Basic + Reddit** | $175-200 | ~15K posts/month | High |
| **Twitter Pro + Reddit** | $4,500-5,000 | ~1M posts/month | Very High |
| **Full Suite (Basic)** | $624 | ~15K posts + news | Very High |
| **Full Suite (Pro)** | $4,949-5,449 | ~1M posts + news | Maximum |

---

## Missing Data Points (Current)

### Twitter
- ❌ Engagement metrics (likes, retweets, views)
- ❌ Username (only has author_id)
- ❌ User verification status
- ❌ Media attachments
- ❌ Thread context

### All Sources
- ❌ Historical data beyond 7 days
- ❌ Source credibility scores
- ❌ Full article content (Google News only has summary)

---

## Quick Wins (Free)

1. ✅ **Reddit** - Add scraper (free API)
2. ✅ **Telegram** - Monitor channels (free Bot API)
3. ✅ **Enhanced Google News** - Scrape full articles from RSS links
4. ✅ **Mastodon** - Alternative social platform (free API)

---

## Implementation Priority

### Week 1
1. Upgrade Twitter to Pro
2. Update TwitterScraper to collect enhanced data
3. Add database fields for new data points

### Week 2
4. Implement Reddit scraper
5. Test and deploy

### Month 1
6. Add NewsAPI or individual news scrapers
7. Add Telegram channel monitoring
8. Backfill historical data (30 days)

---

## Key Metrics to Track

- **Daily Sources**: Target 1,000+
- **Platforms**: Target 5+ (currently 3)
- **Data Completeness**: Target 90%+ with all metadata
- **Engagement Data**: Target 80%+ of sources
- **Historical Coverage**: 30 days (currently 7)

---

## Questions?

See full analysis in:
- `DATA_COLLECTION_ANALYSIS.md` - Detailed analysis
- `DATA_COLLECTION_IMPLEMENTATION.md` - Code examples

---

## Decision Matrix

**If budget is tight ($0-200/month)**:
- Keep Twitter Free (very limited - 100 posts/month)
- Add Reddit (free)
- Add Telegram (free)
- Scrape individual news sites (free, more work)
- **Total**: $0/month

**If budget allows ($200-700/month)**:
- Upgrade Twitter to Basic ($175-200/month)
- Add Reddit (free)
- Add NewsAPI Business ($449) OR scrape individual sites (free)
- Add Telegram (free)
- **Total**: $175-624/month

**If budget is unlimited ($5,000+/month)**:
- Twitter Pro ($4,500-5,000/month)
- NewsAPI Business ($449)
- TikTok Research API (if approved)
- All free sources (Reddit, Telegram, Mastodon)
- **Total**: $5,000+/month

---

## ROI Justification

**Twitter Basic ($175-200/month)**:
- 150x more data (15K vs 100 posts/month) = better fact-checking coverage
- Engagement metrics = identify viral misinformation faster
- Better data quality = more accurate verifications = more user trust
- Affordable upgrade path

**Twitter Pro ($4,500-5,000/month)**:
- 10,000x more data (1M vs 100 posts/month)
- Realtime streaming = instant fact-checking
- Only justified if processing 100K+ posts/month

**Expected Impact (Basic tier)**:
- 150x increase in Twitter data volume
- Better verification accuracy
- Faster detection of trending claims
- Cost-effective upgrade

