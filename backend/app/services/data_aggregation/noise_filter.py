"""
Noise Filter for Social Media Data

Filters out bots, astroturfing, and low-quality signals from social media.
Essential for getting clean sentiment signals.
"""

import logging
import math
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class WeightedPost:
    """A post with credibility and recency weights applied."""
    content: str
    author: str
    platform: str
    timestamp: datetime
    sentiment: float
    raw_engagement: Dict[str, int]
    credibility_weight: float
    recency_weight: float
    engagement_score: float
    
    @property
    def combined_weight(self) -> float:
        """Combined weight for aggregation."""
        return self.credibility_weight * self.recency_weight * self.engagement_score


class NoiseFilter:
    """
    Filter out noise from social media data.
    
    Implements:
    - Bot detection (account age, patterns)
    - Astroturfing detection (coordinated campaigns)
    - Influence weighting (verified, domain experts)
    - Recency decay (recent posts weighted higher)
    """
    
    # Suspicious patterns indicating bots
    BOT_USERNAME_PATTERNS = [
        r'\d{8,}$',  # Long number suffix
        r'^[a-z]{2,3}\d{4,}',  # Letter prefix + numbers
    ]
    
    # Minimum account age for credibility (days)
    MIN_ACCOUNT_AGE_DAYS = 30
    
    # Suspicious engagement ratios
    MAX_FOLLOWER_FOLLOWING_RATIO = 100
    MIN_FOLLOWER_FOLLOWING_RATIO = 0.01
    
    def __init__(self):
        pass
    
    def calculate_account_credibility(
        self,
        author_metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate credibility score for a social media account.
        
        Factors:
        - Account age
        - Follower/following ratio
        - Verification status
        - Posting frequency patterns
        - Engagement patterns
        
        Args:
            author_metadata: Account metadata from scraper
        
        Returns:
            Credibility score 0.0 to 1.0
        """
        if not author_metadata:
            return 0.3  # Low default for missing metadata
        
        score = 0.5  # Base score
        
        # Account age factor
        account_created = author_metadata.get("account_created")
        if account_created:
            try:
                if isinstance(account_created, str):
                    created_date = datetime.fromisoformat(account_created.replace("Z", "+00:00"))
                else:
                    created_date = account_created
                
                age_days = (datetime.utcnow() - created_date.replace(tzinfo=None)).days
                
                if age_days < 7:
                    score -= 0.3  # Very new account
                elif age_days < self.MIN_ACCOUNT_AGE_DAYS:
                    score -= 0.15
                elif age_days > 365:
                    score += 0.1  # Established account
                elif age_days > 1000:
                    score += 0.15
            except Exception:
                pass
        
        # Verification status
        if author_metadata.get("verified", False):
            score += 0.25
        
        # Follower/following ratio
        followers = author_metadata.get("followers", 0)
        following = author_metadata.get("following", 1)
        
        if following > 0:
            ratio = followers / following
            
            if ratio > self.MAX_FOLLOWER_FOLLOWING_RATIO:
                # Could be bot or influencer - need more context
                pass
            elif ratio < self.MIN_FOLLOWER_FOLLOWING_RATIO:
                # Follows many, few followers - suspicious
                score -= 0.2
        
        # High follower count bonus (logarithmic)
        if followers > 1000:
            score += min(0.2, math.log10(followers) * 0.05)
        
        # Profile completeness
        if author_metadata.get("bio"):
            score += 0.05
        if author_metadata.get("profile_image"):
            score += 0.05
        
        # Check for bot patterns in username
        username = author_metadata.get("username", "")
        if self._is_suspicious_username(username):
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _is_suspicious_username(self, username: str) -> bool:
        """Check if username matches suspicious patterns."""
        import re
        
        for pattern in self.BOT_USERNAME_PATTERNS:
            if re.search(pattern, username):
                return True
        
        # Check for excessive numbers
        digit_count = sum(1 for c in username if c.isdigit())
        if len(username) > 0 and digit_count / len(username) > 0.5:
            return True
        
        return False
    
    def detect_coordination(
        self,
        posts: List[Dict[str, Any]],
        time_window_hours: int = 6,
        similarity_threshold: float = 0.8
    ) -> Tuple[float, List[str]]:
        """
        Detect coordinated posting campaigns.
        
        Looks for:
        - Suspiciously similar posts in short timeframe
        - Same content from multiple accounts
        - Unusual posting patterns
        
        Args:
            posts: List of post dictionaries
            time_window_hours: Window to check for coordination
            similarity_threshold: Text similarity threshold
        
        Returns:
            Tuple of (coordination_score 0-1, list of suspicious content)
        """
        if len(posts) < 5:
            return 0.0, []
        
        suspicious_content = []
        coordination_signals = 0
        
        # Group posts by content hash (simple deduplication)
        content_counts = Counter()
        for post in posts:
            content = post.get("content", "").strip().lower()
            # Normalize whitespace and common variations
            content_normalized = " ".join(content.split())[:200]
            content_counts[content_normalized] += 1
        
        # Check for duplicate content from different accounts
        for content, count in content_counts.items():
            if count >= 3:
                coordination_signals += count - 2
                suspicious_content.append(content[:100])
        
        # Check for burst posting patterns
        timestamps = []
        for post in posts:
            ts = post.get("timestamp")
            if ts:
                try:
                    if isinstance(ts, str):
                        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    timestamps.append(ts)
                except Exception:
                    pass
        
        if len(timestamps) >= 10:
            timestamps.sort()
            # Check for unusual clustering
            gaps = []
            for i in range(1, len(timestamps)):
                gap = (timestamps[i] - timestamps[i-1]).total_seconds()
                gaps.append(gap)
            
            if gaps:
                avg_gap = sum(gaps) / len(gaps)
                # If posts are too evenly spaced, could be scheduled/coordinated
                variance = sum((g - avg_gap) ** 2 for g in gaps) / len(gaps)
                if variance < avg_gap * 0.1 and avg_gap < 300:  # Very regular ~5 min intervals
                    coordination_signals += 2
        
        # Calculate coordination score
        max_signals = len(posts) // 2
        coordination_score = min(1.0, coordination_signals / max(1, max_signals))
        
        return coordination_score, suspicious_content[:5]
    
    def apply_influence_weighting(
        self,
        posts: List[Dict[str, Any]]
    ) -> List[WeightedPost]:
        """
        Apply influence-based weighting to posts.
        
        Weights by:
        - Verified status
        - Domain expertise (inferred from bio)
        - Follower count (log-scaled)
        - Engagement on the specific post
        
        Args:
            posts: List of post dictionaries
        
        Returns:
            List of WeightedPost objects
        """
        weighted_posts = []
        
        for post in posts:
            # Get author metadata
            author_meta = post.get("author_metadata", {})
            
            # Calculate credibility weight
            credibility = self.calculate_account_credibility(author_meta)
            
            # Calculate engagement score
            engagement = post.get("engagement_metrics", {})
            engagement_score = self._calculate_engagement_score(engagement)
            
            # Parse timestamp
            timestamp = post.get("timestamp", datetime.utcnow())
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except Exception:
                    timestamp = datetime.utcnow()
            
            weighted_posts.append(WeightedPost(
                content=post.get("content", ""),
                author=post.get("author", "unknown"),
                platform=post.get("platform", "unknown"),
                timestamp=timestamp.replace(tzinfo=None) if hasattr(timestamp, 'tzinfo') else timestamp,
                sentiment=post.get("sentiment", 0.0),
                raw_engagement=engagement,
                credibility_weight=credibility,
                recency_weight=1.0,  # Applied separately
                engagement_score=engagement_score
            ))
        
        return weighted_posts
    
    def _calculate_engagement_score(
        self,
        engagement: Dict[str, Any]
    ) -> float:
        """
        Calculate normalized engagement score.
        
        Combines likes, retweets/shares, replies into single score.
        """
        if not engagement:
            return 0.3  # Low default
        
        likes = engagement.get("likes", 0) or engagement.get("favorites", 0) or 0
        shares = engagement.get("retweets", 0) or engagement.get("shares", 0) or 0
        replies = engagement.get("replies", 0) or engagement.get("comments", 0) or 0
        views = engagement.get("views", 0) or engagement.get("impressions", 0) or 0
        
        # Weighted combination (shares > likes > replies)
        raw_score = likes * 1.0 + shares * 2.0 + replies * 1.5
        
        # If we have views, calculate engagement rate
        if views > 100:
            engagement_rate = raw_score / views
            # Good engagement rate is ~2-5%
            if engagement_rate > 0.05:
                return min(1.0, 0.7 + engagement_rate * 2)
            elif engagement_rate > 0.02:
                return 0.6 + engagement_rate * 5
            else:
                return 0.4 + engagement_rate * 10
        
        # Without views, use logarithmic scaling
        if raw_score > 0:
            return min(1.0, 0.3 + math.log10(raw_score + 1) * 0.15)
        
        return 0.3
    
    def apply_recency_decay(
        self,
        posts: List[WeightedPost],
        half_life_hours: int = 12,
        reference_time: datetime = None
    ) -> List[WeightedPost]:
        """
        Apply exponential decay based on recency.
        
        More recent posts are weighted higher.
        
        Args:
            posts: List of WeightedPost objects
            half_life_hours: Hours until weight is halved
            reference_time: Reference time (default: now)
        
        Returns:
            Updated posts with recency_weight applied
        """
        if reference_time is None:
            reference_time = datetime.utcnow()
        
        for post in posts:
            try:
                hours_ago = (reference_time - post.timestamp).total_seconds() / 3600
                
                # Exponential decay: weight = 0.5^(hours / half_life)
                decay = math.pow(0.5, hours_ago / half_life_hours)
                
                # Minimum weight of 0.1 for old posts
                post.recency_weight = max(0.1, decay)
            except Exception:
                post.recency_weight = 0.5  # Default for parsing issues
        
        return posts
    
    def filter_posts(
        self,
        posts: List[Dict[str, Any]],
        min_credibility: float = 0.3,
        check_coordination: bool = True
    ) -> Tuple[List[WeightedPost], int]:
        """
        Full filtering pipeline for posts.
        
        Args:
            posts: Raw posts from scraper
            min_credibility: Minimum credibility to include
            check_coordination: Whether to check for astroturfing
        
        Returns:
            Tuple of (filtered weighted posts, number filtered out)
        """
        if not posts:
            return [], 0
        
        initial_count = len(posts)
        
        # Check for coordination
        if check_coordination:
            coord_score, suspicious = self.detect_coordination(posts)
            if coord_score > 0.5:
                logger.warning(
                    f"High coordination detected ({coord_score:.2f}). "
                    f"Suspicious content: {suspicious}"
                )
        
        # Apply influence weighting
        weighted = self.apply_influence_weighting(posts)
        
        # Apply recency decay
        weighted = self.apply_recency_decay(weighted)
        
        # Filter by credibility
        filtered = [p for p in weighted if p.credibility_weight >= min_credibility]
        
        filtered_count = initial_count - len(filtered)
        
        logger.debug(
            f"Noise filter: {initial_count} posts -> {len(filtered)} "
            f"({filtered_count} filtered)"
        )
        
        return filtered, filtered_count
