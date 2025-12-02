"""
Keywords Management Router

Endpoints for viewing and managing scraping keywords.
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from app.config.scraping_keywords import (
    get_keywords_for_scraping,
    get_keywords_by_category,
    get_keyword_statistics,
    HIGH_PRIORITY_KEYWORDS,
    MEDIUM_PRIORITY_KEYWORDS,
    LOW_PRIORITY_KEYWORDS,
    ALL_KEYWORDS,
    KEYWORDS_BY_CATEGORY
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/keywords", tags=["keywords"])


@router.get("/")
async def get_keywords(
    priority: Optional[str] = Query(None, description="Filter by priority: high|medium|low|all|default"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories")
):
    """Get keywords for scraping"""
    
    if categories:
        # Get keywords by category
        category_list = [c.strip() for c in categories.split(",")]
        keywords = get_keywords_by_category(category_list)
        return {
            "keywords": keywords,
            "count": len(keywords),
            "categories": category_list,
            "source": "categories"
        }
    elif priority:
        # Get keywords by priority
        if priority not in ["high", "medium", "low", "all", "default"]:
            return {
                "error": "Invalid priority. Must be: high, medium, low, all, or default"
            }
        keywords = get_keywords_for_scraping(priority)
        return {
            "keywords": keywords,
            "count": len(keywords),
            "priority": priority,
            "source": "priority"
        }
    else:
        # Return all keywords organized by priority
        return {
            "high_priority": HIGH_PRIORITY_KEYWORDS,
            "medium_priority": MEDIUM_PRIORITY_KEYWORDS,
            "low_priority": LOW_PRIORITY_KEYWORDS,
            "all_keywords": ALL_KEYWORDS,
            "statistics": get_keyword_statistics()
        }


@router.get("/categories")
async def get_categories():
    """Get available keyword categories"""
    return {
        "categories": list(KEYWORDS_BY_CATEGORY.keys()),
        "keywords_by_category": KEYWORDS_BY_CATEGORY
    }


@router.get("/statistics")
async def get_statistics():
    """Get keyword configuration statistics"""
    return get_keyword_statistics()

