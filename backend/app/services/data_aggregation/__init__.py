"""
Data Aggregation Service

Collects and aggregates data from multiple sources for market predictions:
- News articles (via Serper API + Claude Haiku)
- Social media sentiment (Twitter, embeddings-based)
- Cross-platform aggregation
"""

from .news_analyzer import NewsAnalyzer
from .twitter_sentiment import TwitterSentimentAnalyzer
from .noise_filter import NoiseFilter
from .aggregator import DataAggregator

__all__ = [
    "NewsAnalyzer",
    "TwitterSentimentAnalyzer", 
    "NoiseFilter",
    "DataAggregator",
]
