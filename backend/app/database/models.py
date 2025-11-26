from sqlalchemy import Column, String, DateTime, Text, Enum, Integer, ForeignKey, Table, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

# Association table for many-to-many relationship between claims and topics
claim_topics = Table(
    'claim_topics',
    Base.metadata,
    Column('claim_id', String, ForeignKey('claims.id')),
    Column('topic_id', Integer, ForeignKey('topics.id'))
)

class VerificationStatus(enum.Enum):
    VERIFIED = "Verified"
    DEBUNKED = "Debunked"
    MISLEADING = "Misleading"
    UNVERIFIED = "Unverified"

class SubscriptionTier(enum.Enum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    UNPAID = "unpaid"

class Source(Base):
    """Raw social media posts and news articles"""
    __tablename__ = 'sources'
    
    id = Column(String, primary_key=True)
    platform = Column(String, nullable=False)  # Twitter, Reddit, Google News, etc.
    content = Column(Text, nullable=False)
    author = Column(String)
    url = Column(String)
    timestamp = Column(DateTime, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Integer, default=0)  # 0 = pending, 1 = processed, 2 = skipped
    
    # Relationship
    claims = relationship("Claim", back_populates="source")

class Claim(Base):
    """Fact-checked claims with verification results"""
    __tablename__ = 'claims'
    
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey('sources.id'))
    original_text = Column(Text, nullable=False)
    claim_text = Column(Text, nullable=False)
    
    # Verification
    status = Column(Enum(VerificationStatus), nullable=False)
    explanation = Column(Text)
    evidence_sources = Column(JSON)  # List of URLs
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source = relationship("Source", back_populates="claims")
    topics = relationship("Topic", secondary=claim_topics, back_populates="claims")

class Topic(Base):
    """Categories for claims (Executive, Legislative, Judicial, Economy, etc.)"""
    __tablename__ = 'topics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)  # e.g., "Executive", "Judicial Reform"
    slug = Column(String, unique=True, nullable=False)  # e.g., "executive", "judicial-reform"
    description = Column(Text)
    
    # Relationships
    claims = relationship("Claim", secondary=claim_topics, back_populates="topics")

class Entity(Base):
    """Politicians, institutions, locations mentioned in claims"""
    __tablename__ = 'entities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)  # e.g., "Claudia Sheinbaum"
    entity_type = Column(String)  # "person", "institution", "location"
    extra_data = Column(JSON)  # Additional info (position, party, etc.)

class User(Base):
    """User accounts for authentication and subscriptions"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    
    # Profile
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    usage_records = relationship("UsageTracking", back_populates="user")

class Subscription(Base):
    """User subscription information linked to Stripe"""
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    
    # Stripe fields
    stripe_customer_id = Column(String, unique=True, index=True)
    stripe_subscription_id = Column(String, unique=True, index=True)
    stripe_price_id = Column(String)  # Stripe price ID for the tier
    
    # Subscription details
    tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    
    # Billing
    billing_cycle = Column(String)  # "month" or "year"
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    canceled_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="subscription")

class UsageTracking(Base):
    """Track user usage for rate limiting and billing"""
    __tablename__ = 'usage_tracking'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Usage type
    usage_type = Column(String, nullable=False, index=True)  # "verification", "api_call", "search", "export"
    
    # Counters
    count = Column(Integer, default=1)
    
    # Time period tracking (for daily/monthly limits)
    period_start = Column(DateTime, nullable=False, index=True)  # Start of billing period
    period_end = Column(DateTime, nullable=False)  # End of billing period
    date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)  # Specific date of usage
    
    # Metadata (renamed to avoid SQLAlchemy reserved word)
    usage_metadata = Column(JSON)  # Additional info (endpoint, claim_id, etc.)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="usage_records")
