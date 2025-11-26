"""
Seed script to create initial topics in the database.
Run this before processing claims to ensure topics exist.
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Topic, Base

# Add current directory to path
sys.path.append(os.getcwd())

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment variables")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Define topics for Mexican political fact-checking
TOPICS = [
    {
        "name": "Reforma Judicial",
        "slug": "reforma-judicial",
        "description": "Reformas al sistema judicial, elección de jueces, y cambios en el poder judicial"
    },
    {
        "name": "Ejecutivo",
        "slug": "ejecutivo",
        "description": "Acciones y políticas del poder ejecutivo, presidencia, y gobierno federal"
    },
    {
        "name": "Legislativo",
        "slug": "legislativo",
        "description": "Congreso, iniciativas de ley, y actividades del poder legislativo"
    },
    {
        "name": "Economía",
        "slug": "economia",
        "description": "Políticas económicas, inflación, empleo, y finanzas públicas"
    },
    {
        "name": "Seguridad",
        "slug": "seguridad",
        "description": "Seguridad pública, crimen, fuerzas armadas, y políticas de seguridad"
    },
    {
        "name": "Salud",
        "slug": "salud",
        "description": "Sistema de salud, políticas sanitarias, y servicios médicos"
    },
    {
        "name": "Educación",
        "slug": "educacion",
        "description": "Sistema educativo, reformas educativas, y políticas de educación"
    },
    {
        "name": "Infraestructura",
        "slug": "infraestructura",
        "description": "Obras públicas, transporte, y desarrollo de infraestructura"
    },
    {
        "name": "Medio Ambiente",
        "slug": "medio-ambiente",
        "description": "Políticas ambientales, cambio climático, y protección del medio ambiente"
    },
    {
        "name": "Derechos Humanos",
        "slug": "derechos-humanos",
        "description": "Derechos humanos, igualdad, y protección de grupos vulnerables"
    },
    {
        "name": "Corrupción",
        "slug": "corrupcion",
        "description": "Casos de corrupción, transparencia, y rendición de cuentas"
    },
    {
        "name": "Relaciones Internacionales",
        "slug": "relaciones-internacionales",
        "description": "Política exterior, relaciones diplomáticas, y acuerdos internacionales"
    },
    {
        "name": "Energía",
        "slug": "energia",
        "description": "Políticas energéticas, petróleo, electricidad, y recursos energéticos"
    },
    {
        "name": "Migración",
        "slug": "migracion",
        "description": "Políticas migratorias, fronteras, y asilo"
    },
    {
        "name": "Tecnología",
        "slug": "tecnologia",
        "description": "Políticas tecnológicas, digitalización, y innovación"
    }
]

def seed_topics():
    """Create topics in the database if they don't exist"""
    db = SessionLocal()
    created_count = 0
    existing_count = 0
    
    try:
        for topic_data in TOPICS:
            # Check if topic already exists
            existing_topic = db.query(Topic).filter(
                (Topic.name == topic_data["name"]) | (Topic.slug == topic_data["slug"])
            ).first()
            
            if existing_topic:
                existing_count += 1
                print(f"⏭️  Topic already exists: {topic_data['name']}")
            else:
                topic = Topic(
                    name=topic_data["name"],
                    slug=topic_data["slug"],
                    description=topic_data["description"]
                )
                db.add(topic)
                created_count += 1
                print(f"✅ Created topic: {topic_data['name']}")
        
        db.commit()
        print(f"\n📊 Summary:")
        print(f"   Created: {created_count} topics")
        print(f"   Already existed: {existing_count} topics")
        print(f"   Total: {len(TOPICS)} topics")
        
    except Exception as e:
        print(f"❌ Error seeding topics: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Seeding topics...")
    seed_topics()
    print("✅ Done!")

