"""
Twitter/X Posting Service
Posts blog article links to Twitter/X platform
"""
import os
import logging
from typing import Optional

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class TwitterPoster:
    """Post articles to Twitter/X"""
    
    def __init__(self):
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = os.getenv("TWITTER_ACCESS_SECRET")
        
        self.client = None
        if all([self.api_key, self.api_secret, self.access_token, self.access_secret]) and TWEEPY_AVAILABLE:
            try:
                # Twitter API v1.1 OAuth for posting
                auth = tweepy.OAuth1UserHandler(
                    self.api_key,
                    self.api_secret,
                    self.access_token,
                    self.access_secret
                )
                self.client = tweepy.API(auth, wait_on_rate_limit=True)
                logger.info("✓ Twitter API client initialized for posting")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter client: {e}")
                self.client = None
        else:
            if not TWEEPY_AVAILABLE:
                logger.warning("tweepy not available, Twitter posting disabled")
            else:
                logger.warning("Twitter posting credentials not configured")
    
    def post_article(self, title: str, url: str, excerpt: Optional[str] = None) -> Optional[str]:
        """Post article link to Twitter/X
        
        Args:
            title: Article title
            url: Article URL (factcheck.mx/blog/slug)
            excerpt: Optional article excerpt
            
        Returns:
            Tweet URL if successful, None otherwise
        """
        if not self.client:
            logger.warning("Twitter client not available, skipping post")
            return None
        
        # Build tweet text (max 280 chars)
        # Format: "Title\n\nExcerpt...\n\n[URL]"
        # URLs are shortened to ~23 chars by Twitter
        base_text = f"{title}\n\n"
        
        if excerpt:
            # Truncate excerpt to fit with URL (23 chars for t.co + 3 for newlines)
            max_excerpt = 280 - len(base_text) - 23 - 3
            if len(excerpt) > max_excerpt:
                excerpt_text = excerpt[:max_excerpt-3] + "..."
            else:
                excerpt_text = excerpt
            base_text += f"{excerpt_text}\n\n"
        
        base_text += url
        
        # Ensure total length is within limit
        if len(base_text) > 280:
            # Truncate title if needed
            available = 280 - len(url) - 3  # 3 for newlines
            if excerpt:
                available -= len(excerpt[:50]) + 3
            title_max = max(50, available)
            if len(title) > title_max:
                title = title[:title_max-3] + "..."
            base_text = f"{title}\n\n{excerpt[:50] if excerpt else ''}\n\n{url}" if excerpt else f"{title}\n\n{url}"
        
        try:
            tweet = self.client.update_status(status=base_text)
            tweet_url = f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
            logger.info(f"Posted article to Twitter: {tweet_url}")
            return tweet_url
        except Exception as e:
            logger.error(f"Error posting to Twitter: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if Twitter posting is available"""
        return self.client is not None

