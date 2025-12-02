import asyncio
from celery import shared_task
from app.database import SessionLocal, Source
from app.scraper import TwitterScraper, GoogleNewsScraper
from app.tasks.fact_check import process_source
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Import YouTube scraper
try:
    from app.scraper_youtube import YouTubeScraper
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False
    logger.warning("YouTube scraper not available (missing dependencies)")

async def fetch_and_store(keywords):
    db = SessionLocal()
    try:
        # Initialize scrapers
        twitter = TwitterScraper()
        # reddit = RedditScraper() # Disabled
        google = GoogleNewsScraper()
        youtube = YouTubeScraper() if YOUTUBE_AVAILABLE else None
        
        # Check quota and fetch Twitter separately (with quota management)
        from app.services.quota_manager import quota_manager
        can_fetch, max_twitter_posts = quota_manager.can_fetch_posts(100, db)  # Request up to 100
        
        if not can_fetch:
            logger.warning("Twitter quota exhausted. Skipping Twitter scraping this run.")
            twitter_posts = []
        else:
            # Fetch Twitter posts with quota limit
            logger.info(f"Fetching Twitter posts (quota-limited to {max_twitter_posts} posts)")
            twitter_posts = await twitter.fetch_posts(keywords, max_results=max_twitter_posts)
        
        # Fetch other sources concurrently (Google, YouTube)
        tasks = [
            google.fetch_posts(keywords)
        ]
        
        # Add YouTube if available
        if youtube:
            tasks.append(youtube.fetch_posts(keywords))
        
        # Fetch other sources in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Start with Twitter posts (already fetched)
        all_posts = list(twitter_posts) if can_fetch else []
        
        # Add results from other sources
        scraper_names = ["Google", "YouTube"] if youtube else ["Google"]
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error(f"Error in {scraper_names[i]} scraper: {res}")
            elif isinstance(res, list):
                all_posts.extend(res)
        
        if not all_posts:
            logger.warning("No posts scraped from any source.")
        
        new_count = 0
        for post in all_posts:
            # Check if exists
            exists = db.query(Source).filter(Source.id == post.id).first()
            if not exists:
                # Parse timestamp
                try:
                    if post.timestamp:
                        # Try ISO format first
                        if isinstance(post.timestamp, str):
                            post_timestamp = datetime.fromisoformat(post.timestamp.replace('Z', '+00:00'))
                        else:
                            post_timestamp = post.timestamp
                    else:
                        post_timestamp = datetime.utcnow()
                except:
                    post_timestamp = datetime.utcnow()
                
                source = Source(
                    id=post.id,
                    platform=post.platform,
                    content=post.content,
                    author=post.author,
                    url=post.url,
                    timestamp=post_timestamp,
                    processed=0,  # Pending
                    # Enhanced data fields (if available)
                    engagement_metrics=post.engagement_metrics if hasattr(post, 'engagement_metrics') and post.engagement_metrics else None,
                    author_metadata=post.author_metadata if hasattr(post, 'author_metadata') and post.author_metadata else None,
                    media_urls=post.media_urls if hasattr(post, 'media_urls') and post.media_urls else None,
                    context_data=post.context_data if hasattr(post, 'context_data') and post.context_data else None,
                    credibility_score=0.5  # Default, can be calculated later
                )
                db.add(source)
                db.commit()
                
                # Trigger fact-check task
                process_source.delay(source.id)
                new_count += 1
                
        logger.info(f"Scraped {len(all_posts)} posts, {new_count} new.")
        return new_count
        
    except Exception as e:
        logger.error(f"Critical error in scraper task: {e}")
        db.rollback()
    finally:
        db.close()

@shared_task(
    bind=True,  # Bind task to get access to self (for retries)
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def scrape_all_sources(self):
    """Celery task to scrape all sources including YouTube
    
    Automatically retries on failure with exponential backoff.
    """
    # Get keywords from configuration
    # Can be overridden via environment variable: SCRAPING_KEYWORD_PRIORITY
    # Options: "high", "medium", "low", "all", "default"
    import os
    from app.config.scraping_keywords import get_keywords_for_scraping
    
    priority = os.getenv("SCRAPING_KEYWORD_PRIORITY", "default")
    keywords = get_keywords_for_scraping(priority)
    
    logger.info(f"Using {len(keywords)} keywords for scraping (priority: {priority})")
    
    try:
        # Run async function in sync Celery task
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        result = loop.run_until_complete(fetch_and_store(keywords))
        logger.info(f"Scraping task completed successfully. New sources: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Scraping task failed: {exc}", exc_info=True)
        # Re-raise to trigger automatic retry
        raise self.retry(exc=exc)
