from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

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

class VerificationResult(BaseModel):
    status: VerificationStatus
    explanation: str
    sources: List[str]

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
