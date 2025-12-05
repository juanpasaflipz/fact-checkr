# Data Collection Analysis & Recommendations

## Current Data Sources Overview

### 1. Twitter/X API (Basic Tier)
**Status**: ✅ Active but Limited
- **API Version**: v2 with Bearer Token
- **Current Limits**:
  - 10 tweets per query (`max_results=10`)
  - 7-day search window only
  - Basic tier: ~10,000 tweets/month quota
- **Data Collected**:
  - Tweet ID, text, author_id, timestamp, URL
- **Missing Data Points**:
  - ❌ Username (only has `author_id`, needs separate API call)
  - ❌ Engagement metrics (likes, retweets, replies, views)
  - ❌ User verification status
  - ❌ Media attachments (images, videos)
  - ❌ Thread context (replies, quote tweets)
  - ❌ User profile data (follower count, account age)
  - ❌ Geographic data
  - ❌ Historical data beyond 7 days

### 2. Google News RSS (Free)
**Status**: ✅ Active
- **Current Limits**:
  - 10 entries per query
  - 1-day search window (`when:1d`)
  - Free, no API key required
- **Data Collected**:
  - Title, summary, source, link, timestamp
- **Missing Data Points**:
  - ❌ Full article content (only title + summary)
  - ❌ Article metadata (author, word count, category)
  - ❌ Historical data beyond 1 day
  - ❌ Image thumbnails
  - ❌ Source credibility scores

### 3. YouTube Data API v3
**Status**: ✅ Active
- **Current Limits**:
  - 10 videos per search term
  - 5 search terms max
  - 7-day search window
  - Transcripts for videos < 2 hours
- **Data Collected**:
  - Video title, transcript, channel, URL, timestamp
- **Missing Data Points**:
  - ❌ View counts, engagement metrics
  - ❌ Video thumbnails
  - ❌ Channel subscriber counts
  - ❌ Comments (requires separate API calls)
  - ❌ Video duration metadata (parsed but not stored)

---

## Twitter/X API Upgrade Analysis

### Current Tier: Free
- **Monthly Quota**: 100 posts/month
- **Writes**: 500 writes/month
- **Apps**: 1 environment
- **Search Window**: 7 days (limited)
- **Features**: Very limited access

### Upgrade Option 1: Basic Tier ($175/month annual or $200/month)
**Benefits**:
- ✅ **15,000 posts/month** (150x increase from free)
- ✅ **75,000 DM requests/month per user**
- ✅ **50,000 user requests/month per user**
- ✅ **2 app environments**
- ✅ **Enhanced tweet fields**: engagement metrics, media, user data
- ✅ **Better rate limits** than free tier
- ✅ **User lookup**: Get usernames without extra calls
- ✅ **Media attachments**: Images, videos, GIFs

**ROI Analysis**:
- Current: 100 posts/month = ~3 posts/day
- Basic: 15,000 posts/month = ~500 posts/day
- **Cost per post**: $0.0117 (annual) or $0.0133 (monthly)
- **Data quality**: Significantly better with engagement metrics
- **150x volume increase** for $175-200/month

**Recommendation**: ⭐ **RECOMMENDED** (if budget allows)
- Significant volume increase (150x)
- Much more affordable than Pro tier
- Good balance of cost vs. features
- Still has limitations (no realtime stream, 15K limit)

### Upgrade Option 2: Pro Tier ($4,500/month annual or $5,000/month)
**Benefits**:
- ✅ **1,000,000 posts/month** (10,000x increase from free, 67x from Basic)
- ✅ **Over 300,000 DM requests/month per user**
- ✅ **Over 8,000,000 user requests/month per user**
- ✅ **3 app environments**
- ✅ **Realtime Posts stream**: Access to realtime posts stream
- ✅ **Full archive search** (historical data)
- ✅ **All enhanced features** from Basic tier

**ROI Analysis**:
- Current: 100 posts/month
- Pro: 1,000,000 posts/month = ~33,333 posts/day
- **Cost per post**: $0.0045 (annual) or $0.005 (monthly)
- **Much better cost efficiency** than Basic tier
- **Realtime streaming** enables instant fact-checking

**Recommendation**: ⚠️ **ONLY IF SCALE JUSTIFIES**
- Very expensive ($4,500-5,000/month)
- Only worth it if you're processing 100K+ posts/month
- Consider when revenue > $50k/month
- Realtime stream is powerful but requires infrastructure

---

## Additional Data Sources to Add

### High Priority (Implement First)

#### 1. **Reddit API** (Free)
- **Why**: High-quality political discussions, AMAs, fact-checking communities
- **Data Points**: Post content, upvotes, comments, subreddit, author karma
- **Implementation**: `praw` library (Python Reddit API Wrapper)
- **Cost**: Free (with rate limits)
- **Mexican Politics Subreddits**: r/mexico, r/politica, r/mexicopolitico

#### 2. **NewsAPI.org** ($449/month for Business)
- **Why**: Access to 80,000+ news sources, full article content
- **Data Points**: Full articles, authors, images, categories
- **Mexican Sources**: 50+ major Mexican news outlets
- **Alternative**: Use individual news site APIs (free but more complex)

#### 3. **Facebook Graph API** (Free with limits)
- **Why**: Major platform for political content in Mexico
- **Data Points**: Public posts, engagement, page info
- **Limitations**: Requires app review, limited public data access
- **Note**: Meta has restricted API access significantly

#### 4. **Telegram Channels** (Free via Bot API)
- **Why**: Popular for political news in Mexico
- **Data Points**: Channel posts, views, forwards
- **Implementation**: Telegram Bot API
- **Cost**: Free

### Medium Priority

#### 5. **TikTok Research API** (Paid, requires approval)
- **Why**: Growing platform for political content
- **Data Points**: Video metadata, captions, engagement
- **Cost**: Custom pricing
- **Note**: Requires research partnership application

#### 6. **Instagram Basic Display API** (Free)
- **Why**: Visual political content
- **Data Points**: Public posts, captions, engagement
- **Limitations**: Very limited public data access

#### 7. **Mastodon/Fediverse** (Free)
- **Why**: Alternative social platform gaining traction
- **Data Points**: Posts, boosts, favorites
- **Implementation**: Mastodon API (open source)

### Low Priority (Future)

#### 8. **WhatsApp Business API** (Paid)
- **Why**: Popular messaging platform in Mexico
- **Limitations**: Requires business verification, limited public data
- **Use Case**: Fact-checking bot integration

#### 9. **LinkedIn API** (Paid)
- **Why**: Professional political commentary
- **Data Points**: Posts, engagement, author info
- **Cost**: LinkedIn Marketing API pricing

---

## Enhanced Data Points to Collect

### For All Sources

#### Engagement Metrics
```python
engagement_metrics = {
    "likes": int,
    "shares": int,
    "comments": int,
    "views": int,
    "retweets": int,  # Twitter-specific
    "upvotes": int,   # Reddit-specific
    "engagement_rate": float  # Calculated
}
```

#### User/Author Metadata
```python
author_metadata = {
    "username": str,
    "display_name": str,
    "verified": bool,
    "follower_count": int,
    "account_created": datetime,
    "bio": str,
    "location": str
}
```

#### Media Attachments
```python
media = {
    "images": List[str],  # URLs
    "videos": List[str],  # URLs
    "thumbnails": List[str]
}
```

#### Context Data
```python
context = {
    "thread_id": str,  # For Twitter threads
    "parent_id": str,   # For replies
    "is_reply": bool,
    "is_retweet": bool,
    "quote_tweet_id": str
}
```

#### Source Credibility
```python
credibility = {
    "source_domain": str,
    "source_reliability_score": float,  # Based on whitelist
    "fact_check_history": int,  # Previous fact-checks from this source
    "accuracy_rate": float  # Historical accuracy
}
```

---

## Implementation Recommendations

### Phase 1: Immediate (Week 1-2)
1. ✅ **Upgrade Twitter to Pro Tier**
   - Cost: $100/month
   - Impact: 100x more data, 30-day window, engagement metrics
   - Implementation: Update `TwitterScraper` to use enhanced fields

2. ✅ **Add Reddit Scraper**
   - Cost: Free
   - Impact: High-quality political discussions
   - Implementation: Create `RedditScraper` class

3. ✅ **Enhance Data Models**
   - Add `engagement_metrics` JSON field to `Source` model
   - Add `author_metadata` JSON field
   - Add `media_urls` JSON field

### Phase 2: Short-term (Month 1)
4. ✅ **NewsAPI Integration**
   - Cost: $449/month (Business tier)
   - Impact: Full article content from 50+ Mexican sources
   - Alternative: Scrape individual news sites (free but complex)

5. ✅ **Telegram Channel Monitor**
   - Cost: Free
   - Impact: Real-time political news channels
   - Implementation: Telegram Bot API

6. ✅ **Enhanced Twitter Data Collection**
   - Collect engagement metrics
   - Collect user metadata
   - Collect media attachments
   - Collect thread context

### Phase 3: Medium-term (Month 2-3)
7. ✅ **Facebook Public Page Monitor**
   - Cost: Free (with limitations)
   - Impact: Major political pages and public figures

8. ✅ **Historical Data Backfill**
   - Use Twitter Pro full archive search
   - Backfill last 30 days of data
   - Build historical trend analysis

9. ✅ **Source Credibility Scoring**
   - Implement reliability scoring
   - Track historical accuracy
   - Weight fact-checks by source credibility

### Phase 4: Long-term (Month 4+)
10. ✅ **TikTok Research API** (if approved)
11. ✅ **WhatsApp Fact-Checking Bot**
12. ✅ **Real-time Streaming** (Twitter Enterprise if scale justifies)

---

## Cost-Benefit Analysis

### Current Monthly Costs
- Twitter Free: $0
- Google News RSS: $0
- YouTube API: $0 (within free tier)
- **Total**: $0/month

### Recommended Monthly Costs (Option 1: Budget-Conscious)
- Twitter Basic: $175/month (annual) or $200/month
- Reddit API: $0
- Telegram API: $0
- Individual news scrapers: $0 (more dev work)
- **Total**: $175-200/month

### Recommended Monthly Costs (Option 2: Full Suite)
- Twitter Basic: $175/month (annual)
- NewsAPI Business: $449/month (or free alternative)
- Reddit API: $0
- Telegram API: $0
- **Total**: $624/month (or $175/month with free alternatives)

### Recommended Monthly Costs (Option 3: Maximum Scale)
- Twitter Pro: $4,500/month (annual) or $5,000/month
- NewsAPI Business: $449/month
- Reddit API: $0
- Telegram API: $0
- **Total**: $4,949-5,449/month

### ROI Justification

**Twitter Basic ($175-200/month)**:
- **Data Volume**: 150x increase (15K vs 100 posts/month)
- **Data Quality**: Engagement metrics enable better fact-checking
- **Cost Efficiency**: $0.0117 per post (annual pricing)
- **Source Diversity**: Multiple platforms reduce bias
- **User Value**: Better data = better verifications = more subscriptions

**Twitter Pro ($4,500-5,000/month)**:
- **Data Volume**: 10,000x increase (1M vs 100 posts/month)
- **Realtime Streaming**: Instant fact-checking capability
- **Cost Efficiency**: $0.0045 per post (much better than Basic)
- **Only justified if**: Processing 100K+ posts/month or need realtime

### Alternative: Free Tier Strategy
If budget is constrained:
1. Keep Twitter Free (100 posts/month - very limited)
2. Add Reddit (free, unlimited with rate limits)
3. Add Telegram (free)
4. Scrape individual news sites (free, more complex)
5. **Total**: $0/month, but very limited Twitter data

---

## Technical Implementation Notes

### Database Schema Updates Needed

```python
# Add to Source model
engagement_metrics = Column(JSON)  # likes, shares, views, etc.
author_metadata = Column(JSON)     # username, verified, followers, etc.
media_urls = Column(JSON)          # images, videos, thumbnails
context_data = Column(JSON)        # thread_id, parent_id, is_reply, etc.
credibility_score = Column(Float)   # Source reliability score
```

### Scraper Architecture Updates

1. **Enhanced TwitterScraper**
   - Use `expansions` parameter for user data
   - Use `tweet.fields` for engagement metrics
   - Use `media.fields` for attachments
   - Batch user lookups for efficiency

2. **New RedditScraper**
   - Use `praw` library
   - Monitor specific subreddits
   - Collect upvotes, comments, awards

3. **NewsAPI Scraper**
   - Full article content
   - Source metadata
   - Image thumbnails

### Rate Limiting & Quota Management

- Implement quota tracking per API
- Prioritize high-value sources
- Cache responses to reduce API calls
- Implement exponential backoff for rate limits

---

## Success Metrics

### Data Collection KPIs
- **Daily Sources Collected**: Target 1,000+ (currently ~50-100)
- **Source Diversity**: 5+ platforms (currently 3)
- **Historical Coverage**: 30 days (currently 7)
- **Engagement Data**: 80%+ of sources (currently 0%)
- **Media Attachments**: 30%+ of sources (currently 0%)

### Quality Metrics
- **Source Credibility**: Average score > 0.7
- **Data Completeness**: 90%+ of sources have all metadata
- **Duplicate Detection**: < 5% duplicates

---

## Next Steps

1. **Immediate**: Upgrade Twitter to Pro tier ($100/month)
2. **This Week**: Implement Reddit scraper (free)
3. **This Month**: Add NewsAPI or individual news scrapers
4. **Next Month**: Enhance data models and backfill historical data

---

## Questions to Consider

1. **Budget**: Can we afford $549/month for data collection?
2. **Priority**: Which platforms are most important for Mexican politics?
3. **Scale**: How much data do we actually need?
4. **Quality vs Quantity**: Better to have less but higher quality data?

---

## Conclusion

**Recommended Action Plan**:
1. ✅ **Upgrade Twitter to Basic** ($175-200/month) - 150x volume increase, affordable
2. ✅ **Add Reddit** - Free, high-quality political content
3. ✅ **Enhance data models** - Store engagement metrics and metadata
4. ⚠️ **NewsAPI** - Consider if budget allows ($449/month), or use free alternatives
5. 📅 **Plan for Telegram** - Easy win, free, real-time
6. 🚀 **Consider Twitter Pro later** - Only if scale justifies $4,500-5,000/month

**Total Investment**: $175-624/month (Basic tier) or $4,949-5,449/month (Pro tier)
**Expected Impact**: 
- Basic tier: 150x increase in Twitter data volume
- Pro tier: 10,000x increase + realtime streaming

