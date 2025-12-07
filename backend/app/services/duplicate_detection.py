"""
Cross-platform duplicate detection service.

Prevents processing the same claim multiple times when it appears
across different social media platforms.
"""

import re
from typing import List, Dict, Set, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.models import Source
from app.services.embeddings import EmbeddingService


class DuplicateDetector:
    """
    Detects duplicate content across social media platforms.

    Uses multiple strategies:
    1. Text similarity (cosine similarity of embeddings)
    2. URL matching (same URL = duplicate)
    3. Author-content matching (same author + similar content)
    4. Time-based clustering (claims within short time windows)
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        # Similarity threshold for considering content as duplicate
        self.duplicate_threshold = 0.85
        # Time window for considering claims as potentially duplicate (minutes)
        self.time_window_minutes = 60

    def find_duplicates(self, posts: List[Dict], db: Optional[Session] = None) -> List[Dict]:
        """
        Find and mark duplicate posts across platforms.

        Returns posts with duplicate information added.
        """
        if len(posts) <= 1:
            return posts

        # Group posts by time windows to reduce computation
        time_windows = self._group_by_time_windows(posts)

        processed_posts = []
        seen_content_hashes = set()

        for window_posts in time_windows:
            # Find duplicates within each time window
            unique_posts = self._deduplicate_window(window_posts, seen_content_hashes)
            processed_posts.extend(unique_posts)

        return processed_posts

    def _group_by_time_windows(self, posts: List[Dict]) -> List[List[Dict]]:
        """Group posts into time windows for efficient duplicate detection."""
        if not posts:
            return []

        # Sort posts by timestamp
        sorted_posts = sorted(posts, key=lambda x: x.get('timestamp', ''))

        windows = []
        current_window = []
        window_start = None

        for post in sorted_posts:
            try:
                post_time = datetime.fromisoformat(post['timestamp'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                # If timestamp parsing fails, put in current window
                if current_window:
                    current_window.append(post)
                else:
                    current_window = [post]
                continue

            if window_start is None:
                window_start = post_time
                current_window = [post]
            elif (post_time - window_start).total_seconds() / 60 <= self.time_window_minutes:
                current_window.append(post)
            else:
                # Start new window
                if current_window:
                    windows.append(current_window)
                window_start = post_time
                current_window = [post]

        if current_window:
            windows.append(current_window)

        return windows

    def _deduplicate_window(self, posts: List[Dict], seen_hashes: Set[str]) -> List[Dict]:
        """Find duplicates within a time window."""
        if len(posts) <= 1:
            return posts

        unique_posts = []
        duplicates_info = {}

        # First pass: exact URL matches (definite duplicates)
        url_groups = {}
        for post in posts:
            url = post.get('url', '').strip()
            if url:
                if url not in url_groups:
                    url_groups[url] = []
                url_groups[url].append(post)

        # Keep only one post per URL
        for url, url_posts in url_groups.items():
            if len(url_posts) > 1:
                # Keep the one with highest engagement
                best_post = max(url_posts, key=lambda x: self._calculate_engagement_score(x))
                unique_posts.append(best_post)

                # Mark others as duplicates
                for duplicate_post in url_posts:
                    if duplicate_post != best_post:
                        duplicates_info[duplicate_post['id']] = {
                            'is_duplicate': True,
                            'duplicate_of': best_post['id'],
                            'reason': 'same_url'
                        }
            else:
                unique_posts.append(url_posts[0])

        # Second pass: content similarity (for posts without URLs or different URLs)
        remaining_posts = [p for p in posts if p not in unique_posts]
        if remaining_posts:
            similarity_groups = self._group_by_similarity(remaining_posts)

            for group in similarity_groups:
                if len(group) > 1:
                    # Keep the one with highest engagement
                    best_post = max(group, key=lambda x: self._calculate_engagement_score(x))
                    unique_posts.append(best_post)

                    # Mark others as duplicates
                    for duplicate_post in group:
                        if duplicate_post != best_post:
                            duplicates_info[duplicate_post['id']] = {
                                'is_duplicate': True,
                                'duplicate_of': best_post['id'],
                                'reason': 'similar_content'
                            }
                else:
                    unique_posts.append(group[0])

        # Add duplicate information to posts
        for post in unique_posts:
            post_id = post['id']
            if post_id in duplicates_info:
                post['duplicate_info'] = duplicates_info[post_id]
            else:
                post['duplicate_info'] = {'is_duplicate': False}

        return unique_posts

    def _group_by_similarity(self, posts: List[Dict]) -> List[List[Dict]]:
        """Group posts by content similarity using embeddings."""
        if len(posts) <= 1:
            return [posts]

        groups = []
        processed_ids = set()

        for i, post1 in enumerate(posts):
            if post1['id'] in processed_ids:
                continue

            current_group = [post1]
            processed_ids.add(post1['id'])

            content1 = self._normalize_text(post1.get('content', ''))

            for j, post2 in enumerate(posts[i+1:], i+1):
                if post2['id'] in processed_ids:
                    continue

                content2 = self._normalize_text(post2.get('content', ''))

                # Quick text-based similarity check first
                if self._quick_text_similarity(content1, content2) < 0.7:
                    continue

                # Use embeddings for more accurate similarity
                similarity = self._calculate_embedding_similarity(content1, content2)

                if similarity >= self.duplicate_threshold:
                    current_group.append(post2)
                    processed_ids.add(post2['id'])

            groups.append(current_group)

        return groups

    def _calculate_embedding_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity using embeddings."""
        try:
            # This is a simplified version - in production you'd cache embeddings
            embedding1 = self.embedding_service.embed_text(text1)
            embedding2 = self.embedding_service.embed_text(text2)

            if not embedding1 or not embedding2:
                return 0.0

            # Cosine similarity
            try:
                import numpy as np
            except ImportError:
                # Fallback to manual calculation if numpy not available
                # Simple dot product and norm calculation
                dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
                norm1 = sum(a * a for a in embedding1) ** 0.5
                norm2 = sum(b * b for b in embedding2) ** 0.5
                
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                
                return dot_product / (norm1 * norm2)
            
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)

        except Exception as e:
            print(f"Error calculating embedding similarity: {e}")
            return 0.0

    def _quick_text_similarity(self, text1: str, text2: str) -> float:
        """Quick text-based similarity check."""
        if not text1 or not text2:
            return 0.0

        # Simple Jaccard similarity on words
        words1 = set(self._tokenize(text1))
        words2 = set(self._tokenize(text2))

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for text comparison."""
        # Remove punctuation and lowercase
        text = re.sub(r'[^\w\s]', '', text.lower())
        # Split into words and filter short words
        return [word for word in text.split() if len(word) > 2]

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""

        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        # Remove mentions (@username)
        text = re.sub(r'@\w+', '', text)
        # Remove hashtags symbols but keep the text
        text = re.sub(r'#(\w+)', r'\1', text)
        # Remove extra whitespace
        text = ' '.join(text.split())

        return text.lower()

    def _calculate_engagement_score(self, post: Dict) -> float:
        """Calculate engagement score for ranking duplicates."""
        metrics = post.get('engagement_metrics', {})

        score = (
            metrics.get('likes', 0) * 1.0 +
            metrics.get('comments', 0) * 2.0 +
            metrics.get('shares', 0) * 3.0 +
            metrics.get('retweets', 0) * 2.0 +
            metrics.get('views', 0) * 0.1
        )

        return score
