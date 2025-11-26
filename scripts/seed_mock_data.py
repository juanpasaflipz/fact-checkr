import sys
import os
from datetime import datetime, timedelta
import uuid

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

from app.database import SessionLocal, engine
from app.database.models import Base, Claim, Source, VerificationStatus

def seed_data():
    print("Seeding mock data...")
    db = SessionLocal()
    
    try:
        # Create some mock sources
        sources = [
            Source(
                id=str(uuid.uuid4()),
                platform="twitter",
                content="¡Increíble! El gobierno va a regalar casas a todos los que tengan perro.",
                author="@fake_news_bot",
                url="https://twitter.com/fake_news_bot/status/123456789",
                timestamp=datetime.utcnow() - timedelta(hours=2),
                processed=1
            ),
            Source(
                id=str(uuid.uuid4()),
                platform="reddit",
                content="TIL that the moon is actually made of cheese and NASA is hiding it.",
                author="u/conspiracy_theorist",
                url="https://reddit.com/r/conspiracy/comments/12345/moon_cheese",
                timestamp=datetime.utcnow() - timedelta(hours=5),
                processed=1
            ),
             Source(
                id=str(uuid.uuid4()),
                platform="twitter",
                content="La reforma judicial permitirá que cualquiera sea juez sin estudiar.",
                author="@politico_opuesto",
                url="https://twitter.com/politico/status/987654321",
                timestamp=datetime.utcnow() - timedelta(minutes=30),
                processed=1
            )
        ]
        
        for s in sources:
            if not db.query(Source).filter(Source.id == s.id).first():
                db.add(s)
        
        db.commit()
        
        # Create claims linked to sources
        claims = [
            Claim(
                id=str(uuid.uuid4()),
                original_text=sources[0].content,
                claim_text="El gobierno regalará casas a dueños de perros.",
                status=VerificationStatus.DEBUNKED,
                explanation="No existe ningún programa gubernamental que regale casas por tener mascotas. Es una noticia falsa circulando en redes.",
                evidence_sources=["https://gob.mx/vivienda", "https://animal.mx/fact-check"],
                source_id=sources[0].id
            ),
            Claim(
                id=str(uuid.uuid4()),
                original_text=sources[1].content,
                claim_text="The moon is made of cheese.",
                status=VerificationStatus.DEBUNKED,
                explanation="Multiple lunar missions have confirmed the moon is made of rock and dust.",
                evidence_sources=["https://nasa.gov/moon", "https://science.org/moon-composition"],
                source_id=sources[1].id
            ),
            Claim(
                id=str(uuid.uuid4()),
                original_text=sources[2].content,
                claim_text="Reforma judicial elimina requisitos académicos para jueces.",
                status=VerificationStatus.MISLEADING,
                explanation="La reforma propone elección popular, pero mantiene ciertos requisitos de elegibilidad, aunque se debaten sus alcances.",
                evidence_sources=["https://senado.gob.mx/reforma", "https://juridicas.unam.mx/analisis"],
                source_id=sources[2].id
            )
        ]
        
        for c in claims:
            db.add(c)
            
        db.commit()
        print("Successfully seeded mock data!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
