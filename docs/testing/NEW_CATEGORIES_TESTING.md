# Testing New Market Categories

This document describes how to test the new market categories implementation (sports, financial-markets, weather, social-incidents).

## Quick Test Script

Run the comprehensive test script:

```bash
cd backend
source venv/bin/activate  # or: source .venv/bin/activate
python ../scripts/test_new_categories.py
```

This script will:
1. ✅ Create test markets in each new category
2. ✅ Verify filtering works for each category
3. ✅ Test market intelligence agent with category-specific questions
4. ✅ Verify user preferences save correctly with new categories

## Manual Testing Steps

### 1. Create Test Markets

#### Via Database (Direct)
```bash
cd backend
source venv/bin/activate
python ../scripts/test_new_categories.py
```

#### Via API (Requires Pro Account)
```bash
# Get auth token first
TOKEN="your_auth_token"

# Create sports market
curl -X POST "http://localhost:8000/api/markets/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Ganará la Selección Mexicana su próximo partido?",
    "description": "Predicción sobre resultado del próximo partido oficial",
    "category": "sports",
    "resolution_criteria": "Basado en resultado oficial del partido"
  }'

# Create financial market
curl -X POST "http://localhost:8000/api/markets/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿El peso superará los $18 por dólar en 2025?",
    "category": "financial-markets",
    "resolution_criteria": "Basado en datos oficiales de Banxico"
  }'

# Create weather market
curl -X POST "http://localhost:8000/api/markets/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Habrá más de 200mm de lluvia en CDMX en septiembre?",
    "category": "weather",
    "resolution_criteria": "Basado en datos de CONAGUA"
  }'

# Create social incidents market
curl -X POST "http://localhost:8000/api/markets/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Habrá manifestación masiva en el Zócalo en 2025?",
    "category": "social-incidents",
    "resolution_criteria": "Basado en reportes oficiales verificados"
  }'
```

### 2. Test Filtering

#### Via Frontend
1. Navigate to `/markets` page
2. Click on each new category tab:
   - "Deportes" (sports)
   - "Mercados Financieros" (financial-markets)
   - "Clima" (weather)
   - "Incidentes Sociales" (social-incidents)
3. Verify markets appear when filtering by each category

#### Via API
```bash
# Test sports filtering
curl "http://localhost:8000/api/markets?category=sports&limit=10"

# Test financial-markets filtering
curl "http://localhost:8000/api/markets?category=financial-markets&limit=10"

# Test weather filtering
curl "http://localhost:8000/api/markets?category=weather&limit=10"

# Test social-incidents filtering
curl "http://localhost:8000/api/markets?category=social-incidents&limit=10"
```

### 3. Test Market Intelligence Agent

The agent should automatically assess new markets when they're created. To manually test:

```python
from app.database.connection import SessionLocal
from app.database.models import Market
from app.agents.market_intelligence_agent import MarketIntelligenceAgent
import asyncio

db = SessionLocal()
agent = MarketIntelligenceAgent()

# Get a market from each new category
sports_market = db.query(Market).filter(Market.category == 'sports').first()
financial_market = db.query(Market).filter(Market.category == 'financial-markets').first()
weather_market = db.query(Market).filter(Market.category == 'weather').first()
social_market = db.query(Market).filter(Market.category == 'social-incidents').first()

# Test assessment
if sports_market:
    result = asyncio.run(agent.assess_market_probability(sports_market, db))
    print(f"Sports market assessment: {result}")

if financial_market:
    result = asyncio.run(agent.assess_market_probability(financial_market, db))
    print(f"Financial market assessment: {result}")

# ... etc
```

### 4. Test User Preferences

#### Via Frontend
1. Complete onboarding or go to user settings
2. Select new categories (sports, financial-markets, weather, social-incidents)
3. Save preferences
4. Navigate to markets page
5. Click "Para ti" filter
6. Verify markets from selected categories appear

#### Via API
```bash
# Update preferences
curl -X PUT "http://localhost:8000/api/auth/me/preferences" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "preferred_categories": ["sports", "financial-markets", "weather"]
  }'

# Verify preferences were saved
curl "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer $TOKEN"

# Test "for you" feed
curl "http://localhost:8000/api/markets?for_you=true" \
  -H "Authorization: Bearer $TOKEN"
```

## Expected Results

### ✅ Success Criteria

1. **Market Creation**
   - Markets can be created with new categories
   - Categories are saved correctly in database
   - Markets appear in database queries

2. **Filtering**
   - Frontend tabs show correct markets when clicked
   - API filtering returns correct markets per category
   - "Todos" shows all markets including new categories

3. **Market Intelligence Agent**
   - Agent recognizes category-specific context
   - Provides appropriate data sources (e.g., CONAGUA for weather, BMV for financial)
   - Generates reasonable probability assessments

4. **User Preferences**
   - New categories can be selected in onboarding
   - Preferences save correctly
   - "Para ti" feed filters by selected categories
   - API validation accepts new categories

## Troubleshooting

### Markets not appearing in frontend
- Check backend is running: `curl http://localhost:8000/health`
- Check CORS configuration
- Verify markets exist in database: `SELECT * FROM markets WHERE category IN ('sports', 'financial-markets', 'weather', 'social-incidents');`

### Agent not assessing markets
- Check Celery worker is running
- Check market intelligence task is queued
- Review logs: `backend/logs/celery_worker.log`

### Preferences not saving
- Verify user is authenticated
- Check API validation includes new categories
- Review backend logs for validation errors

## Example Test Markets

### Sports
- "¿Ganará la Selección Mexicana su próximo partido de eliminatoria mundialista?"
- "¿Llegará el América a la final del torneo?"

### Financial Markets
- "¿El peso mexicano superará los $18 por dólar antes del 31 de diciembre de 2025 según Banxico?"
- "¿Subirá el IPC más del 5% este trimestre?"

### Weather
- "¿Habrá más de 200mm de lluvia acumulada en la CDMX durante septiembre de 2025 según CONAGUA?"
- "¿Llegará un huracán categoría 3+ a costas mexicanas este año?"

### Social Incidents
- "¿Se reportará una manifestación masiva (más de 10,000 personas) en el Zócalo durante 2025?"
- "¿Habrá más de 100 incidentes de seguridad reportados en X estado este mes?"

