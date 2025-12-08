#!/usr/bin/env python3
"""
Publish all unpublished blog articles

This script finds all blog articles with published=False and:
1. Sets published=True
2. Sets published_at to current timestamp
3. Optionally publishes to Telegraph (if PUBLISH_TO_TELEGRAPH=true)

Usage:
    python scripts/publish_all_blog_articles.py [--publish-telegraph]
    or
    PUBLISH_TO_TELEGRAPH=true python scripts/publish_all_blog_articles.py
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy.orm import Session

# Add backend directory to path to import app modules
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Load environment variables (try backend/.env first, then root .env)
backend_env = os.path.join(backend_path, '.env')
if os.path.exists(backend_env):
    load_dotenv(backend_env)
else:
    load_dotenv()  # Load from root directory

from app.database.connection import get_engine
from app.database.models import BlogArticle
from sqlalchemy.orm import sessionmaker

# Configuration
PUBLISH_TO_TELEGRAPH = os.getenv("PUBLISH_TO_TELEGRAPH", "false").lower() == "true"


async def publish_to_telegraph(article: BlogArticle, db: Session):
    """Publish article to Telegraph if not already published there"""
    try:
        from app.routers.telegraph import create_telegraph_page, format_article_for_telegraph
        
        # Skip if already published to Telegraph
        if article.telegraph_url:
            print(f"  ✓ Article already published to Telegraph: {article.telegraph_url}")
            return
        
        print(f"  → Publishing to Telegraph...")
        telegraph_content = format_article_for_telegraph(article)
        page = await create_telegraph_page(
            title=article.title,
            content=telegraph_content,
            author_name="FactCheckr MX",
            author_url="https://factcheck.mx"
        )
        article.telegraph_url = page.url
        article.telegraph_path = page.path
        print(f"  ✓ Published to Telegraph: {page.url}")
    except Exception as e:
        print(f"  ⚠ Warning: Failed to publish to Telegraph: {e}")
        # Continue even if Telegraph fails


def publish_all_articles(publish_telegraph: bool = False):
    """Publish all unpublished blog articles"""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Find all unpublished articles
        unpublished = db.query(BlogArticle).filter(
            BlogArticle.published == False
        ).order_by(BlogArticle.created_at).all()
        
        total = len(unpublished)
        
        if total == 0:
            print("✅ No unpublished articles found. All articles are already published!")
            return
        
        print(f"📝 Found {total} unpublished article(s)")
        print("-" * 60)
        
        # Create event loop for async Telegraph publishing
        loop = None
        if publish_telegraph:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        
        published_count = 0
        skipped_count = 0
        
        for i, article in enumerate(unpublished, 1):
            print(f"\n[{i}/{total}] Processing: {article.title}")
            print(f"  Type: {article.article_type}, Slug: {article.slug}")
            
            try:
                # Set published flag and timestamp
                article.published = True
                article.published_at = datetime.utcnow()
                
                # Publish to Telegraph if requested
                if publish_telegraph:
                    loop.run_until_complete(publish_to_telegraph(article, db))
                
                # Commit changes
                db.commit()
                db.refresh(article)
                
                print(f"  ✅ Published successfully!")
                published_count += 1
                
            except Exception as e:
                print(f"  ❌ Error publishing article: {e}")
                db.rollback()
                skipped_count += 1
                continue
        
        print("\n" + "=" * 60)
        print(f"📊 Summary:")
        print(f"   Total unpublished: {total}")
        print(f"   ✅ Published: {published_count}")
        if skipped_count > 0:
            print(f"   ⚠ Skipped (errors): {skipped_count}")
        
        # Show final stats
        total_published = db.query(BlogArticle).filter(
            BlogArticle.published == True
        ).count()
        total_unpublished = db.query(BlogArticle).filter(
            BlogArticle.published == False
        ).count()
        
        print(f"\n📈 Database Status:")
        print(f"   Total published articles: {total_published}")
        print(f"   Total unpublished articles: {total_unpublished}")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Publish all unpublished blog articles"
    )
    parser.add_argument(
        "--publish-telegraph",
        action="store_true",
        help="Also publish articles to Telegraph"
    )
    
    args = parser.parse_args()
    
    # Check environment variable or command line argument
    publish_telegraph = PUBLISH_TO_TELEGRAPH or args.publish_telegraph
    
    if publish_telegraph:
        print("📡 Telegraph publishing enabled")
    else:
        print("ℹ️  Telegraph publishing disabled (use --publish-telegraph or PUBLISH_TO_TELEGRAPH=true to enable)")
    
    print("\n🚀 Starting publication process...\n")
    
    publish_all_articles(publish_telegraph=publish_telegraph)
    
    print("\n✅ Done!")

