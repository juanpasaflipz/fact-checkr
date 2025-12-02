from sqlalchemy import Column, String, DateTime, Text, Enum, Integer, ForeignKey, Table, JSON, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


def enum_values(enum_cls: enum.EnumMeta):
    """Return enum values so Postgres bindings match lowercase enums already stored."""
    return [member.value for member in enum_cls]

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

class MarketStatus(enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"

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
    
    # Enhanced data fields (for Twitter Basic tier and other platforms)
    engagement_metrics = Column(JSON, nullable=True)  # {likes, retweets, replies, views, etc.}
    author_metadata = Column(JSON, nullable=True)  # {username, verified, followers, account_created, etc.}
    media_urls = Column(JSON, nullable=True)  # [image_urls, video_urls, thumbnails]
    context_data = Column(JSON, nullable=True)  # {thread_id, parent_id, is_reply, is_retweet, etc.}
    credibility_score = Column(Float, nullable=True, default=0.5)  # Source reliability score
    
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
    
    # Enhanced verification fields
    confidence = Column(Float, nullable=True)  # Confidence score 0.0-1.0
    evidence_strength = Column(String, nullable=True)  # "strong|moderate|weak|insufficient"
    key_evidence_points = Column(JSON, nullable=True)  # Key evidence points
    needs_review = Column(Boolean, default=False)  # Flag for human review
    review_priority = Column(String, nullable=True)  # "high|medium|low"
    agent_findings = Column(JSON, nullable=True)  # Multi-agent analysis results
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source = relationship("Source", back_populates="claims")
    topics = relationship("Topic", secondary=claim_topics, back_populates="claims")
    markets = relationship("Market", back_populates="claim")

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
    is_admin = Column(Boolean, default=False)
    
    # Preferences for personalization
    preferred_categories = Column(JSON, nullable=True)  # Array of category strings
    onboarding_completed = Column(Boolean, default=False, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    usage_records = relationship("UsageTracking", back_populates="user")
    balance = relationship("UserBalance", back_populates="user", uselist=False)
    market_trades = relationship("MarketTrade", back_populates="user")

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

class Market(Base):
    """Prediction markets for claims - binary YES/NO markets"""
    __tablename__ = 'markets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    question = Column(String, nullable=False)
    description = Column(Text)
    
    # Link to claim (optional)
    claim_id = Column(String, ForeignKey('claims.id'), nullable=True, index=True)
    
    # Category for filtering (politics, economy, security, rights, environment, mexico-us-relations, institutions)
    category = Column(String, nullable=True, index=True)
    
    # Market status
    status = Column(
        Enum(
            MarketStatus,
            name="marketstatus",
            values_callable=enum_values
        ),
        default=MarketStatus.OPEN,
        nullable=False
    )
    
    # Liquidity for CPMM (Constant Product Market Maker)
    yes_liquidity = Column(Float, default=1000.0, nullable=False)
    no_liquidity = Column(Float, default=1000.0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    closes_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Resolution
    winning_outcome = Column(String, nullable=True)  # "yes" or "no"
    resolution_source = Column(String, nullable=True)  # Official data source (INEGI, INE, SESNSP, Banxico, etc.)
    resolution_criteria = Column(Text, nullable=True)  # Transparent resolution rules
    
    # Relationships
    claim = relationship("Claim", back_populates="markets")
    trades = relationship("MarketTrade", back_populates="market")

class UserBalance(Base):
    """User credit balances for prediction markets"""
    __tablename__ = 'user_balances'
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    available_credits = Column(Float, default=0.0, nullable=False)
    locked_credits = Column(Float, default=0.0, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="balance")

class MarketTrade(Base):
    """Individual trades in prediction markets"""
    __tablename__ = 'market_trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    market_id = Column(Integer, ForeignKey('markets.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Trade details
    outcome = Column(String, nullable=False)  # "yes" or "no"
    shares = Column(Float, nullable=False)
    price = Column(Float, nullable=False)  # Average price per share
    cost = Column(Float, nullable=False)  # Total credits spent
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    market = relationship("Market", back_populates="trades")
    user = relationship("User", back_populates="market_trades")
