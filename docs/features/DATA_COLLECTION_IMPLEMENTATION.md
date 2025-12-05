# Data Collection Implementation Guide

## Quick Start: Twitter Pro Upgrade

### Step 1: Upgrade Twitter API Access

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Navigate to your app settings
3. Upgrade to **Pro** tier ($100/month)
4. Update your API keys if needed

### Step 2: Update TwitterScraper

The current implementation only collects basic data. Here's what needs to be enhanced:

**Current Limitations**:
- Only 10 tweets per query
- No engagement metrics
- No user metadata (only author_id)
- No media attachments

**Enhanced Implementation**:

```python
# Enhanced Twitter API v2 query with expansions
response = self.client.search_recent_tweets(
    query=query,
    max_results=100,  # Pro tier allows up to 100
    tweet_fields=[
        "created_at", 
        "author_id", 
        "id", 
        "text",
        "public_metrics",  # likes, retweets, replies, quotes
        "attachments",     # media keys
        "context_annotations",
        "geo",
        "lang"
    ],
    expansions=[
        "author_id",       # Get user data
        "attachments.media_keys"  # Get media data
    ],
    user_fields=[
        "username",
        "name",
        "verified",
        "public_metrics",  # follower_count, following_count
        "created_at",
        "description",
        "location"
    ],
    media_fields=[
        "type",
        "url",
        "preview_image_url",
        "variants"  # For videos
    ]
)
```

### Step 3: Update Data Model

Add new fields to `Source` model in `backend/app/database/models.py`:

```python
class Source(Base):
    # ... existing fields ...
    
    # New fields for enhanced data
    engagement_metrics = Column(JSON)  # {likes, retweets, replies, views}
    author_metadata = Column(JSON)     # {username, verified, followers, etc.}
    media_urls = Column(JSON)          # [image_urls, video_urls]
    context_data = Column(JSON)        # {thread_id, parent_id, is_reply}
    credibility_score = Column(Float, default=0.5)
```

---

## Reddit Scraper Implementation

### Step 1: Install Dependencies

```bash
cd backend
pip install praw python-dotenv
```

### Step 2: Get Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Create a new app (script type)
3. Get: `client_id`, `client_secret`, `user_agent`

### Step 3: Add to Environment Variables

```bash
# backend/.env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=fact-checkr/1.0 (by /u/yourusername)
```

### Step 4: Create RedditScraper

Create `backend/app/scraper_reddit.py`:

```python
import os
import praw
from typing import List
from datetime import datetime
from app.models import SocialPost
import logging

logger = logging.getLogger(__name__)

class RedditScraper:
    """Scraper for Reddit posts focused on Mexico political content"""
    
    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "fact-checkr/1.0")
        
        self.reddit = None
        if self.client_id and self.client_secret:
            try:
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
            except Exception as e:
                logger.error(f"Failed to initialize Reddit API: {e}")
        else:
            logger.warning("Reddit credentials not found. Reddit scraping will be disabled.")
    
    async def fetch_posts(self, keywords: List[str]) -> List[SocialPost]:
        """Fetch Reddit posts matching keywords"""
        if not self.reddit:
            return []
        
        posts = []
        
        # Mexico political subreddits
        subreddits = [
            "mexico",
            "politica",
            "mexicopolitico",
            "MexicoNews"
        ]
        
        # Combine keywords into search query
        query = " OR ".join(keywords)
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for posts from last 7 days
                for submission in subreddit.search(
                    query,
                    sort="new",
                    time_filter="week",
                    limit=10
                ):
                    # Skip if too old (Reddit search can be imprecise)
                    post_age = datetime.utcnow() - datetime.fromtimestamp(submission.created_utc)
                    if post_age.days > 7:
                        continue
                    
                    # Combine title and selftext
                    content = submission.title
                    if submission.selftext:
                        content += f"\n\n{submission.selftext}"
                    
                    # Truncate if too long
                    if len(content) > 2000:
                        content = content[:2000] + "..."
                    
                    post = SocialPost(
                        id=f"reddit_{submission.id}",
                        platform="Reddit",
                        content=content,
                        author=f"u/{submission.author.name}" if submission.author else "Unknown",
                        timestamp=datetime.fromtimestamp(submission.created_utc).isoformat(),
                        url=f"https://reddit.com{submission.permalink}"
                    )
                    
                    posts.append(post)
                    
            except Exception as e:
                logger.error(f"Error fetching from r/{subreddit_name}: {e}")
                continue
        
        # Remove duplicates
        seen_ids = set()
        unique_posts = []
        for post in posts:
            if post.id not in seen_ids:
                seen_ids.add(post.id)
                unique_posts.append(post)
        
        logger.info(f"Fetched {len(unique_posts)} Reddit posts")
        return unique_posts
```

### Step 5: Integrate Reddit Scraper

Update `backend/app/scraper.py`:

```python
# Add import
try:
    from app.scraper_reddit import RedditScraper
except ImportError:
    RedditScraper = None
```

Update `backend/app/tasks/scraper.py`:

```python
# Add Reddit scraper
try:
    from app.scraper_reddit import RedditScraper
    REDDIT_AVAILABLE = True
except ImportError:
    REDDIT_AVAILABLE = False

async def fetch_and_store(keywords):
    # ... existing code ...
    
    reddit = RedditScraper() if REDDIT_AVAILABLE else None
    
    tasks = [
        twitter.fetch_posts(keywords),
        google.fetch_posts(keywords),
    ]
    
    if youtube:
        tasks.append(youtube.fetch_posts(keywords))
    
    if reddit:
        tasks.append(reddit.fetch_posts(keywords))
    
    # ... rest of code ...
```

---

## Enhanced Data Collection

### Update Source Model

Add migration for new fields:

```python
# alembic/versions/xxx_add_enhanced_source_fields.py
def upgrade():
    op.add_column('sources', sa.Column('engagement_metrics', sa.JSON(), nullable=True))
    op.add_column('sources', sa.Column('author_metadata', sa.JSON(), nullable=True))
    op.add_column('sources', sa.Column('media_urls', sa.JSON(), nullable=True))
    op.add_column('sources', sa.Column('context_data', sa.JSON(), nullable=True))
    op.add_column('sources', sa.Column('credibility_score', sa.Float(), nullable=True, server_default='0.5'))
```

### Update TwitterScraper to Collect Enhanced Data

```python
# In TwitterScraper.fetch_posts()
if response.data:
    # Get expanded data
    users = {u.id: u for u in response.includes.get('users', [])} if response.includes else {}
    media = {m.media_key: m for m in response.includes.get('media', [])} if response.includes else {}
    
    for tweet in response.data:
        author = users.get(tweet.author_id)
        tweet_media = []
        
        # Extract media URLs
        if hasattr(tweet, 'attachments') and tweet.attachments:
            for media_key in tweet.attachments.get('media_keys', []):
                if media_key in media:
                    m = media[media_key]
                    if hasattr(m, 'url'):
                        tweet_media.append(m.url)
                    elif hasattr(m, 'preview_image_url'):
                        tweet_media.append(m.preview_image_url)
        
        # Build engagement metrics
        engagement = {}
        if hasattr(tweet, 'public_metrics'):
            engagement = {
                "likes": tweet.public_metrics.get('like_count', 0),
                "retweets": tweet.public_metrics.get('retweet_count', 0),
                "replies": tweet.public_metrics.get('reply_count', 0),
                "quotes": tweet.public_metrics.get('quote_count', 0),
                "views": tweet.public_metrics.get('impression_count', 0) if hasattr(tweet.public_metrics, 'impression_count') else 0
            }
        
        # Build author metadata
        author_meta = {}
        if author:
            author_meta = {
                "username": author.username,
                "display_name": author.name,
                "verified": author.verified if hasattr(author, 'verified') else False,
                "follower_count": author.public_metrics.get('followers_count', 0) if hasattr(author, 'public_metrics') else 0,
                "account_created": author.created_at.isoformat() if hasattr(author, 'created_at') and author.created_at else None,
                "bio": author.description if hasattr(author, 'description') else None,
                "location": author.location if hasattr(author, 'location') else None
            }
        
        # Create enhanced source
        source = Source(
            id=str(tweet.id),
            platform="X (Twitter)",
            content=tweet.text,
            author=author.username if author else f"user_{tweet.author_id}",
            url=f"https://twitter.com/{author.username if author else 'user'}/status/{tweet.id}",
            timestamp=tweet.created_at.isoformat() if tweet.created_at else datetime.now().isoformat(),
            engagement_metrics=engagement,
            author_metadata=author_meta,
            media_urls=tweet_media,
            context_data={
                "is_reply": hasattr(tweet, 'in_reply_to_user_id') and tweet.in_reply_to_user_id is not None,
                "parent_id": tweet.in_reply_to_user_id if hasattr(tweet, 'in_reply_to_user_id') else None
            }
        )
```

---

## Testing Checklist

- [ ] Twitter Pro API access working
- [ ] Enhanced Twitter data collection (engagement metrics, user data, media)
- [ ] Reddit scraper fetching posts
- [ ] Database schema updated with new fields
- [ ] Data being stored correctly
- [ ] No duplicate sources
- [ ] Rate limits respected
- [ ] Error handling working

---

## Monitoring

Track these metrics:
- Daily sources collected per platform
- API quota usage (Twitter, Reddit)
- Data completeness (% of sources with all metadata)
- Error rates per scraper
- Average engagement metrics collected

---

## Next Steps After Implementation

1. Backfill historical data (last 30 days with Twitter Pro)
2. Add source credibility scoring
3. Implement NewsAPI or individual news scrapers
4. Add Telegram channel monitoring
5. Build analytics dashboard for data collection metrics

