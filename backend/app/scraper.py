from abc import ABC, abstractmethod
from typing import List
from app.models import SocialPost
import uuid
import os
from datetime import datetime
from bs4 import BeautifulSoup

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

    async def fetch_posts(self, keywords: List[str]) -> List[SocialPost]:
        if not self.client:
            return []

        posts = []
        # Twitter API V2 query
        # "keyword1 OR keyword2 -is:retweet lang:es"
        query = f"({' OR '.join(keywords)}) -is:retweet lang:es"
        
        try:
            # Search recent tweets (last 7 days)
            # Note: Basic tier has limits on search
            response = self.client.search_recent_tweets(
                query=query,
                max_results=10,
                tweet_fields=["created_at", "author_id", "id", "text"]
            )
            
            if response.data:
                for tweet in response.data:
                    posts.append(SocialPost(
                        id=str(tweet.id),
                        platform="X (Twitter)",
                        content=tweet.text,
                        author=f"user_{tweet.author_id}", # We'd need another call to get username, skipping for speed
                        timestamp=tweet.created_at.isoformat() if tweet.created_at else datetime.now().isoformat(),
                        url=f"https://twitter.com/user/status/{tweet.id}"
                    ))
        except Exception as e:
            print(f"Error fetching from Twitter: {e}")
            
        return posts

import feedparser
import urllib.parse

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
