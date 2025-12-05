"""
Seed prediction markets with demo data

Creates sample markets linked to existing claims for testing the prediction market system.

Usage:
    cd backend
    source venv/bin/activate  # or: source .venv/bin/activate
    python ../scripts/seed_markets.py
"""
import os
import sys

# Determine backend directory and add it to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_dir = os.path.join(project_root, 'backend')

# Always add backend directory to path so we can import app modules
# Python adds the script's directory to sys.path, not the current working directory
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Try importing required packages and provide helpful error messages
try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: python-dotenv not found. Make sure your virtual environment is activated.")
    print("   Run: cd backend && source venv/bin/activate")
    sys.exit(1)

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
except ImportError:
    print("❌ Error: sqlalchemy not found. Make sure your virtual environment is activated.")
    print("   Run: cd backend && source venv/bin/activate")
    sys.exit(1)

from datetime import datetime, timedelta
import re

# Load environment variables
load_dotenv()
# Try loading from backend/.env if DATABASE_URL not found
if not os.getenv("DATABASE_URL"):
    backend_env = os.path.join(backend_dir, '.env')
    if os.path.exists(backend_env):
        load_dotenv(backend_env)

try:
    from app.database.models import Market, MarketStatus, Claim
except ImportError as e:
    print(f"❌ Error importing app modules: {e}")
    print(f"   Backend directory: {backend_dir}")
    print(f"   Python path: {sys.path[:3]}")
    print("   Make sure you're running from the backend directory with venv activated")
    sys.exit(1)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment variables")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


def seed_markets():
    """Create Mexico-focused markets on system-level issues"""
    db = SessionLocal()
    try:
        print("📊 Creating Mexico-focused prediction markets...")
        
        markets_created = 0
        
        # Define Mexico-focused markets aligned with product vision
        # Categories: politics, economy, security, rights, environment, mexico-us-relations, institutions
        mexico_markets = [
            {
                "question": "¿El PIB de México crecerá más del 3% en 2025 según datos de INEGI?",
                "description": "Predicción sobre el crecimiento económico de México basado en datos oficiales del Instituto Nacional de Estadística y Geografía.",
                "category": "economy",
                "resolution_criteria": "Se resolverá basado en datos oficiales publicados por INEGI sobre el PIB trimestral de 2025. Se considerará SÍ si el crecimiento anual es mayor al 3%.",
                "closes_at": datetime.utcnow() + timedelta(days=365)
            },
            {
                "question": "¿La tasa de homicidios dolosos disminuirá en 2025 según datos de SESNSP?",
                "description": "Predicción sobre la seguridad pública en México basada en estadísticas del Secretariado Ejecutivo del Sistema Nacional de Seguridad Pública.",
                "category": "security",
                "resolution_criteria": "Se resolverá comparando la tasa de homicidios dolosos de 2025 con la de 2024, usando datos oficiales de SESNSP. Se considerará SÍ si hay una reducción.",
                "closes_at": datetime.utcnow() + timedelta(days=400)
            },
            {
                "question": "¿Se aprobará una reforma constitucional en materia electoral antes de 2026 según el INE?",
                "description": "Predicción sobre cambios institucionales en el sistema electoral mexicano.",
                "category": "institutions",
                "resolution_criteria": "Se resolverá basado en la publicación oficial de reformas constitucionales en materia electoral antes del 31 de diciembre de 2025, verificadas por el INE.",
                "closes_at": datetime.utcnow() + timedelta(days=730)
            },
            {
                "question": "¿La inflación anual será menor al 4% en 2025 según Banxico?",
                "description": "Predicción sobre la estabilidad de precios en México basada en datos del Banco de México.",
                "category": "economy",
                "resolution_criteria": "Se resolverá usando la inflación anual reportada por Banxico al cierre de 2025. Se considerará SÍ si es menor al 4%.",
                "closes_at": datetime.utcnow() + timedelta(days=365)
            },
            {
                "question": "¿Se implementará una nueva política migratoria bilateral México-Estados Unidos en 2025?",
                "description": "Predicción sobre relaciones internacionales y políticas migratorias entre México y Estados Unidos.",
                "category": "mexico-us-relations",
                "resolution_criteria": "Se resolverá basado en anuncios oficiales de ambos gobiernos sobre una nueva política migratoria bilateral implementada en 2025.",
                "closes_at": datetime.utcnow() + timedelta(days=365)
            },
            {
                "question": "¿México cumplirá con sus compromisos de reducción de emisiones de carbono para 2025?",
                "description": "Predicción sobre políticas ambientales y cumplimiento de compromisos climáticos de México.",
                "category": "environment",
                "resolution_criteria": "Se resolverá basado en reportes oficiales sobre el cumplimiento de compromisos de reducción de emisiones establecidos en acuerdos internacionales, verificados por la SEMARNAT.",
                "closes_at": datetime.utcnow() + timedelta(days=365)
            },
            {
                "question": "¿Se aprobará una ley federal de protección de datos personales más estricta en 2025?",
                "description": "Predicción sobre derechos digitales y protección de datos personales en México.",
                "category": "rights",
                "resolution_criteria": "Se resolverá basado en la publicación en el Diario Oficial de la Federación de una nueva ley o reforma que fortalezca significativamente la protección de datos personales antes del 31 de diciembre de 2025.",
                "closes_at": datetime.utcnow() + timedelta(days=365)
            },
            {
                "question": "¿La participación electoral en las elecciones intermedias de 2025 será mayor al 50% según el INE?",
                "description": "Predicción sobre participación ciudadana en procesos electorales.",
                "category": "politics",
                "resolution_criteria": "Se resolverá usando datos oficiales del INE sobre la participación electoral en las elecciones intermedias de 2025. Se considerará SÍ si supera el 50%.",
                "closes_at": datetime.utcnow() + timedelta(days=180)
            }
        ]
        
        for market_data in mexico_markets:
            # Check if market already exists
            existing = db.query(Market).filter(Market.question == market_data["question"]).first()
            if existing:
                print(f"⏭️  Market already exists: {market_data['question'][:50]}..., skipping...")
                continue
            
            # Generate unique slug
            base_slug = slugify(market_data["question"])
            slug = base_slug
            counter = 1
            while db.query(Market).filter(Market.slug == slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Create market
            market = Market(
                slug=slug,
                question=market_data["question"],
                description=market_data["description"],
                category=market_data["category"],
                resolution_criteria=market_data["resolution_criteria"],
                claim_id=None,
                status=MarketStatus.OPEN,
                yes_liquidity=1000.0,
                no_liquidity=1000.0,
                closes_at=market_data["closes_at"]
            )
            
            db.add(market)
            markets_created += 1
            print(f"✅ Created market: {market.slug[:50]}... (ID: {market.id}, Category: {market.category})")
        
        db.commit()
        print(f"\n🎉 Successfully created {markets_created} Mexico-focused markets!")
        print(f"   Categories: economy, security, institutions, mexico-us-relations, environment, rights, politics")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding prediction markets...")
    seed_markets()
    print("✅ Done!")

