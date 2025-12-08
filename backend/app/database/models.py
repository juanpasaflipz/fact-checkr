from sqlalchemy import Column, String, DateTime, Text, Enum, Integer, ForeignKey, Table, JSON, Boolean, Float, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
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

# Association table for many-to-many relationship between trending topics and sources
trending_topic_sources = Table(
    'trending_topic_sources',
    Base.metadata,
    Column('topic_id', Integer, ForeignKey('trending_topics.id'), primary_key=True),
    Column('source_id', String, ForeignKey('sources.id'), primary_key=True),
    Column('detected_at', DateTime, default=datetime.utcnow)
)

# Association table for many-to-many relationship between blog articles and claims
blog_article_claims = Table(
    'blog_article_claims',
    Base.metadata,
    Column('blog_article_id', Integer, ForeignKey('blog_articles.id'), primary_key=True),
    Column('claim_id', String, ForeignKey('claims.id'), primary_key=True)
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
    
    # Trending topic association
    trending_topic_id = Column(Integer, ForeignKey('trending_topics.id'), nullable=True)
    
    # Relationships
    claims = relationship("Claim", back_populates="source")
    trending_topics = relationship("TrendingTopic", secondary=trending_topic_sources, back_populates="sources")

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
    embedding = Column(Vector(1536))  # OpenAI text-embedding-3-small dimensions
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source = relationship("Source", back_populates="claims")
    topics = relationship("Topic", secondary=claim_topics, back_populates="claims")
    markets = relationship("Market", back_populates="claim")
    blog_articles = relationship("BlogArticle", secondary=blog_article_claims, back_populates="related_claims")

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
    
    # Referral system
    referred_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    referral_code = Column(String, unique=True, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    usage_records = relationship("UsageTracking", back_populates="user")
    balance = relationship("UserBalance", back_populates="user", uselist=False)
    market_trades = relationship("MarketTrade", back_populates="user")
    market_stats = relationship("UserMarketStats", back_populates="user", uselist=False)
    market_notifications = relationship("MarketNotification", back_populates="user")

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
    tier = Column(
        Enum(
            SubscriptionTier,
            name="subscriptiontier",
            values_callable=enum_values
        ),
        default=SubscriptionTier.FREE,
        nullable=False
    )
    status = Column(
        Enum(
            SubscriptionStatus,
            name="subscriptionstatus",
            values_callable=enum_values
        ),
        default=SubscriptionStatus.ACTIVE,
        nullable=False
    )
    
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
    
    # Creator tracking
    created_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
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
    creator = relationship("User", foreign_keys=[created_by_user_id])
    notifications = relationship("MarketNotification", back_populates="market")

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


class MarketProposal(Base):
    """User-submitted market proposals (requires admin approval)"""
    __tablename__ = 'market_proposals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Proposal details
    question = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    resolution_criteria = Column(Text)
    
    # Status tracking
    status = Column(String, default="pending", nullable=False)  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class UserMarketStats(Base):
    """User performance statistics for prediction markets"""
    __tablename__ = 'user_market_stats'
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    
    # Performance metrics
    total_trades = Column(Integer, default=0, nullable=False)
    total_volume = Column(Float, default=0.0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    losing_trades = Column(Integer, default=0, nullable=False)
    accuracy_rate = Column(Float, default=0.0, nullable=False)
    total_credits_earned = Column(Float, default=0.0, nullable=False)
    
    # Timestamps
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="market_stats")


class MarketNotification(Base):
    """Notifications for market events (probability changes, resolutions, etc.)"""
    __tablename__ = 'market_notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    market_id = Column(Integer, ForeignKey('markets.id'), nullable=False, index=True)
    
    # Notification details
    notification_type = Column(String, nullable=False)  # probability_change, resolution, new_market
    message = Column(Text)
    read = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="market_notifications")
    market = relationship("Market", back_populates="notifications")


class ReferralBonus(Base):
    """Referral bonus tracking"""
    __tablename__ = 'referral_bonuses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    
    # Bonus details
    bonus_credits = Column(Float, default=100.0, nullable=False)
    paid = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id])
    referred = relationship("User", foreign_keys=[referred_id])


class TrendingTopic(Base):
    """Detected trending topics with intelligence scores"""
    __tablename__ = 'trending_topics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_name = Column(String(255), nullable=False)
    topic_keywords = Column(ARRAY(String), nullable=False)
    detected_at = Column(DateTime, nullable=False)
    trend_score = Column(Float, nullable=False)  # 0.0-1.0
    engagement_velocity = Column(Float, nullable=True)  # Posts per hour
    cross_platform_correlation = Column(Float, nullable=True)  # 0.0-1.0
    context_relevance_score = Column(Float, nullable=True)  # 0.0-1.0
    misinformation_risk_score = Column(Float, nullable=True)  # 0.0-1.0
    final_priority_score = Column(Float, nullable=False)  # Weighted combination
    status = Column(String(20), default='active')  # active, processed, archived
    topic_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sources = relationship("Source", secondary=trending_topic_sources, back_populates="trending_topics")
    priority_entries = relationship("TopicPriorityQueue", back_populates="topic")


class ContextIntelligence(Base):
    """Cached context intelligence for topics"""
    __tablename__ = 'context_intelligence'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_key = Column(String(255), unique=True, nullable=False, index=True)
    political_context = Column(JSON, nullable=True)
    economic_context = Column(JSON, nullable=True)
    social_context = Column(JSON, nullable=True)
    relevance_score = Column(Float, nullable=False)  # 0.0-1.0
    noise_filter_score = Column(Float, nullable=True)  # Lower = more noise
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TopicPriorityQueue(Base):
    """Priority queue for processing topics"""
    __tablename__ = 'topic_priority_queue'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey('trending_topics.id'), nullable=False)
    priority_score = Column(Float, nullable=False)
    queued_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    processing_status = Column(String(20), default='pending')  # pending, processing, completed
    
    # Relationships
    topic = relationship("TrendingTopic", back_populates="priority_entries")


class BlogArticle(Base):
    """AI-generated blog articles from fact-checking data"""
    __tablename__ = 'blog_articles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    excerpt = Column(Text)
    content = Column(Text, nullable=False)  # Markdown format
    
    # Article metadata
    article_type = Column(String, nullable=False)  # "morning", "afternoon", "evening", "breaking"
    edition_number = Column(Integer)  # Sequential number per article type
    
    # Data context (snapshot of analytics used for generation)
    data_context = Column(JSON)  # Store claims, topics, stats used
    
    # Publishing
    published = Column(Boolean, default=False)
    published_at = Column(DateTime, nullable=True)
    telegraph_url = Column(String, nullable=True)
    telegraph_path = Column(String, nullable=True)
    
    # Social media posting
    twitter_posted = Column(Boolean, default=False)
    twitter_url = Column(String, nullable=True)
    
    # Video generation (future phase)
    video_generated = Column(Boolean, default=False)
    youtube_url = Column(String, nullable=True)
    tiktok_video_path = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    related_claims = relationship("Claim", secondary=blog_article_claims, back_populates="blog_articles")
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=True)
    topic = relationship("Topic")
