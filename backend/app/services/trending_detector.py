"""
Trending Topic Detection Service

Detects trending topics from social media signals by analyzing:
1. Engagement velocity (posts per hour)
2. Cross-platform correlation
3. Keyword clustering
4. Temporal patterns
"""
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from sqlalchemy import func, and_

from app.database.connection import SessionLocal
from app.database.models import Source, TrendingTopic

logger = logging.getLogger(__name__)


class TrendingDetector:
    """Detects trending topics from social media signals"""
    
    def __init__(self):
        self.time_window_hours = 6  # Analyze last 6 hours
        self.min_velocity_threshold = 5  # Minimum posts/hour to be considered trending
        self.min_cross_platform = 2  # Must appear on at least 2 platforms
    
    async def detect_trending_topics(
        self,
        time_window_hours: int = None,
        min_velocity: float = None
    ) -> List[Dict]:
        """Detect trending topics from recent sources
        
        Args:
            time_window_hours: Hours to look back (default: 6)
            min_velocity: Minimum posts/hour threshold (default: 5)
        
        Returns:
            List of trending topics with scores
        """
        time_window = time_window_hours or self.time_window_hours
        min_vel = min_velocity or self.min_velocity_threshold
        
        db = SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=time_window)
            
            # Get recent sources with engagement metrics
            recent_sources = db.query(Source).filter(
                and_(
                    Source.timestamp >= cutoff_time,
                    Source.processed.in_([0, 1])  # Pending or processed
                )
            ).all()
            
            if len(recent_sources) < 10:
                logger.info(f"Not enough sources ({len(recent_sources)}) for trending detection")
                return []
            
            # Analyze by platform
            platform_sources = defaultdict(list)
            for source in recent_sources:
                platform_sources[source.platform].append(source)
            
            # Calculate engagement velocity per platform
            platform_velocities = {}
            for platform, sources in platform_sources.items():
                if sources:
                    hours = time_window
                    velocity = len(sources) / hours
                    platform_velocities[platform] = {
                        'velocity': velocity,
                        'count': len(sources),
                        'avg_engagement': self._calculate_avg_engagement(sources)
                    }
            
            # Cluster sources by semantic similarity (topic detection)
            topics = await self._cluster_topics(recent_sources, platform_velocities)
            
            # Calculate cross-platform correlation
            for topic in topics:
                topic['cross_platform_correlation'] = self._calculate_cross_platform_correlation(
                    topic, platform_sources
                )
            
            # Filter by thresholds
            trending = [
                t for t in topics
                if t['engagement_velocity'] >= min_vel
                and t['cross_platform_correlation'] >= (self.min_cross_platform / max(len(platform_sources), 1))
            ]
            
            # Sort by final score
            trending.sort(key=lambda x: x['final_score'], reverse=True)
            
            logger.info(f"Detected {len(trending)} trending topics from {len(recent_sources)} sources")
            return trending[:20]  # Top 20 trending topics
            
        except Exception as e:
            logger.error(f"Error detecting trending topics: {e}", exc_info=True)
            return []
        finally:
            db.close()
    
    async def _cluster_topics(
        self,
        sources: List[Source],
        platform_velocities: Dict
    ) -> List[Dict]:
        """Cluster sources into topics using semantic similarity"""
        # Group by time windows (hourly buckets)
        hourly_buckets = defaultdict(list)
        for source in sources:
            hour_key = source.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_buckets[hour_key].append(source)
        
        topics = []
        
        # Analyze each hour bucket
        for hour, hour_sources in hourly_buckets.items():
            if len(hour_sources) < 3:
                continue
            
            # Extract keywords/phrases from sources
            keywords = await self._extract_keywords_from_sources(hour_sources)
            
            # Group by similar keywords (simple approach - can be enhanced with embeddings)
            keyword_groups = self._group_similar_keywords(keywords)
            
            for group_keywords, group_sources in keyword_groups.items():
                if len(group_sources) < 3:
                    continue
                
                # Calculate metrics
                velocity = len(group_sources) / 1.0  # Per hour
                avg_engagement = self._calculate_avg_engagement(group_sources)
                
                # Calculate trend score
                trend_score = self._calculate_trend_score(
                    velocity,
                    avg_engagement,
                    platform_velocities
                )
                
                topic = {
                    'topic_name': self._generate_topic_name(group_keywords),
                    'topic_keywords': list(group_keywords),
                    'detected_at': hour,
                    'engagement_velocity': velocity,
                    'trend_score': trend_score,
                    'source_count': len(group_sources),
                    'source_ids': [s.id for s in group_sources],
                    'platforms': list(set(s.platform for s in group_sources)),
                    'final_score': trend_score  # Will be updated with context intelligence
                }
                
                topics.append(topic)
        
        return topics
    
    async def _extract_keywords_from_sources(
        self,
        sources: List[Source]
    ) -> List[Tuple[str, Source]]:
        """Extract relevant keywords from source content"""
        # Simple keyword extraction (can be enhanced with NLP)
        keywords = []
        
        # Mexican political keywords to look for
        political_keywords = [
            'sheinbaum', 'amlo', 'morena', 'pan', 'pri', 'ine',
            'reforma', 'congreso', 'senado', 'suprema corte',
            'pemex', 'cfe', 'banxico', 'inflación', 'economía',
            'seguridad', 'violencia', 'migración', 'educación',
            'salud', 'corrupción', 'derechos humanos', 'justicia'
        ]
        
        for source in sources:
            content_lower = source.content.lower()
            found_keywords = [
                kw for kw in political_keywords
                if kw in content_lower
            ]
            
            # Also check for entity mentions if available in metadata
            if source.author_metadata and isinstance(source.author_metadata, dict):
                # Could extract entities from metadata if available
                pass
            
            if found_keywords:
                # Use most prominent keyword
                primary_keyword = found_keywords[0]
                keywords.append((primary_keyword, source))
        
        return keywords
    
    def _group_similar_keywords(
        self,
        keywords: List[Tuple[str, Source]]
    ) -> Dict[str, List[Source]]:
        """Group sources by similar keywords"""
        groups = defaultdict(list)
        
        for keyword, source in keywords:
            # Normalize keyword
            normalized = keyword.lower().strip()
            groups[normalized].append(source)
        
        return dict(groups)
    
    def _generate_topic_name(self, keywords: set) -> str:
        """Generate a human-readable topic name from keywords"""
        if len(keywords) == 1:
            return keywords.pop().title()
        
        # Combine keywords
        sorted_kw = sorted(list(keywords))[:3]  # Top 3
        return " / ".join([k.title() for k in sorted_kw])
    
    def _calculate_avg_engagement(self, sources: List[Source]) -> float:
        """Calculate average engagement across sources"""
        if not sources:
            return 0.0
        
        total_engagement = 0
        count = 0
        
        for source in sources:
            if source.engagement_metrics:
                metrics = source.engagement_metrics
                # Sum all engagement types
                engagement = (
                    metrics.get('likes', 0) +
                    metrics.get('retweets', 0) +
                    metrics.get('replies', 0) +
                    metrics.get('views', 0) * 0.1  # Views weighted less
                )
                total_engagement += engagement
                count += 1
        
        return total_engagement / count if count > 0 else 0.0
    
    def _calculate_trend_score(
        self,
        velocity: float,
        avg_engagement: float,
        platform_velocities: Dict
    ) -> float:
        """Calculate trend score (0.0-1.0)"""
        # Normalize velocity (assume max 100 posts/hour is very high)
        velocity_score = min(velocity / 100.0, 1.0)
        
        # Normalize engagement (assume max 10,000 total engagement is very high)
        engagement_score = min(avg_engagement / 10000.0, 1.0)
        
        # Weighted combination
        trend_score = (velocity_score * 0.6) + (engagement_score * 0.4)
        
        return round(trend_score, 3)
    
    def _calculate_cross_platform_correlation(
        self,
        topic: Dict,
        platform_sources: Dict[str, List[Source]]
    ) -> float:
        """Calculate how many platforms this topic appears on (0.0-1.0)"""
        topic_platforms = set(topic['platforms'])
        total_platforms = len(platform_sources)
        
        if total_platforms == 0:
            return 0.0
        
        return len(topic_platforms) / total_platforms
    
    async def store_trending_topics(self, topics: List[Dict]) -> List[TrendingTopic]:
        """Store detected trending topics in database"""
        from app.database.models import trending_topic_sources
        
        db = SessionLocal()
        stored_topics = []
        
        try:
            for topic_data in topics:
                # Check if similar topic already exists (within last hour)
                existing = db.query(TrendingTopic).filter(
                    and_(
                        TrendingTopic.topic_name == topic_data['topic_name'],
                        TrendingTopic.detected_at >= datetime.utcnow() - timedelta(hours=1)
                    )
                ).first()
                
                if existing:
                    # Update existing
                    existing.trend_score = topic_data['trend_score']
                    existing.engagement_velocity = topic_data['engagement_velocity']
                    existing.cross_platform_correlation = topic_data['cross_platform_correlation']
                    existing.final_priority_score = topic_data['final_score']
                    existing.updated_at = datetime.utcnow()
                    stored_topics.append(existing)
                else:
                    # Create new
                    topic = TrendingTopic(
                        topic_name=topic_data['topic_name'],
                        topic_keywords=topic_data['topic_keywords'],
                        detected_at=topic_data['detected_at'],
                        trend_score=topic_data['trend_score'],
                        engagement_velocity=topic_data['engagement_velocity'],
                        cross_platform_correlation=topic_data['cross_platform_correlation'],
                        final_priority_score=topic_data['final_score'],
                        status='active',
                        topic_metadata={
                            'source_count': topic_data['source_count'],
                            'platforms': topic_data['platforms']
                        }
                    )
                    db.add(topic)
                    db.flush()  # Get ID
                    
                    # Associate sources using the relationship
                    for source_id in topic_data['source_ids']:
                        # Check if source exists
                        source = db.query(Source).filter(Source.id == source_id).first()
                        if source:
                            # Add to relationship (SQLAlchemy handles the association table)
                            topic.sources.append(source)
                    
                    stored_topics.append(topic)
            
            db.commit()
            logger.info(f"Stored {len(stored_topics)} trending topics")
            return stored_topics
            
        except Exception as e:
            logger.error(f"Error storing trending topics: {e}", exc_info=True)
            db.rollback()
            return []
        finally:
            db.close()

