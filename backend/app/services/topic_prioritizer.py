"""
Hybrid Topic Prioritization Engine

Combines:
- Trending scores (from TrendingDetector)
- Keyword matches (from existing keyword system)
- Context relevance (from ContextIntelligence)
- Misinformation risk (from historical patterns)

Outputs prioritized queue for fact-checking.
"""
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.database.connection import SessionLocal
from app.database.models import (
    TrendingTopic, ContextIntelligence, TopicPriorityQueue,
    Source, Claim
)
from app.config.scraping_keywords import (
    HIGH_PRIORITY_KEYWORDS, MEDIUM_PRIORITY_KEYWORDS,
    LOW_PRIORITY_KEYWORDS, ALL_KEYWORDS
)
from app.services.trending_detector import TrendingDetector
from app.services.context_intelligence import ContextIntelligenceService

logger = logging.getLogger(__name__)


class TopicPrioritizer:
    """Hybrid prioritization engine"""
    
    def __init__(self):
        self.trending_detector = TrendingDetector()
        self.context_service = ContextIntelligenceService()
        
        # Weight configuration (can be tuned)
        self.weights = {
            'trending_score': 0.35,      # 35% - trending popularity
            'keyword_match': 0.25,       # 25% - matches important keywords
            'context_relevance': 0.25,    # 25% - Mexican context relevance
            'misinformation_risk': 0.15  # 15% - historical misinformation patterns
        }
    
    async def prioritize_topics(
        self,
        limit: int = 20
    ) -> List[Dict]:
        """Generate prioritized list of topics for fact-checking
        
        Args:
            limit: Maximum number of topics to return
        
        Returns:
            List of prioritized topics with scores
        """
        # 1. Get trending topics
        trending_topics = await self.trending_detector.detect_trending_topics()
        
        # 2. Get keyword-based topics (from existing system)
        keyword_topics = self._get_keyword_topics()
        
        # 3. Merge and deduplicate
        all_topics = self._merge_topics(trending_topics, keyword_topics)
        
        # 4. Calculate final priority scores
        prioritized = []
        
        for topic in all_topics:
            # Get context intelligence
            context = await self.context_service.assess_topic_relevance(
                topic_name=topic.get('topic_name', ''),
                topic_keywords=topic.get('topic_keywords', []),
                sample_content=topic.get('sample_content', [])
            )
            
            # Calculate keyword match score
            keyword_score = self._calculate_keyword_match_score(
                topic.get('topic_keywords', [])
            )
            
            # Calculate misinformation risk
            risk_score = await self._calculate_misinformation_risk(
                topic.get('topic_keywords', [])
            )
            
            # Calculate final priority score
            final_score = (
                (topic.get('trend_score', 0.0) * self.weights['trending_score']) +
                (keyword_score * self.weights['keyword_match']) +
                (context['relevance_score'] * self.weights['context_relevance']) +
                (risk_score * self.weights['misinformation_risk'])
            )
            
            prioritized.append({
                **topic,
                'context_intelligence': context,
                'keyword_match_score': keyword_score,
                'misinformation_risk_score': risk_score,
                'final_priority_score': round(final_score, 3),
                'should_fact_check': context.get('should_fact_check', final_score > 0.5)
            })
        
        # Sort by final priority score
        prioritized.sort(key=lambda x: x['final_priority_score'], reverse=True)
        
        # Store in priority queue
        await self._store_priority_queue(prioritized[:limit])
        
        return prioritized[:limit]
    
    def _get_keyword_topics(self) -> List[Dict]:
        """Get topics from existing keyword system"""
        # This simulates keyword-based topic detection
        # In reality, you'd analyze recent sources matching keywords
        
        keyword_topics = []
        
        # High priority keywords get boost
        for keyword in HIGH_PRIORITY_KEYWORDS:
            keyword_topics.append({
                'topic_name': keyword,
                'topic_keywords': [keyword],
                'trend_score': 0.8,  # High baseline for important keywords
                'source': 'keyword_system',
                'keyword_priority': 'high'
            })
        
        # Medium priority
        for keyword in MEDIUM_PRIORITY_KEYWORDS[:10]:  # Top 10
            keyword_topics.append({
                'topic_name': keyword,
                'topic_keywords': [keyword],
                'trend_score': 0.6,
                'source': 'keyword_system',
                'keyword_priority': 'medium'
            })
        
        return keyword_topics
    
    def _merge_topics(
        self,
        trending: List[Dict],
        keyword: List[Dict]
    ) -> List[Dict]:
        """Merge and deduplicate topics"""
        merged = {}
        
        # Add trending topics
        for topic in trending:
            key = self._topic_key(topic)
            merged[key] = topic
            merged[key]['source'] = 'trending'
        
        # Add keyword topics (may override if similar)
        for topic in keyword:
            key = self._topic_key(topic)
            if key in merged:
                # Merge: keep trending data but boost score if keyword match
                merged[key]['trend_score'] = max(
                    merged[key]['trend_score'],
                    topic['trend_score']
                )
                merged[key]['keyword_boost'] = True
            else:
                merged[key] = topic
        
        return list(merged.values())
    
    def _topic_key(self, topic: Dict) -> str:
        """Generate unique key for topic"""
        keywords = topic.get('topic_keywords', [])
        if keywords:
            return keywords[0].lower()
        return topic.get('topic_name', '').lower()
    
    def _calculate_keyword_match_score(self, keywords: List[str]) -> float:
        """Calculate how well topic matches important keywords"""
        if not keywords:
            return 0.0
        
        score = 0.0
        keyword_lower = [k.lower() for k in keywords]
        
        # Check against priority lists
        for kw in keyword_lower:
            if kw in [k.lower() for k in HIGH_PRIORITY_KEYWORDS]:
                score += 0.3
            elif kw in [k.lower() for k in MEDIUM_PRIORITY_KEYWORDS]:
                score += 0.2
            elif kw in [k.lower() for k in LOW_PRIORITY_KEYWORDS]:
                score += 0.1
        
        return min(score, 1.0)
    
    async def _calculate_misinformation_risk(
        self,
        keywords: List[str]
    ) -> float:
        """Calculate misinformation risk based on historical patterns"""
        db = SessionLocal()
        try:
            # Check historical debunk rate for similar topics
            # This is a simplified version - can be enhanced with embeddings
            
            if not keywords:
                return 0.5  # Default risk
            
            # Query for similar claims that were debunked
            from sqlalchemy import or_, func
            
            keyword_patterns = [f"%{kw.lower()}%" for kw in keywords]
            conditions = [Claim.claim_text.ilike(pattern) for pattern in keyword_patterns]
            
            # Get debunk rate for similar claims
            total_claims = db.query(func.count(Claim.id)).filter(
                or_(*conditions)
            ).scalar()
            
            if total_claims == 0:
                return 0.5  # No history, default risk
            
            debunked_claims = db.query(func.count(Claim.id)).filter(
                and_(
                    or_(*conditions),
                    Claim.status == 'Debunked'
                )
            ).scalar()
            
            debunk_rate = debunked_claims / total_claims if total_claims > 0 else 0.0
            
            # Higher debunk rate = higher misinformation risk
            return min(debunk_rate, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating misinformation risk: {e}")
            return 0.5
        finally:
            db.close()
    
    async def _store_priority_queue(self, prioritized_topics: List[Dict]):
        """Store prioritized topics in queue for processing"""
        db = SessionLocal()
        try:
            for topic_data in prioritized_topics:
                # Get or create trending topic
                topic_name = topic_data.get('topic_name')
                trending_topic = db.query(TrendingTopic).filter(
                    TrendingTopic.topic_name == topic_name
                ).order_by(TrendingTopic.detected_at.desc()).first()
                
                if not trending_topic:
                    # Create new trending topic
                    trending_topic = TrendingTopic(
                        topic_name=topic_name,
                        topic_keywords=topic_data.get('topic_keywords', []),
                        detected_at=datetime.utcnow(),
                        trend_score=topic_data.get('trend_score', 0.0),
                        engagement_velocity=topic_data.get('engagement_velocity', 0.0),
                        cross_platform_correlation=topic_data.get('cross_platform_correlation', 0.0),
                        context_relevance_score=topic_data.get('context_intelligence', {}).get('relevance_score', 0.0),
                        misinformation_risk_score=topic_data.get('misinformation_risk_score', 0.0),
                        final_priority_score=topic_data.get('final_priority_score', 0.0),
                        status='active',
                        topic_metadata=topic_data.get('topic_metadata', {})
                    )
                    db.add(trending_topic)
                    db.flush()
                
                # Check if already in queue
                existing = db.query(TopicPriorityQueue).filter(
                    and_(
                        TopicPriorityQueue.topic_id == trending_topic.id,
                        TopicPriorityQueue.processing_status == 'pending'
                    )
                ).first()
                
                if not existing:
                    # Add to queue
                    queue_entry = TopicPriorityQueue(
                        topic_id=trending_topic.id,
                        priority_score=topic_data.get('final_priority_score', 0.0),
                        processing_status='pending'
                    )
                    db.add(queue_entry)
            
            db.commit()
            logger.info(f"Stored {len(prioritized_topics)} topics in priority queue")
            
        except Exception as e:
            logger.error(f"Error storing priority queue: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()
    
    async def get_next_topics_to_process(self, limit: int = 10) -> List[TrendingTopic]:
        """Get next topics from priority queue for processing"""
        db = SessionLocal()
        try:
            queue_entries = db.query(TopicPriorityQueue).filter(
                TopicPriorityQueue.processing_status == 'pending'
            ).order_by(
                TopicPriorityQueue.priority_score.desc(),
                TopicPriorityQueue.queued_at.asc()
            ).limit(limit).all()
            
            topics = [entry.topic for entry in queue_entries]
            
            # Mark as processing
            for entry in queue_entries:
                entry.processing_status = 'processing'
                entry.processed_at = datetime.utcnow()
            
            db.commit()
            return topics
            
        except Exception as e:
            logger.error(f"Error getting next topics: {e}")
            db.rollback()
            return []
        finally:
            db.close()

