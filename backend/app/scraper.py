from abc import ABC, abstractmethod
from typing import List
from app.models import SocialPost
import uuid
import os
from datetime import datetime
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class Scraper(ABC):
    @abstractmethod
    async def fetch_posts(self, keywords: List[str]) -> List[SocialPost]:
        pass

class MockScraper(Scraper):
    async def fetch_posts(self, keywords: List[str]) -> List[SocialPost]:
        # Simulate fetching data from social media
        # In a real scenario, this would use APIs or scraping tools
        
        mock_data = [
            SocialPost(
                id=str(uuid.uuid4()),
                platform="Twitter",
                content="¡Increíble! La Reforma Judicial va a eliminar a todos los jueces mañana. #ReformaJudicial",
                author="@fake_news_bot",
                timestamp=datetime.now().isoformat(),
                url="https://twitter.com/fake/status/123"
            ),
            SocialPost(
                id=str(uuid.uuid4()),
                platform="Facebook",
                content="Sheinbaum anuncia que el metro será gratis para siempre. ¿Será verdad?",
                author="Tía Conspiración",
                timestamp=datetime.now().isoformat(),
                url="https://facebook.com/post/456"
            )
        ]
        return mock_data



import tweepy
import requests
from datetime import datetime, timedelta
import json

# Optional Facebook SDK import
try:
    import facebook
    FACEBOOK_AVAILABLE = True
except ImportError:
    FACEBOOK_AVAILABLE = False
    facebook = None

class TwitterScraper(Scraper):
    def __init__(self):
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = os.getenv("TWITTER_ACCESS_SECRET")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        self.client = None
        
        if self.bearer_token:
            # V2 API Client
            self.client = tweepy.Client(bearer_token=self.bearer_token)
        elif self.api_key and self.api_secret:
            # Fallback to V1.1 or V2 with consumer keys if needed, but V2 usually needs bearer for search
            # For simplicity, we'll assume Bearer Token is available for V2 search
            pass
            
        if not self.client:
            print("Warning: Twitter credentials (Bearer Token) not found. TwitterScraper will not work.")

    async def fetch_posts(self, keywords: List[str], max_results: int = None) -> List[SocialPost]:
        if not self.client:
            return []

        # Check quota before fetching
        from app.services.quota_manager import quota_manager
        from app.database.connection import SessionLocal
        
        db = SessionLocal()
        try:
            # Default max_results if not specified
            if max_results is None:
                max_results = 100  # Basic tier allows up to 100 per request
            
            # Check quota and adjust max_results
            can_fetch, allowed_count = quota_manager.can_fetch_posts(max_results, db)
            
            if not can_fetch:
                logger.warning("Twitter quota exhausted. Skipping fetch.")
                return []
            
            # Use the allowed count (may be less than requested)
            max_results = allowed_count
            
            quota_status = quota_manager.get_quota_status(db)
            logger.info(
                f"Twitter quota: {quota_status['used']}/{quota_status['monthly_quota']} "
                f"({quota_status['percentage_used']:.1f}% used). "
                f"Fetching up to {max_results} posts."
            )
        finally:
            db.close()

        posts = []
        # Twitter API V2 query
        # "keyword1 OR keyword2 -is:retweet lang:es"
        query = f"({' OR '.join(keywords)}) -is:retweet lang:es"
        
        try:
            # Search recent tweets with Basic tier enhancements
            # Basic tier allows up to 100 results per request (increased from 10)
            # Using expansions to get user data and media without extra API calls
            response = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,  # Use quota-limited count
                tweet_fields=[
                    "created_at", 
                    "author_id", 
                    "id", 
                    "text",
                    "public_metrics",  # Engagement metrics: likes, retweets, replies, quotes
                    "attachments",     # Media keys
                    "context_annotations",
                    "geo",
                    "lang",
                    "possibly_sensitive",
                    "referenced_tweets"  # For replies and quote tweets
                ],
                expansions=[
                    "author_id",              # Get user data
                    "attachments.media_keys"  # Get media data
                ],
                user_fields=[
                    "username",
                    "name",
                    "verified",
                    "public_metrics",  # follower_count, following_count, tweet_count
                    "created_at",
                    "description",
                    "location",
                    "profile_image_url"
                ],
                media_fields=[
                    "type",
                    "url",
                    "preview_image_url",
                    "variants",  # For videos
                    "width",
                    "height"
                ]
            )
            
            if response.data:
                # Build lookup dictionaries for expanded data
                users = {}
                media = {}
                
                if response.includes:
                    # Map user IDs to user objects
                    if 'users' in response.includes:
                        users = {user.id: user for user in response.includes['users']}
                    
                    # Map media keys to media objects
                    if 'media' in response.includes:
                        media = {m.media_key: m for m in response.includes['media']}
                
                for tweet in response.data:
                    # Get author information
                    author = users.get(tweet.author_id) if tweet.author_id else None
                    author_username = author.username if author else f"user_{tweet.author_id}"
                    
                    # Extract media URLs
                    media_urls = []
                    if hasattr(tweet, 'attachments') and tweet.attachments:
                        # attachments can be a dict or an object
                        if isinstance(tweet.attachments, dict):
                            media_keys = tweet.attachments.get('media_keys', [])
                        else:
                            media_keys = getattr(tweet.attachments, 'media_keys', [])
                        
                        for media_key in media_keys:
                            if media_key in media:
                                m = media[media_key]
                                url = getattr(m, 'url', None) or (m.url if isinstance(m, dict) else None)
                                preview_url = getattr(m, 'preview_image_url', None) or (m.get('preview_image_url') if isinstance(m, dict) else None)
                                
                                if url:
                                    media_urls.append(url)
                                elif preview_url:
                                    media_urls.append(preview_url)
                    
                    # Build engagement metrics
                    engagement = {}
                    if hasattr(tweet, 'public_metrics') and tweet.public_metrics:
                        # public_metrics can be a dict or an object
                        if isinstance(tweet.public_metrics, dict):
                            engagement = {
                                "likes": tweet.public_metrics.get('like_count', 0),
                                "retweets": tweet.public_metrics.get('retweet_count', 0),
                                "replies": tweet.public_metrics.get('reply_count', 0),
                                "quotes": tweet.public_metrics.get('quote_count', 0),
                                "views": tweet.public_metrics.get('impression_count', 0)
                            }
                        else:
                            # It's an object with attributes
                            engagement = {
                                "likes": getattr(tweet.public_metrics, 'like_count', 0),
                                "retweets": getattr(tweet.public_metrics, 'retweet_count', 0),
                                "replies": getattr(tweet.public_metrics, 'reply_count', 0),
                                "quotes": getattr(tweet.public_metrics, 'quote_count', 0),
                                "views": getattr(tweet.public_metrics, 'impression_count', 0)
                            }
                    
                    # Build author metadata
                    author_meta = {}
                    if author:
                        # Get public_metrics safely
                        follower_count = 0
                        following_count = 0
                        tweet_count = 0
                        if hasattr(author, 'public_metrics') and author.public_metrics:
                            if isinstance(author.public_metrics, dict):
                                follower_count = author.public_metrics.get('followers_count', 0)
                                following_count = author.public_metrics.get('following_count', 0)
                                tweet_count = author.public_metrics.get('tweet_count', 0)
                            else:
                                follower_count = getattr(author.public_metrics, 'followers_count', 0)
                                following_count = getattr(author.public_metrics, 'following_count', 0)
                                tweet_count = getattr(author.public_metrics, 'tweet_count', 0)
                        
                        author_meta = {
                            "username": getattr(author, 'username', None),
                            "display_name": getattr(author, 'name', None),
                            "verified": getattr(author, 'verified', False),
                            "follower_count": follower_count,
                            "following_count": following_count,
                            "tweet_count": tweet_count,
                            "account_created": author.created_at.isoformat() if hasattr(author, 'created_at') and author.created_at else None,
                            "bio": getattr(author, 'description', None),
                            "location": getattr(author, 'location', None),
                            "profile_image_url": getattr(author, 'profile_image_url', None)
                        }
                    
                    # Build context data
                    context = {}
                    if hasattr(tweet, 'referenced_tweets') and tweet.referenced_tweets:
                        for ref in tweet.referenced_tweets:
                            if ref.type == 'replied_to':
                                context['is_reply'] = True
                                context['parent_id'] = ref.id
                            elif ref.type == 'quoted':
                                context['is_quote_tweet'] = True
                                context['quoted_tweet_id'] = ref.id
                    
                    # Build URL with actual username
                    tweet_url = f"https://twitter.com/{author_username}/status/{tweet.id}"
                    
                    # Create SocialPost with enhanced data
                    posts.append(SocialPost(
                        id=str(tweet.id),
                        platform="X (Twitter)",
                        content=tweet.text,
                        author=author_username,
                        timestamp=tweet.created_at.isoformat() if tweet.created_at else datetime.now().isoformat(),
                        url=tweet_url,
                        engagement_metrics=engagement if engagement else None,
                        author_metadata=author_meta if author_meta else None,
                        media_urls=media_urls if media_urls else None,
                        context_data=context if context else None
                    ))
                    
        except Exception as e:
            print(f"Error fetching from Twitter: {e}")
            import traceback
            traceback.print_exc()
            
        return posts

import feedparser
import urllib.parse

# Import YouTube scraper
try:
    from app.scraper_youtube import YouTubeScraper
except ImportError:
    YouTubeScraper = None
    print("Warning: YouTube scraper not available (missing dependencies)")

class GoogleNewsScraper(Scraper):
    async def fetch_posts(self, keywords: List[str]) -> List[SocialPost]:
        posts = []
        # Construct RSS URL
        # query: {keywords} when:1d
        # hl=es-419&gl=MX&ceid=MX:es-419 (Mexico settings)
        
        query_str = " OR ".join(keywords)
        encoded_query = urllib.parse.quote(f"{query_str} when:1d")
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es-419&gl=MX&ceid=MX:es-419"
        
        try:
            # feedparser is synchronous, but fast enough for PoC. 
            # In production, run in executor.
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:10]:
                # Strip HTML from title and summary using BeautifulSoup
                clean_title = BeautifulSoup(entry.title, "html.parser").get_text() if 'title' in entry else ""
                clean_summary = BeautifulSoup(entry.summary, "html.parser").get_text() if 'summary' in entry else ""
                
                posts.append(SocialPost(
                    id=entry.id if 'id' in entry else entry.link,
                    platform="Google News",
                    content=f"{clean_title}\n{clean_summary}".strip(),
                    author=entry.source.title if 'source' in entry else "Unknown Source",
                    timestamp=datetime(*entry.published_parsed[:6]).isoformat() if 'published_parsed' in entry else datetime.now().isoformat(),
                    url=entry.link
                ))
        except Exception as e:
            print(f"Error fetching from Google News: {e}")

        return posts


class FacebookScraper(Scraper):
    """Facebook Graph API scraper for public posts and pages"""

    def __init__(self):
        if not FACEBOOK_AVAILABLE:
            print("Warning: facebook-sdk not installed. Facebook scraping disabled.")
            self.api = None
            return

        self.app_id = os.getenv("FACEBOOK_APP_ID")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET")
        self.access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        self.page_access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
        self.api = None

        if self.access_token:
            try:
                self.api = facebook.GraphAPI(access_token=self.access_token, version="3.1")
                print("✓ Facebook Graph API initialized")
            except Exception as e:
                print(f"Warning: Failed to initialize Facebook API: {e}")
                self.api = None
        else:
            print("Warning: FACEBOOK_ACCESS_TOKEN not found. Facebook scraping disabled.")

    async def fetch_posts(self, keywords: List[str]) -> List[SocialPost]:
        """Fetch posts from Facebook pages and public groups"""
        posts = []

        if not self.api:
            print("Facebook API not initialized - returning empty results")
            return posts

        # Mexican political pages and groups to monitor
        target_pages = [
            "gobierno.mexico",  # Official government page
            "lopezobrador.org",  # President López Obrador
            "PRI.Nacional",     # PRI Party
            "PAN",
            "prd.mx",           # PRD Party
            "MovimientoCiudadanoMX",
            "partidoverde.mx",
            "PTmexico",
            "MorenaOficial",    # Morena Party
            "partidomovimiento.ciudadano",  # Movimiento Ciudadano
            "claudia.sheinbaum",  # Claudia Sheinbaum
            "XochitlGalvez",    # Xóchitl Gálvez
        ]

        try:
            for page_id in target_pages[:5]:  # Limit to 5 pages to avoid rate limits
                try:
                    # Get recent posts from the page
                    page_posts = self.api.get_connections(page_id, 'posts', limit=10,
                                                        fields='id,message,created_time,permalink_url,likes.summary(true),comments.summary(true),shares')

                    for post in page_posts['data']:
                        content = post.get('message', '')
                        if not content:
                            continue

                        # Check if post contains any of our keywords
                        content_lower = content.lower()
                        matched_keywords = [kw for kw in keywords if kw.lower() in content_lower]

                        if matched_keywords:
                            # Get engagement metrics
                            likes_count = post.get('likes', {}).get('summary', {}).get('total_count', 0)
                            comments_count = post.get('comments', {}).get('summary', {}).get('total_count', 0)
                            shares_count = post.get('shares', {}).get('count', 0) if 'shares' in post else 0

                            engagement = {
                                'likes': likes_count,
                                'comments': comments_count,
                                'shares': shares_count,
                                'total_engagement': likes_count + comments_count + shares_count
                            }

                            posts.append(SocialPost(
                                id=post['id'],
                                platform="Facebook",
                                content=content,
                                author=page_id,  # Page name
                                timestamp=post['created_time'],
                                url=post.get('permalink_url', f"https://facebook.com/{post['id']}"),
                                engagement_metrics=engagement,
                                context_data={
                                    'matched_keywords': matched_keywords,
                                    'post_type': 'page_post'
                                }
                            ))

                except Exception as e:
                    print(f"Error fetching from Facebook page {page_id}: {e}")
                    continue

        except Exception as e:
            print(f"Error in Facebook scraping: {e}")

        print(f"Facebook scraper found {len(posts)} posts")
        return posts


class InstagramScraper(Scraper):
    """Instagram Basic Display API scraper"""

    def __init__(self):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.user_id = os.getenv("INSTAGRAM_USER_ID")
        self.base_url = "https://graph.instagram.com"

    async def fetch_posts(self, keywords: List[str]) -> List[SocialPost]:
        """Fetch posts from Instagram accounts"""
        posts = []

        if not self.access_token or not self.user_id:
            print("Instagram credentials not configured - returning empty results")
            return posts

        try:
            # Get recent media from the account
            url = f"{self.base_url}/{self.user_id}/media"
            params = {
                'access_token': self.access_token,
                'fields': 'id,media_type,media_url,permalink,caption,timestamp,like_count,comments_count',
                'limit': 20
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for media in data.get('data', []):
                caption = media.get('caption', '')
                if not caption:
                    continue

                # Check if caption contains any of our keywords
                caption_lower = caption.lower()
                matched_keywords = [kw for kw in keywords if kw.lower() in caption_lower]

                if matched_keywords:
                    engagement = {
                        'likes': media.get('like_count', 0),
                        'comments': media.get('comments_count', 0),
                        'total_engagement': media.get('like_count', 0) + media.get('comments_count', 0)
                    }

                    posts.append(SocialPost(
                        id=media['id'],
                        platform="Instagram",
                        content=caption,
                        author=self.user_id,  # Account ID
                        timestamp=media['timestamp'],
                        url=media.get('permalink', ''),
                        engagement_metrics=engagement,
                        media_urls=[media.get('media_url')] if media.get('media_url') else None,
                        context_data={
                            'matched_keywords': matched_keywords,
                            'media_type': media.get('media_type', 'IMAGE'),
                            'post_type': 'instagram_post'
                        }
                    ))

        except Exception as e:
            print(f"Error in Instagram scraping: {e}")

        print(f"Instagram scraper found {len(posts)} posts")
        return posts
