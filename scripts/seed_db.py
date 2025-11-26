import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Claim, Source, VerificationStatus
from datetime import datetime
import uuid

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def seed():
    db = SessionLocal()
    try:
        # Create Source
        source_id = f"seed_{uuid.uuid4().hex[:8]}"
        source = Source(
            id=source_id,
            platform="Twitter",
            content="This is a test claim for API verification.",
            author="TestUser",
            url="https://twitter.com/test/status/123",
            timestamp=datetime.utcnow(),
            processed=1
        )
        db.add(source)
        
        # Create Claim
        claim = Claim(
            id=f"claim_{source_id}",
            source_id=source_id,
            original_text=source.content,
            claim_text="Test claim text extracted.",
            status=VerificationStatus.VERIFIED,
            explanation="This is a verified test claim.",
            evidence_sources=["https://example.com/evidence"]
        )
        db.add(claim)
        
        db.commit()
        print(f"✅ Seeded claim: {claim.id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
