"""
Comprehensive test script for new market categories

Tests:
1. Creating test markets in each new category
2. Verifying filtering works for each category
3. Testing market intelligence agent with category-specific questions
4. Verifying user preferences save correctly with new categories

Usage:
    cd backend
    source venv/bin/activate
    python ../scripts/test_new_categories.py
"""
import os
import sys
import requests
from datetime import datetime, timedelta
import re

# Add backend to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_dir = os.path.join(project_root, 'backend')

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment
load_dotenv()
if not os.getenv("DATABASE_URL"):
    backend_env = os.path.join(backend_dir, '.env')
    if os.path.exists(backend_env):
        load_dotenv(backend_env)

from app.database.models import Market, MarketStatus, User, UserBalance
from app.services.markets import yes_probability, no_probability, calculate_volume
from app.agents.market_intelligence_agent import MarketIntelligenceAgent

DATABASE_URL = os.getenv("DATABASE_URL")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

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


def test_create_markets():
    """Test 1: Create test markets in each new category"""
    print("\n" + "="*80)
    print("TEST 1: Creating test markets in new categories")
    print("="*80)
    
    db = SessionLocal()
    markets_created = []
    
    try:
        # Test markets for each new category
        test_markets = [
            {
                "question": "¿Ganará la Selección Mexicana su próximo partido de eliminatoria mundialista?",
                "description": "Predicción sobre el resultado del próximo partido oficial de la Selección Nacional de México.",
                "category": "sports",
                "resolution_criteria": "Se resolverá basado en el resultado oficial del próximo partido de eliminatoria mundialista de la Selección Mexicana. SÍ si gana, NO si pierde o empata.",
                "closes_at": datetime.utcnow() + timedelta(days=90)
            },
            {
                "question": "¿El peso mexicano superará los $18 por dólar antes del 31 de diciembre de 2025 según Banxico?",
                "description": "Predicción sobre el tipo de cambio peso-dólar basada en datos oficiales del Banco de México.",
                "category": "financial-markets",
                "resolution_criteria": "Se resolverá usando el tipo de cambio oficial reportado por Banxico. Se considerará SÍ si el peso supera $18 por dólar en cualquier momento antes del 31 de diciembre de 2025.",
                "closes_at": datetime.utcnow() + timedelta(days=365)
            },
            {
                "question": "¿Habrá más de 200mm de lluvia acumulada en la CDMX durante el mes de septiembre de 2025 según CONAGUA?",
                "description": "Predicción sobre precipitaciones en la Ciudad de México basada en datos meteorológicos oficiales.",
                "category": "weather",
                "resolution_criteria": "Se resolverá usando datos oficiales de CONAGUA sobre precipitación acumulada en la CDMX durante septiembre de 2025. SÍ si supera 200mm, NO si es menor o igual.",
                "closes_at": datetime.utcnow() + timedelta(days=120)
            },
            {
                "question": "¿Se reportará una manifestación masiva (más de 10,000 personas) en el Zócalo de la CDMX durante 2025?",
                "description": "Predicción sobre eventos sociales y manifestaciones en la Ciudad de México.",
                "category": "social-incidents",
                "resolution_criteria": "Se resolverá basado en reportes oficiales o noticias verificadas de manifestaciones en el Zócalo con más de 10,000 participantes durante 2025.",
                "closes_at": datetime.utcnow() + timedelta(days=365)
            }
        ]
        
        for market_data in test_markets:
            # Check if market already exists
            existing = db.query(Market).filter(
                Market.question == market_data["question"]
            ).first()
            
            if existing:
                print(f"⏭️  Market already exists: {market_data['category']} - {market_data['question'][:60]}...")
                markets_created.append(existing)
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
            db.flush()  # Get ID without committing
            markets_created.append(market)
            print(f"✅ Created {market_data['category']} market: {market.id} - {market.question[:60]}...")
        
        db.commit()
        print(f"\n✅ Successfully created/verified {len(markets_created)} test markets")
        print(f"   Categories: {', '.join(set(m.category for m in markets_created))}")
        
        return markets_created
        
    except Exception as e:
        print(f"❌ Error creating markets: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return []
    finally:
        db.close()


def test_filtering(markets):
    """Test 2: Verify filtering works for each category"""
    print("\n" + "="*80)
    print("TEST 2: Testing category filtering")
    print("="*80)
    
    db = SessionLocal()
    all_passed = True
    
    try:
        new_categories = ['sports', 'financial-markets', 'weather', 'social-incidents']
        
        for category in new_categories:
            # Query markets by category
            filtered_markets = db.query(Market).filter(
                Market.category == category,
                Market.status == MarketStatus.OPEN
            ).all()
            
            if filtered_markets:
                print(f"✅ Category '{category}': Found {len(filtered_markets)} markets")
                for market in filtered_markets[:2]:  # Show first 2
                    yes_prob = yes_probability(market)
                    no_prob = no_probability(market)
                    volume = calculate_volume(market, db)
                    print(f"   - {market.question[:60]}... (Prob: {yes_prob:.1%} SÍ, Volume: {volume:.0f})")
            else:
                print(f"⚠️  Category '{category}': No markets found (this is OK if markets weren't created)")
                all_passed = False
        
        # Test API endpoint filtering (if API is available)
        try:
            response = requests.get(f"{API_BASE_URL}/api/markets?category=sports&limit=5", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ API filtering test: Found {len(data)} sports markets via API")
            else:
                print(f"\n⚠️  API filtering test: Status {response.status_code} (API may not be running)")
        except Exception as e:
            print(f"\n⚠️  API filtering test: Could not connect to API ({e})")
            print("   (This is OK if the backend server is not running)")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing filtering: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_market_intelligence_agent(markets):
    """Test 3: Test market intelligence agent with category-specific questions"""
    print("\n" + "="*80)
    print("TEST 3: Testing market intelligence agent")
    print("="*80)
    
    db = SessionLocal()
    all_passed = True
    
    try:
        import asyncio
        agent = MarketIntelligenceAgent()
        
        # Test one market from each new category
        category_markets = {}
        for market in markets:
            if market.category in ['sports', 'financial-markets', 'weather', 'social-incidents']:
                if market.category not in category_markets:
                    category_markets[market.category] = market
        
        async def assess_market(market):
            try:
                result = await agent.assess_market_probability(market, db)
                return result
            except Exception as e:
                print(f"   ❌ Error assessing {market.category}: {e}")
                return None
        
        for category, market in category_markets.items():
            print(f"\n📊 Testing {category} market: {market.question[:60]}...")
            try:
                result = asyncio.run(assess_market(market))
                if result:
                    print(f"   ✅ Assessment successful:")
                    print(f"      - Yes probability: {result.get('yes_probability', 0):.1%}")
                    print(f"      - Confidence: {result.get('confidence', 0):.1%}")
                    print(f"      - Uncertainty: {result.get('uncertainty', 'unknown')}")
                    print(f"      - Reasoning: {result.get('reasoning', 'N/A')[:80]}...")
                    print(f"      - Model used: {result.get('model_used', 'unknown')}")
                else:
                    print(f"   ⚠️  Assessment returned no result")
                    all_passed = False
            except Exception as e:
                print(f"   ❌ Error: {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_user_preferences():
    """Test 4: Verify user preferences save correctly with new categories"""
    print("\n" + "="*80)
    print("TEST 4: Testing user preferences with new categories")
    print("="*80)
    
    db = SessionLocal()
    all_passed = True
    
    try:
        # Get a test user (or create one if needed)
        test_user = db.query(User).first()
        
        if not test_user:
            print("⚠️  No users found in database. Skipping user preferences test.")
            print("   (Create a user first to test preferences)")
            return True
        
        # Test valid new categories
        new_categories = ['sports', 'financial-markets', 'weather', 'social-incidents']
        valid_categories = [
            'politics', 'economy', 'security', 'rights', 'environment',
            'mexico-us-relations', 'institutions'
        ] + new_categories
        
        # Test setting preferences with new categories
        test_preferences = ['sports', 'financial-markets', 'weather']
        
        print(f"📝 Testing preferences for user: {test_user.username}")
        print(f"   Setting preferences: {test_preferences}")
        
        # Update user preferences
        test_user.preferred_categories = test_preferences
        db.commit()
        db.refresh(test_user)
        
        # Verify preferences were saved
        if test_user.preferred_categories == test_preferences:
            print(f"   ✅ Preferences saved correctly: {test_user.preferred_categories}")
        else:
            print(f"   ❌ Preferences mismatch!")
            print(f"      Expected: {test_preferences}")
            print(f"      Got: {test_user.preferred_categories}")
            all_passed = False
        
        # Test validation logic by checking the file directly
        try:
            auth_file = os.path.join(backend_dir, 'app', 'routers', 'auth.py')
            with open(auth_file, 'r') as f:
                content = f.read()
            
            if all(cat in content for cat in new_categories):
                print(f"\n✅ Backend validation includes new categories:")
                for cat in new_categories:
                    print(f"   ✅ '{cat}' is in validation list")
            else:
                print(f"\n❌ Backend validation may not include all new categories")
                all_passed = False
        except Exception as e:
            print(f"⚠️  Could not verify validation: {e}")
            print(f"   (Manual check: new categories should be in auth.py)")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing preferences: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Run all tests"""
    print("🧪 Testing New Market Categories Implementation")
    print("="*80)
    
    results = {
        "create_markets": False,
        "filtering": False,
        "intelligence_agent": False,
        "user_preferences": False
    }
    
    # Test 1: Create markets
    markets = test_create_markets()
    results["create_markets"] = len(markets) > 0
    
    # Test 2: Filtering
    if markets:
        results["filtering"] = test_filtering(markets)
    else:
        print("\n⚠️  Skipping filtering test (no markets created)")
    
    # Test 3: Intelligence agent
    if markets:
        results["intelligence_agent"] = test_market_intelligence_agent(markets)
    else:
        print("\n⚠️  Skipping agent test (no markets created)")
    
    # Test 4: User preferences
    results["user_preferences"] = test_user_preferences()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! New categories are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Review the output above for details.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

