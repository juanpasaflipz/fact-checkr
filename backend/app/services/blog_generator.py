"""
Blog Article Generator Service
Generates AI-powered blog articles from fact-checking data analytics
"""
import os
import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func, case

from app.database.models import (
    Claim, Source, Topic, TrendingTopic,
    VerificationStatus, BlogArticle
)
from app.agent import FactChecker

logger = logging.getLogger(__name__)

# Free tier article limit
FREE_TIER_ARTICLE_LIMIT = int(os.getenv("BLOG_FREE_TIER_LIMIT", "3"))


class BlogArticleGenerator:
    """Generate blog articles from fact-checking data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.fact_checker = FactChecker()
    
    async def generate_morning_edition(self) -> BlogArticle:
        """Generate morning summary (9 AM) - covers last 12 hours"""
        hours_back = 12
        start_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Get data
        claims = self._get_recent_claims(start_time, limit=20)
        trending_topics = self._get_trending_topics(limit=5)
        top_debunked = self._get_top_claims_by_status(
            VerificationStatus.DEBUNKED, start_time, limit=5
        )
        
        data_context = {
            "period_hours": hours_back,
            "claims_count": len(claims),
            "top_claims": self._format_claims_for_context(claims[:10]),
            "trending_topics": [{"name": t.topic_name, "score": t.final_priority_score} for t in trending_topics],
            "top_debunked": self._format_claims_for_context(top_debunked)
        }
        
        # Generate content
        content = await self._generate_article_content(
            article_type="morning",
            data_context=data_context,
            claims=claims,
            trending_topics=trending_topics
        )
        
        return self._create_article(
            title=content["title"],
            excerpt=content["excerpt"],
            content=content["body"],
            article_type="morning",
            data_context=data_context
        )
    
    async def generate_afternoon_edition(self) -> BlogArticle:
        """Generate afternoon analysis (3 PM) - covers 6 AM to 12 PM"""
        # Calculate time window
        now = datetime.utcnow()
        start_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
        
        # Adjust if current time is before 12 PM
        if now.hour < 12:
            start_time = start_time - timedelta(days=1)
            end_time = end_time - timedelta(days=1)
        
        # Get data
        claims = self._get_claims_in_window(start_time, end_time, limit=25)
        
        # Get topic distribution (last 6 hours = 0.25 days)
        topic_dist = await self._get_topic_distribution(days=0.25, limit=10)
        platform_dist = await self._get_platform_distribution(days=0.25)
        
        # Select topic for deep-dive (highest claim count)
        deep_dive_topic = topic_dist["topics"][0] if topic_dist.get("topics") else None
        
        data_context = {
            "period": "6 AM - 12 PM",
            "claims_count": len(claims),
            "topic_distribution": topic_dist,
            "platform_distribution": platform_dist,
            "deep_dive_topic": deep_dive_topic
        }
        
        content = await self._generate_article_content(
            article_type="afternoon",
            data_context=data_context,
            claims=claims,
            deep_dive_topic=deep_dive_topic
        )
        
        return self._create_article(
            title=content["title"],
            excerpt=content["excerpt"],
            content=content["body"],
            article_type="afternoon",
            data_context=data_context,
            topic_id=deep_dive_topic["topic_id"] if deep_dive_topic else None
        )
    
    async def generate_evening_edition(self) -> BlogArticle:
        """Generate evening summary (9 PM) - covers full day"""
        start_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get full day data
        claims = self._get_recent_claims(start_time, limit=50)
        top_viral = self._get_top_viral_claims(start_time, limit=10)
        verification_stats = self._get_verification_stats(start_time)
        
        data_context = {
            "period": "Full day",
            "total_claims": len(claims),
            "top_viral": self._format_claims_for_context(top_viral),
            "verification_stats": verification_stats
        }
        
        content = await self._generate_article_content(
            article_type="evening",
            data_context=data_context,
            claims=claims,
            top_viral=top_viral
        )
        
        return self._create_article(
            title=content["title"],
            excerpt=content["excerpt"],
            content=content["body"],
            article_type="evening",
            data_context=data_context
        )
    
    async def generate_breaking_news_edition(self) -> BlogArticle:
        """Generate breaking news check (11:30 PM) - last 6 hours"""
        hours_back = 6
        start_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Get only high-engagement recent claims
        claims = self._get_high_engagement_claims(start_time, limit=15)
        
        data_context = {
            "period_hours": hours_back,
            "claims_count": len(claims),
            "breaking_claims": self._format_claims_for_context(claims)
        }
        
        content = await self._generate_article_content(
            article_type="breaking",
            data_context=data_context,
            claims=claims
        )
        
        return self._create_article(
            title=content["title"],
            excerpt=content["excerpt"],
            content=content["body"],
            article_type="breaking",
            data_context=data_context
        )
    
    async def _generate_article_content(
        self,
        article_type: str,
        data_context: Dict,
        **kwargs
    ) -> Dict[str, str]:
        """Use LLM to generate article content"""
        
        system_prompt = """Eres un periodista profesional especializado en fact-checking 
        político mexicano. Escribe artículos claros, atractivos y objetivos en español. 
        Mantén integridad periodística y cita datos específicos. Usa un tono profesional 
        pero accesible."""
        
        # Build context string
        context_str = json.dumps(data_context, indent=2, ensure_ascii=False)
        
        # Article type specific prompts
        prompts = {
            "morning": f"""
            Escribe un resumen matutino de verificación de hechos.
            
            CONTEXTO:
            {context_str}
            
            ESTRUCTURA:
            1. Título atractivo (máx 80 caracteres)
            2. Introducción (2-3 párrafos sobre lo más importante de la noche)
            3. Sección: "Lo Más Viral" (top 3 claims con más engagement)
            4. Sección: "Tendencias" (topics trending)
            5. Sección: "Desmentidos Destacados" (top debunked)
            6. Conclusión con takeaways clave
            
            FORMATO JSON:
            {{
                "title": "...",
                "excerpt": "... (máx 200 caracteres)",
                "body": "# Título\\n\\n[contenido en markdown]"
            }}
            """,
            
            "afternoon": f"""
            Escribe un análisis del día de verificación de hechos.
            
            CONTEXTO:
            {context_str}
            
            ESTRUCTURA:
            1. Título atractivo
            2. Introducción con estadísticas del día
            3. Análisis profundo del topic principal
            4. Comparación de plataformas (Twitter vs YouTube vs News)
            5. Patrones de verificación observados
            6. Conclusión
            
            FORMATO JSON:
            {{
                "title": "...",
                "excerpt": "...",
                "body": "# Título\\n\\n[contenido en markdown]"
            }}
            """,
            
            "evening": f"""
            Escribe un resumen vespertino completo del día.
            
            CONTEXTO:
            {context_str}
            
            ESTRUCTURA:
            1. Título atractivo
            2. Resumen ejecutivo del día
            3. Top 10 claims más virales
            4. Estadísticas de verificación (Verified vs Debunked)
            5. Insights y patrones
            6. Conclusión
            
            FORMATO JSON:
            {{
                "title": "...",
                "excerpt": "...",
                "body": "# Título\\n\\n[contenido en markdown]"
            }}
            """,
            
            "breaking": f"""
            Escribe un artículo breve de breaking news fact-checking.
            
            CONTEXTO:
            {context_str}
            
            ESTRUCTURA:
            1. Título urgente pero preciso
            2. Introducción breve
            3. Lista de verificaciones recientes (últimas 6 horas)
            4. Conclusión rápida
            
            FORMATO JSON:
            {{
                "title": "...",
                "excerpt": "...",
                "body": "# Título\\n\\n[contenido en markdown]"
            }}
            """
        }
        
        user_prompt = prompts.get(article_type, prompts["morning"])
        
        # Use existing FactChecker's LLM client
        if self.fact_checker.anthropic_client:
            try:
                response = self.fact_checker.anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4000,
                    temperature=0.7,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                content = response.content[0].text.strip()
            except Exception as e:
                logger.error(f"Anthropic API error: {e}")
                content = None
        else:
            content = None
        
        # Fallback to OpenAI
        if not content and self.fact_checker.openai_client:
            try:
                response = self.fact_checker.openai_client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=4000,
                    temperature=0.7,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                content = response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                content = None
        
        # Parse JSON response
        if content:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON from LLM response")
        
        # Fallback if JSON parsing fails
        return {
            "title": f"Resumen de Verificación - {article_type}",
            "excerpt": "Análisis de claims verificados",
            "body": content or f"# Resumen de Verificación\n\nContenido generado para {article_type}"
        }
    
    def _get_recent_claims(self, start_time: datetime, limit: int = 20) -> List[Claim]:
        """Get recent claims with sources"""
        return self.db.query(Claim).join(Source).filter(
            Claim.created_at >= start_time
        ).order_by(desc(Claim.created_at)).limit(limit).all()
    
    def _get_claims_in_window(self, start_time: datetime, end_time: datetime, limit: int = 25) -> List[Claim]:
        """Get claims within a time window"""
        return self.db.query(Claim).join(Source).filter(
            and_(
                Claim.created_at >= start_time,
                Claim.created_at <= end_time
            )
        ).order_by(desc(Claim.created_at)).limit(limit).all()
    
    def _get_top_viral_claims(self, start_time: datetime, limit: int = 10) -> List[Claim]:
        """Get claims with highest engagement"""
        claims = self.db.query(Claim).join(Source).filter(
            and_(
                Claim.created_at >= start_time,
                Source.engagement_metrics.isnot(None)
            )
        ).all()
        
        # Calculate engagement score and sort
        scored_claims = []
        for claim in claims:
            engagement = claim.source.engagement_metrics or {}
            score = (
                engagement.get('likes', 0) +
                engagement.get('retweets', 0) * 2 +
                engagement.get('replies', 0) * 1.5 +
                engagement.get('views', 0) * 0.1
            )
            scored_claims.append((score, claim))
        
        scored_claims.sort(reverse=True, key=lambda x: x[0])
        return [claim for _, claim in scored_claims[:limit]]
    
    def _get_high_engagement_claims(self, start_time: datetime, limit: int = 15) -> List[Claim]:
        """Get only high-engagement claims for breaking news"""
        return self._get_top_viral_claims(start_time, limit=limit)
    
    def _get_trending_topics(self, limit: int = 5) -> List[TrendingTopic]:
        """Get trending topics"""
        return self.db.query(TrendingTopic).filter(
            TrendingTopic.status == 'active'
        ).order_by(desc(TrendingTopic.final_priority_score)).limit(limit).all()
    
    def _get_top_claims_by_status(
        self,
        status: VerificationStatus,
        start_time: datetime,
        limit: int = 5
    ) -> List[Claim]:
        """Get top claims by verification status"""
        return self.db.query(Claim).join(Source).filter(
            and_(
                Claim.created_at >= start_time,
                Claim.status == status
            )
        ).order_by(desc(Claim.created_at)).limit(limit).all()
    
    def _get_verification_stats(self, start_time: datetime) -> Dict[str, int]:
        """Get verification statistics"""
        stats = self.db.query(
            Claim.status,
            func.count(Claim.id).label('count')
        ).filter(
            Claim.created_at >= start_time
        ).group_by(Claim.status).all()
        
        return {str(stat.status): stat.count for stat in stats}
    
    async def _get_topic_distribution(self, days: float, limit: int = 10) -> Dict:
        """Get topic distribution (similar to analytics endpoint)"""
        from app.database.models import VerificationStatus as VS
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        total_claims = self.db.query(func.count(Claim.id)).filter(
            Claim.created_at >= start_date
        ).scalar() or 1
        
        topic_data = self.db.query(
            Topic.id,
            Topic.name,
            Topic.slug,
            func.count(Claim.id).label('claim_count'),
            func.sum(case((Claim.status == VS.VERIFIED, 1), else_=0)).label('verified_count'),
            func.sum(case((Claim.status == VS.DEBUNKED, 1), else_=0)).label('debunked_count'),
        ).join(
            Claim.topics, isouter=True
        ).filter(
            Claim.created_at >= start_date
        ).group_by(
            Topic.id, Topic.name, Topic.slug
        ).order_by(
            desc('claim_count')
        ).limit(limit).all()
        
        topics = []
        for t in topic_data:
            topics.append({
                "topic_id": t.id,
                "topic_name": t.name,
                "topic_slug": t.slug,
                "claim_count": t.claim_count or 0,
                "verified_count": int(t.verified_count or 0),
                "debunked_count": int(t.debunked_count or 0),
            })
        
        return {"topics": topics, "total_claims": total_claims}
    
    async def _get_platform_distribution(self, days: float) -> Dict:
        """Get platform distribution"""
        from app.database.models import VerificationStatus as VS
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        platform_data = self.db.query(
            Source.platform,
            func.count(Source.id).label('total_count'),
            func.sum(case((Claim.status == VS.VERIFIED, 1), else_=0)).label('verified_count'),
            func.sum(case((Claim.status == VS.DEBUNKED, 1), else_=0)).label('debunked_count'),
        ).join(
            Claim, Claim.source_id == Source.id, isouter=True
        ).filter(
            Source.scraped_at >= start_date
        ).group_by(
            Source.platform
        ).order_by(
            desc('total_count')
        ).all()
        
        platforms = []
        for p in platform_data:
            platforms.append({
                "platform": p.platform,
                "total_count": int(p.total_count or 0),
                "verified_count": int(p.verified_count or 0),
                "debunked_count": int(p.debunked_count or 0),
            })
        
        return {"platforms": platforms}
    
    def _format_claims_for_context(self, claims: List[Claim]) -> List[Dict]:
        """Format claims for LLM context"""
        result = []
        for claim in claims:
            engagement = claim.source.engagement_metrics or {} if claim.source else {}
            result.append({
                "claim_text": claim.claim_text[:200],
                "status": str(claim.status),
                "explanation": claim.explanation[:300] if claim.explanation else "",
                "engagement": {
                    "likes": engagement.get('likes', 0),
                    "retweets": engagement.get('retweets', 0),
                    "views": engagement.get('views', 0)
                },
                "url": claim.source.url if claim.source else None
            })
        return result
    
    def _create_article(
        self,
        title: str,
        excerpt: str,
        content: str,
        article_type: str,
        data_context: Dict,
        topic_id: Optional[int] = None
    ) -> BlogArticle:
        """Create and save article to database"""
        try:
            from slugify import slugify
        except ImportError:
            # Fallback slugify implementation
            def slugify(text):
                text = text.lower()
                text = re.sub(r'[^\w\s-]', '', text)
                text = re.sub(r'[-\s]+', '-', text)
                return text.strip('-')
        
        # Generate slug
        base_slug = slugify(title)
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M")
        slug = f"{base_slug}-{timestamp}"
        
        # Ensure uniqueness
        existing = self.db.query(BlogArticle).filter(BlogArticle.slug == slug).first()
        if existing:
            slug = f"{base_slug}-{timestamp}-{existing.id + 1}"
        
        # Get next edition number
        last_edition = self.db.query(BlogArticle).filter(
            BlogArticle.article_type == article_type
        ).order_by(desc(BlogArticle.created_at)).first()
        
        edition_number = (last_edition.edition_number + 1) if last_edition and last_edition.edition_number else 1
        
        # Check if auto-publish is enabled
        auto_publish = os.getenv("AUTO_PUBLISH_BLOG", "false").lower() == "true"
        
        article = BlogArticle(
            title=title,
            slug=slug,
            excerpt=excerpt,
            content=content,
            article_type=article_type,
            edition_number=edition_number,
            data_context=data_context,
            topic_id=topic_id,
            published=auto_publish  # Auto-publish if configured
        )
        
        # Set published_at if auto-publishing
        if auto_publish:
            article.published_at = datetime.utcnow()
        
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        
        logger.info(f"Created blog article: {slug} (type: {article_type}, edition: {edition_number})")
        return article

