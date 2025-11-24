import asyncio
from celery import shared_task
from app.database import SessionLocal, Source
from app.scraper import TwitterScraper, GoogleNewsScraper
from app.tasks.fact_check import process_source
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def fetch_and_store(keywords):
    db = SessionLocal()
    try:
        # Initialize scrapers
        twitter = TwitterScraper()
        # reddit = RedditScraper() # Disabled
        google = GoogleNewsScraper()
        
        # Fetch concurrently with individual error handling
        tasks = [
            twitter.fetch_posts(keywords),
            # reddit.fetch_posts(keywords),
            google.fetch_posts(keywords)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_posts = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                scraper_names = ["Twitter", "Google"]
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
                source = Source(
                    id=post.id,
                    platform=post.platform,
                    content=post.content,
                    author=post.author,
                    url=post.url,
                    timestamp=post.timestamp or datetime.utcnow(),
                    processed=0 # Pending
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

@shared_task
def scrape_all_sources():
    """Celery task to scrape all sources"""
    keywords = ["Reforma Judicial", "Sheinbaum", "México", "Morena"]
    
    # Run async function in sync Celery task
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(fetch_and_store(keywords))
