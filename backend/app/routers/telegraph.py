"""
Telegraph (Telegra.ph) Integration Router
Publishes fact-check articles to Telegraph
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
import os
import logging
import httpx
from app.database import SessionLocal, get_db
from app.database.models import Claim as DBClaim, Topic as DBTopic, BlogArticle
from sqlalchemy.orm import Session
from sqlalchemy import desc
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegraph", tags=["telegraph"])

# Telegraph API
TELEGRAPH_API_URL = "https://api.telegra.ph"

class TelegraphPage(BaseModel):
    """Telegraph page response"""
    path: str
    url: str
    title: str
    description: Optional[str] = None
    author_name: Optional[str] = None
    author_url: Optional[str] = None
    views: Optional[int] = None
    can_edit: Optional[bool] = None

class CreatePageRequest(BaseModel):
    """Request to create a Telegraph page"""
    title: str
    content: List[Dict[str, Any]]  # Telegraph content format
    author_name: Optional[str] = "FactCheckr MX"
    author_url: Optional[str] = None
    return_content: Optional[bool] = False

async def create_telegraph_account() -> str:
    """Create or get Telegraph account access token"""
    # Check if we have a stored token
    token = os.getenv("TELEGRAPH_ACCESS_TOKEN")
    
    if not token:
        # Create new account
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TELEGRAPH_API_URL}/createAccount",
                params={
                    "short_name": "FactCheckr MX",
                    "author_name": "FactCheckr MX",
                    "author_url": "https://factcheck.mx"
                }
            )
            response.raise_for_status()
            data = response.json()
            token = data.get("result", {}).get("access_token")
            
            if token:
                logger.info("Created new Telegraph account")
                # In production, store this token securely
                # For now, user should add to .env: TELEGRAPH_ACCESS_TOKEN=...
    
    return token

async def create_telegraph_page(
    title: str,
    content: List[Dict[str, Any]],
    author_name: str = "FactCheckr MX",
    author_url: Optional[str] = None
) -> TelegraphPage:
    """Create a page on Telegraph"""
    token = await create_telegraph_account()
    
    if not token:
        raise HTTPException(
            status_code=500,
            detail="Could not create or access Telegraph account"
        )
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAPH_API_URL}/createPage",
            params={"access_token": token},
            json={
                "title": title,
                "content": content,
                "author_name": author_name,
                "author_url": author_url or "https://factcheck.mx",
                "return_content": False
            }
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("ok"):
            result = data.get("result", {})
            return TelegraphPage(
                path=result.get("path"),
                url=result.get("url"),
                title=result.get("title"),
                description=result.get("description"),
                author_name=result.get("author_name"),
                author_url=result.get("author_url"),
                views=result.get("views"),
                can_edit=result.get("can_edit")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Telegraph API error: {data.get('error', 'Unknown error')}"
            )

def format_claim_for_telegraph(claim: DBClaim) -> Tuple[str, List[Dict[str, Any]]]:
    """Format claim as Telegraph article content"""
    status_emoji = {
        "Verified": "✅",
        "Debunked": "❌",
        "Misleading": "⚠️",
        "Unverified": "❓"
    }
    
    emoji = status_emoji.get(claim.status.value, "❓")
    title = f"{emoji} Verificación: {claim.claim_text[:100]}"
    
    # Build Telegraph content (HTML-like structure)
    # Telegraph uses a specific format: children can be strings or objects
    content = [
        {
            "tag": "h3",
            "children": [f"{emoji} {claim.status.value}"]
        },
        {
            "tag": "p",
            "children": [f"<strong>Afirmación:</strong> {claim.claim_text}"]
        }
    ]
    
    if claim.explanation:
        content.append({
            "tag": "h4",
            "children": ["Explicación"]
        })
        content.append({
            "tag": "p",
            "children": [claim.explanation]
        })
    
    if claim.evidence_sources:
        content.append({
            "tag": "h4",
            "children": ["Fuentes"]
        })
        for source in claim.evidence_sources:
            content.append({
                "tag": "p",
                "children": [{
                    "tag": "a",
                    "attrs": {"href": source},
                    "children": [source]
                }]
            })
    
    if claim.source:
        content.append({
            "tag": "hr"
        })
        content.append({
            "tag": "p",
            "children": [f"<strong>Fuente original:</strong> {claim.source.platform}"]
        })
        if claim.source.url:
            content.append({
                "tag": "p",
                "children": [{
                    "tag": "a",
                    "attrs": {"href": claim.source.url},
                    "children": ["Ver fuente original"]
                }]
            })
    
    # Add metadata
    content.append({
        "tag": "hr"
    })
    content.append({
        "tag": "p",
        "children": [f"<em>Verificado por FactCheckr MX - {claim.created_at.strftime('%d/%m/%Y') if claim.created_at else 'Fecha no disponible'}</em>"]
    })
    
    return title, content

def format_article_for_telegraph(article: BlogArticle) -> List[Dict[str, Any]]:
    """Format blog article as Telegraph content
    
    Converts markdown content to Telegraph format
    """
    content = []
    
    # Add title
    content.append({
        "tag": "h1",
        "children": [article.title]
    })
    
    # Add excerpt if available
    if article.excerpt:
        content.append({
            "tag": "p",
            "children": [f"<em>{article.excerpt}</em>"]
        })
        content.append({
            "tag": "hr"
        })
    
    # Parse markdown content and convert to Telegraph format
    # Simple markdown parser for common elements
    lines = article.content.split('\n')
    current_paragraph = []
    
    for line in lines:
        line = line.strip()
        
        if not line:
            # Empty line - flush current paragraph
            if current_paragraph:
                content.append({
                    "tag": "p",
                    "children": [" ".join(current_paragraph)]
                })
                current_paragraph = []
            continue
        
        # Headers
        if line.startswith('# '):
            if current_paragraph:
                content.append({
                    "tag": "p",
                    "children": [" ".join(current_paragraph)]
                })
                current_paragraph = []
            content.append({
                "tag": "h2",
                "children": [line[2:].strip()]
            })
        elif line.startswith('## '):
            if current_paragraph:
                content.append({
                    "tag": "p",
                    "children": [" ".join(current_paragraph)]
                })
                current_paragraph = []
            content.append({
                "tag": "h3",
                "children": [line[3:].strip()]
            })
        elif line.startswith('### '):
            if current_paragraph:
                content.append({
                    "tag": "p",
                    "children": [" ".join(current_paragraph)]
                })
                current_paragraph = []
            content.append({
                "tag": "h4",
                "children": [line[4:].strip()]
            })
        # Lists
        elif line.startswith('- ') or line.startswith('* '):
            if current_paragraph:
                content.append({
                    "tag": "p",
                    "children": [" ".join(current_paragraph)]
                })
                current_paragraph = []
            content.append({
                "tag": "li",
                "children": [line[2:].strip()]
            })
        # Bold text
        elif '**' in line:
            # Simple bold handling
            parts = re.split(r'\*\*(.*?)\*\*', line)
            children = []
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    if part:
                        children.append(part)
                else:
                    children.append({
                        "tag": "strong",
                        "children": [part]
                    })
            if current_paragraph:
                content.append({
                    "tag": "p",
                    "children": [" ".join(current_paragraph)]
                })
                current_paragraph = []
            content.append({
                "tag": "p",
                "children": children if children else [line]
            })
        # Links
        elif '[' in line and '](' in line:
            # Markdown link format: [text](url)
            link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
            matches = re.findall(link_pattern, line)
            if matches:
                if current_paragraph:
                    content.append({
                        "tag": "p",
                        "children": [" ".join(current_paragraph)]
                    })
                    current_paragraph = []
                # Replace links in line
                processed_line = line
                for text, url in matches:
                    processed_line = processed_line.replace(f"[{text}]({url})", text)
                # Add paragraph with links
                parts = re.split(link_pattern, line)
                children = []
                link_idx = 0
                for i, part in enumerate(parts):
                    if i % 3 == 0 and part:
                        children.append(part)
                    elif i % 3 == 1:
                        # Link text
                        url = parts[i + 1] if i + 1 < len(parts) else "#"
                        children.append({
                            "tag": "a",
                            "attrs": {"href": url},
                            "children": [part]
                        })
                content.append({
                    "tag": "p",
                    "children": children if children else [processed_line]
                })
            else:
                current_paragraph.append(line)
        else:
            # Regular paragraph text
            current_paragraph.append(line)
    
    # Flush remaining paragraph
    if current_paragraph:
        content.append({
            "tag": "p",
            "children": [" ".join(current_paragraph)]
        })
    
    # Add footer with link back to factcheck.mx
    content.append({
        "tag": "hr"
    })
    content.append({
        "tag": "p",
        "children": [
            "Lee el artículo completo en ",
            {
                "tag": "a",
                "attrs": {"href": f"https://factcheck.mx/blog/{article.slug}"},
                "children": ["FactCheckr MX"]
            }
        ]
    })
    content.append({
        "tag": "p",
        "children": [f"<em>Publicado el {article.published_at.strftime('%d/%m/%Y %H:%M') if article.published_at else 'Fecha no disponible'}</em>"]
    })
    
    return content

@router.post("/publish/{claim_id}")
async def publish_claim_to_telegraph(
    claim_id: str,
    db: Session = Depends(get_db)
) -> TelegraphPage:
    """Publish a fact-check claim to Telegraph"""
    claim = db.query(DBClaim).filter(DBClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    try:
        title, content = format_claim_for_telegraph(claim)
        page = await create_telegraph_page(
            title=title,
            content=content,
            author_name="FactCheckr MX",
            author_url="https://factcheck.mx"
        )
        
        logger.info(f"Published claim {claim_id} to Telegraph: {page.url}")
        return page
        
    except Exception as e:
        logger.error(f"Error publishing to Telegraph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/publish/batch")
async def publish_batch_to_telegraph(
    claim_ids: List[str],
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Publish multiple claims to Telegraph"""
    results = []
    
    for claim_id in claim_ids:
        try:
            page = await publish_claim_to_telegraph(claim_id, db)
            results.append({
                "claim_id": claim_id,
                "status": "success",
                "url": page.url,
                "path": page.path
            })
        except Exception as e:
            results.append({
                "claim_id": claim_id,
                "status": "error",
                "error": str(e)
            })
    
    return results

@router.get("/recent")
async def get_recent_claims_for_telegraph(
    limit: int = 10,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get recent claims formatted for Telegraph publishing"""
    query = db.query(DBClaim).order_by(desc(DBClaim.created_at))
    
    if status:
        from app.database.models import VerificationStatus
        try:
            status_enum = VerificationStatus[status.upper()]
            query = query.filter(DBClaim.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    claims = query.limit(limit).all()
    
    return {
        "claims": [
            {
                "id": claim.id,
                "title": claim.claim_text[:100],
                "status": claim.status.value,
                "created_at": str(claim.created_at) if claim.created_at else None,
                "telegraph_url": None  # Would be populated if already published
            }
            for claim in claims
        ]
    }

@router.post("/create-page")
async def create_custom_page(
    request: CreatePageRequest
) -> TelegraphPage:
    """Create a custom Telegraph page"""
    try:
        page = await create_telegraph_page(
            title=request.title,
            content=request.content,
            author_name=request.author_name or "FactCheckr MX",
            author_url=request.author_url
        )
        return page
    except Exception as e:
        logger.error(f"Error creating Telegraph page: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

