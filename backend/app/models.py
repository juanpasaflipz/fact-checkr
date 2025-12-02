from pydantic import BaseModel
from typing import List, Optional, Literal
from enum import Enum
from datetime import datetime

class VerificationStatus(str, Enum):
    VERIFIED = "Verified"
    DEBUNKED = "Debunked"
    MISLEADING = "Misleading"
    UNVERIFIED = "Unverified"

class SocialPost(BaseModel):
    id: str
    platform: str
    content: str
    author: str
    timestamp: str
    url: str
    # Enhanced data fields (optional, for Twitter Basic tier and other platforms)
    engagement_metrics: Optional[dict] = None  # {likes, retweets, replies, views, etc.}
    author_metadata: Optional[dict] = None  # {username, verified, followers, etc.}
    media_urls: Optional[list] = None  # [image_urls, video_urls]
    context_data: Optional[dict] = None  # {thread_id, parent_id, is_reply, etc.}

class VerificationResult(BaseModel):
    status: VerificationStatus
    explanation: str
    sources: List[str]
    confidence: float = 0.5  # Confidence score 0.0-1.0
    evidence_strength: Optional[str] = None  # "strong|moderate|weak|insufficient"
    key_evidence_points: Optional[List[str]] = None  # Key points from evidence

class Topic(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None

class Claim(BaseModel):
    id: str
    original_text: str
    claim_text: str
    verification: Optional[VerificationResult] = None
    source_post: Optional[SocialPost] = None
    topics: List[Topic] = []
    market: Optional['MarketSummary'] = None

class Source(BaseModel):
    id: str
    platform: str
    content: str
    author: Optional[str] = None
    url: Optional[str] = None
    timestamp: str
    scraped_at: str
    processed: int  # 0 = pending, 1 = processed, 2 = skipped
    claim_count: int = 0  # Number of claims from this source

# Prediction Market Schemas
class MarketSummary(BaseModel):
    id: int
    slug: str
    question: str
    yes_probability: float
    no_probability: float
    volume: float
    closes_at: Optional[datetime] = None
    status: str  # "open", "resolved", "cancelled"
    claim_id: Optional[str] = None
    category: Optional[str] = None  # politics, economy, security, rights, environment, mexico-us-relations, institutions

    class Config:
        from_attributes = True

class MarketDetail(BaseModel):
    id: int
    slug: str
    question: str
    description: Optional[str] = None
    yes_probability: float
    no_probability: float
    yes_liquidity: float
    no_liquidity: float
    volume: float
    created_at: datetime
    closes_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    status: str
    winning_outcome: Optional[str] = None
    resolution_source: Optional[str] = None
    resolution_criteria: Optional[str] = None
    claim_id: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True

class TradeRequest(BaseModel):
    amount: float
    outcome: Literal["yes", "no"]

class TradeResponse(BaseModel):
    shares: float
    price: float
    cost: float
    market: MarketSummary
    user_balance: float

class UserBalanceResponse(BaseModel):
    available_credits: float
    locked_credits: float

class CreateMarketRequest(BaseModel):
    question: str
    description: Optional[str] = None
    claim_id: Optional[str] = None
    closes_at: Optional[datetime] = None
    category: Optional[str] = None  # politics, economy, security, rights, environment, mexico-us-relations, institutions
    resolution_criteria: Optional[str] = None  # Transparent resolution rules

class ResolveMarketRequest(BaseModel):
    winning_outcome: Literal["yes", "no"]
    resolution_source: Optional[str] = None
