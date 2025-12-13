"""
Blog API Router
Handles blog article listing, retrieval, and publishing with subscription-based access
"""
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, nullslast
from typing import Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel

from app.database.connection import get_db
from app.database.models import BlogArticle, User, SubscriptionTier
from app.core.auth import get_current_user, get_optional_user
from app.core.utils import get_user_tier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/blog", tags=["blog"])

# Free tier: 3 articles, PRO: unlimited
FREE_TIER_ARTICLE_LIMIT = int(os.getenv("BLOG_FREE_TIER_LIMIT", "3"))


@router.get("/stats")
async def get_blog_stats(db: Session = Depends(get_db)):
    """Get blog statistics (for debugging)"""
    try:
        total = db.query(BlogArticle).count()
        published = db.query(BlogArticle).filter(BlogArticle.published == True).count()
        unpublished = total - published
        
        # Count by article type
        by_type = {}
        for article_type in ["morning", "afternoon", "evening", "breaking"]:
            count = db.query(BlogArticle).filter(
                BlogArticle.article_type == article_type,
                BlogArticle.published == True
            ).count()
            by_type[article_type] = count
        
        return {
            "total_articles": total,
            "published": published,
            "unpublished": unpublished,
            "by_type": by_type
        }
    except Exception as e:
        logger.error(f"Error getting blog stats: {e}", exc_info=True)
        return {"error": str(e)}


class BlogArticleResponse(BaseModel):
    """Blog article summary response"""
    id: int
    title: str
    slug: str
    excerpt: Optional[str]
    article_type: str
    published_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class BlogArticleDetailResponse(BlogArticleResponse):
    """Full blog article response"""
    content: str
    telegraph_url: Optional[str]
    twitter_url: Optional[str]
    topic_id: Optional[int]
    data_context: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


@router.get("/articles", response_model=Dict)
async def list_articles(
    limit: int = Query(20, ge=1, le=100),
    article_type: Optional[str] = None,
    status: Optional[str] = Query("published", pattern="^(published|draft|all)$"),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """List blog articles with subscription-based access
    
    Free tier: Returns only 3 most recent articles
    PRO tier: Returns all articles with pagination
    Admin: Can view drafts/all articles
    """
    try:
        # Log the request for debugging
        logger.info(f"Blog articles request: user={user.id if user else None}, article_type={article_type}, limit={limit}, status={status}")
        
        query = db.query(BlogArticle)
        
        # Admin-only status filtering
        is_admin = user and user.is_admin
        
        if status == "draft":
            if not is_admin:
                raise HTTPException(status_code=403, detail="Only admins can view drafts")
            query = query.filter(BlogArticle.published == False)
        elif status == "all":
            if not is_admin:
                raise HTTPException(status_code=403, detail="Only admins can view all articles")
            # No filter on published
        else:
            # Default: only published
            query = query.filter(BlogArticle.published == True)
        
        if article_type:
            query = query.filter(BlogArticle.article_type == article_type)
        
        # Get user tier (default to FREE for anonymous users)
        tier = get_user_tier(db, user.id) if user else SubscriptionTier.FREE
        logger.info(f"User tier determined: {tier.value}")
        
        # Free tier limit (only applies to non-admins)
        if tier == SubscriptionTier.FREE and not is_admin:
            # Order by published_at (NULLS LAST) or created_at as fallback
            query = query.order_by(
                nullslast(desc(BlogArticle.published_at)),
                desc(BlogArticle.created_at)
            ).limit(FREE_TIER_ARTICLE_LIMIT)
            has_more = False
        else:
            query = query.order_by(
                nullslast(desc(BlogArticle.published_at)),
                desc(BlogArticle.created_at)
            ).limit(limit)
            
            # Check if there are more articles
            count_query = db.query(BlogArticle)
            if status == "published" or not is_admin:
                count_query = count_query.filter(BlogArticle.published == True)
            elif status == "draft":
                count_query = count_query.filter(BlogArticle.published == False)
            
            total_count = count_query.count()
            has_more = total_count > limit
        
        articles = query.all()
        logger.info(f"Found {len(articles)} articles to return")
        
        return {
            "articles": [BlogArticleResponse.model_validate(a) for a in articles],
            "tier": tier.value,
            "has_more": has_more,
            "free_tier_limit": FREE_TIER_ARTICLE_LIMIT if tier == SubscriptionTier.FREE else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching blog articles: {e}", exc_info=True)
        # Return empty result on error instead of crashing
        return {
            "articles": [],
            "tier": SubscriptionTier.FREE.value,
            "has_more": False,
            "free_tier_limit": FREE_TIER_ARTICLE_LIMIT
        }


@router.get("/articles/{slug}", response_model=BlogArticleDetailResponse)
async def get_article(
    slug: str,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get full article content with subscription check
    
    Free tier: Can only access 3 most recent articles
    PRO tier: Full access to all articles
    """
    article = db.query(BlogArticle).filter(
        and_(
            BlogArticle.slug == slug,
            BlogArticle.published == True
        )
    ).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    tier = get_user_tier(db, user.id) if user else SubscriptionTier.FREE
    
    # Free tier: check if article is in top 3 most recent
    if tier == SubscriptionTier.FREE:
        recent_articles = db.query(BlogArticle).filter(
            BlogArticle.published == True
        ).order_by(desc(BlogArticle.published_at)).limit(FREE_TIER_ARTICLE_LIMIT).all()
        
        if article.id not in [a.id for a in recent_articles]:
            raise HTTPException(
                status_code=403,
                detail=f"Free tier limited to {FREE_TIER_ARTICLE_LIMIT} most recent articles. Upgrade to PRO for full access."
            )
    
    return BlogArticleDetailResponse.model_validate(article)


@router.post("/articles/{article_id}/publish")
async def publish_article(
    article_id: int,
    publish_to_telegraph: bool = Query(True),
    publish_to_twitter: bool = Query(False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish article (requires authentication, admin recommended)
    
    Optionally publishes to Telegraph and Twitter
    """
    article = db.query(BlogArticle).filter(BlogArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if article.published:
        raise HTTPException(status_code=400, detail="Article already published")
    
    # Publish to Telegraph if requested
    if publish_to_telegraph:
        try:
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
        except Exception as e:
            logger.error(f"Error publishing to Telegraph: {e}")
            # Continue even if Telegraph fails
    
    # Post to Twitter if requested
    if publish_to_twitter:
        try:
            from app.services.twitter_poster import TwitterPoster
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
        except Exception as e:
            logger.error(f"Error posting to Twitter: {e}")
            # Continue even if Twitter fails
    
    article.published = True
    article.published_at = datetime.utcnow()
    db.commit()
    db.refresh(article)
    
    return {
        "message": "Article published successfully",
        "article_id": article.id,
        "telegraph_url": article.telegraph_url,
        "twitter_url": article.twitter_url
    }


@router.post("/articles/{article_id}/post-twitter")
async def post_to_twitter(
    article_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually post article to Twitter/X"""
    article = db.query(BlogArticle).filter(BlogArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if not article.published:
        raise HTTPException(status_code=400, detail="Article must be published before posting to Twitter")
    
    if article.twitter_posted:
        raise HTTPException(status_code=400, detail="Article already posted to Twitter")
    
    try:
        from app.services.twitter_poster import TwitterPoster
        poster = TwitterPoster()
        
        if not poster.is_available():
            raise HTTPException(status_code=503, detail="Twitter posting not available (credentials not configured)")
        
        blog_url = f"https://factcheck.mx/blog/{article.slug}"
        twitter_url = poster.post_article(
            title=article.title,
            url=blog_url,
            excerpt=article.excerpt
        )
        
        if twitter_url:
            article.twitter_url = twitter_url
            article.twitter_posted = True
            db.commit()
            return {"message": "Posted to Twitter successfully", "twitter_url": twitter_url}
        else:
            raise HTTPException(status_code=500, detail="Failed to post to Twitter")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error posting to Twitter: {e}")
        raise HTTPException(status_code=500, detail=f"Error posting to Twitter: {str(e)}")

