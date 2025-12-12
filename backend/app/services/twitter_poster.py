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
    
    def upload_media(self, file_path: str) -> Optional[str]:
        """Upload media to Twitter/X and return media_id"""
        if not self.client or not os.path.exists(file_path):
            return None
        try:
            # For V1.1 API, we use api.media_upload
            media = self.client.media_upload(filename=file_path)
            return media.media_id_string
        except Exception as e:
            logger.error(f"Error uploading media: {e}")
            return None

    def post_article(self, title: str, url: str, excerpt: Optional[str] = None, image_path: Optional[str] = None) -> Optional[str]:
        """Post article link to Twitter/X
        
        Args:
            title: Article title
            url: Article URL (factcheck.mx/blog/slug)
            excerpt: Optional article excerpt
            image_path: Optional path to local image file to attach
            
        Returns:
            Tweet URL if successful, None otherwise
        """
        if not self.client:
            logger.warning("Twitter client not available, skipping post")
            return None
            
        # Upload media if present
        media_ids = []
        if image_path:
            mid = self.upload_media(image_path)
            if mid:
                media_ids.append(mid)
        
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
            tweet = self.client.update_status(status=base_text, media_ids=media_ids if media_ids else None)
            tweet_url = f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
            logger.info(f"Posted article to Twitter: {tweet_url}")
            return tweet_url
        except Exception as e:
            logger.error(f"Error posting to Twitter: {e}")
            return None
    
    def post_thread(self, tweets: list[str], media_ids: Optional[list[str]] = None) -> Optional[str]:
        """Post a thread of tweets
        
        Args:
            tweets: List of tweet strings
            media_ids: Optional list of media_ids to attach to the FIRST tweet
            
        Returns:
            URL of the first tweet in the thread
        """
        if not self.client or not tweets:
            return None
            
        try:
            # Post first tweet
            first_tweet = self.client.update_status(
                status=tweets[0], 
                media_ids=media_ids if media_ids else None
            )
            previous_id = first_tweet.id
            username = first_tweet.user.screen_name
            first_url = f"https://twitter.com/{username}/status/{previous_id}"
            
            logger.info(f"Started thread: {first_url}")
            
            # Post replies
            for text in tweets[1:]:
                try:
                    reply = self.client.update_status(
                        status=text,
                        in_reply_to_status_id=previous_id,
                        auto_populate_reply_metadata=True
                    )
                    previous_id = reply.id
                except Exception as e:
                    logger.error(f"Error posting reply in thread: {e}")
                    # Continue trying to post remaining tweets? Or break?
                    # Breaking is safer to maintain order
                    break
                    
            return first_url
            
        except Exception as e:
            logger.error(f"Error posting thread start: {e}")
            return None

    def post_long_text(self, text: str) -> Optional[str]:
        """Split long text into a thread and post it"""
        chunks = self._chunk_text(text)
        return self.post_thread(chunks)

    def _chunk_text(self, text: str, limit: int = 280) -> list[str]:
        """Split text into 280-char chunks with numbering (1/X)"""
        import textwrap
        
        # First pass: rough split
        # We need to reserve space for " (XX/XX)" suffix, approx 8 chars
        # So we split at ~270 chars
        
        # Naive estimation of chunks
        est_chunks = (len(text) // 270) + 1
        
        if est_chunks == 1:
            return [text] if len(text) <= limit else textwrap.wrap(text, width=limit)
            
        current_chunks = []
        words = text.split()
        current_chunk = ""
        
        chunks = []
        
        # improved split logic could go here, but using textwrap for simplicity
        # We'll stick to a simpler logic:
        # 1. Split into chunks of 260 chars (leaving room for 1/99)
        # 2. Add numbering
        
        raw_chunks = textwrap.wrap(text, width=270, break_long_words=False, replace_whitespace=False)
        total = len(raw_chunks)
        
        final_chunks = []
        for i, chunk in enumerate(raw_chunks):
            suffix = f" {i+1}/{total}"
            if len(chunk) + len(suffix) > limit:
                # This rare case where adding suffix exceeds limit due to word wrapping edge cases
                # We forced width=270 so this shouldn't happen often unless limit=280
                # But to be safe, we might need to re-wrap or truncate
                pass
            final_chunks.append(f"{chunk}{suffix}")
            
        return final_chunks
    
    def is_available(self) -> bool:
        """Check if Twitter posting is available"""
        return self.client is not None

