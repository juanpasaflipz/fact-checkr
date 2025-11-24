from sqlalchemy import Column, String, DateTime, Text, Enum, Integer, ForeignKey, Table, JSON
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
