"""
Blog Generation Celery Tasks
Scheduled tasks for generating blog articles 3-4 times daily
"""
import asyncio
import os
import logging
from celery import shared_task
from app.database import SessionLocal
from app.services.blog_generator import BlogArticleGenerator
from app.services.twitter_poster import TwitterPoster
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration
AUTO_POST_TO_TWITTER = os.getenv("AUTO_POST_TO_TWITTER", "false").lower() == "true"


@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def generate_morning_blog_article(self):
    """Generate morning edition at 9 AM"""
    db = SessionLocal()
    try:
        generator = BlogArticleGenerator(db)
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        article = loop.run_until_complete(generator.generate_morning_edition())
        logger.info(f"Generated morning article: {article.slug} (ID: {article.id})")
        
        # Auto-publish if configured
        if os.getenv("AUTO_PUBLISH_BLOG", "false").lower() == "true":
            loop.run_until_complete(_publish_article_async(db, article, auto_twitter=AUTO_POST_TO_TWITTER))
        
        return article.id
    except Exception as exc:
        logger.error(f"Morning article generation failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def generate_afternoon_blog_article(self):
    """Generate afternoon edition at 3 PM"""
    db = SessionLocal()
    try:
        generator = BlogArticleGenerator(db)
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        article = loop.run_until_complete(generator.generate_afternoon_edition())
        logger.info(f"Generated afternoon article: {article.slug} (ID: {article.id})")
        
        if os.getenv("AUTO_PUBLISH_BLOG", "false").lower() == "true":
            loop.run_until_complete(_publish_article_async(db, article, auto_twitter=AUTO_POST_TO_TWITTER))
        
        return article.id
    except Exception as exc:
        logger.error(f"Afternoon article generation failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def generate_evening_blog_article(self):
    """Generate evening edition at 9 PM"""
    db = SessionLocal()
    try:
        generator = BlogArticleGenerator(db)
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        article = loop.run_until_complete(generator.generate_evening_edition())
        logger.info(f"Generated evening article: {article.slug} (ID: {article.id})")
        
        if os.getenv("AUTO_PUBLISH_BLOG", "false").lower() == "true":
            loop.run_until_complete(_publish_article_async(db, article, auto_twitter=AUTO_POST_TO_TWITTER))
        
        return article.id
    except Exception as exc:
        logger.error(f"Evening article generation failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def generate_breaking_blog_article(self):
    """Generate breaking news edition at 11:30 PM"""
    db = SessionLocal()
    try:
        generator = BlogArticleGenerator(db)
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        article = loop.run_until_complete(generator.generate_breaking_news_edition())
        logger.info(f"Generated breaking news article: {article.slug} (ID: {article.id})")
        
        if os.getenv("AUTO_PUBLISH_BLOG", "false").lower() == "true":
            loop.run_until_complete(_publish_article_async(db, article, auto_twitter=AUTO_POST_TO_TWITTER))
        
        return article.id
    except Exception as exc:
        logger.error(f"Breaking news article generation failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)
    finally:
        db.close()


async def _publish_article_async(db, article, auto_twitter=False):
    """Helper function to publish article to Telegraph and optionally Twitter"""
    try:
        # Publish to Telegraph
        from app.routers.telegraph import create_telegraph_page, format_article_for_telegraph
        telegraph_content = format_article_for_telegraph(article)
        page = await create_telegraph_page(
            title=article.title,
            content=telegraph_content,
            author_name="FactCheckr MX",
            author_url="https://factcheck.mx"
        )
        article.telegraph_url = page.url
        article.telegraph_path = page.path
        logger.info(f"Published to Telegraph: {page.url}")
    except Exception as e:
        logger.error(f"Error publishing to Telegraph: {e}")
        # Continue even if Telegraph fails
    
    # Post to Twitter if configured
    if auto_twitter:
        try:
            poster = TwitterPoster()
            if poster.is_available():
                blog_url = f"https://factcheck.mx/blog/{article.slug}"
                twitter_url = poster.post_article(
                    title=article.title,
                    url=blog_url,
                    excerpt=article.excerpt
                )
                if twitter_url:
                    article.twitter_url = twitter_url
                    article.twitter_posted = True
                    logger.info(f"Posted to Twitter: {twitter_url}")
        except Exception as e:
            logger.error(f"Error posting to Twitter: {e}")
            # Continue even if Twitter fails
    
    # Mark as published
    article.published = True
    article.published_at = datetime.utcnow()
    db.commit()
    logger.info(f"Article {article.slug} published successfully")

