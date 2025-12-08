# Testing Scripts Quick Reference

## Test New Categories

To test the new market categories (sports, financial-markets, weather, social-incidents):

```bash
cd backend
source venv/bin/activate
python ../scripts/test_new_categories.py
```

This will:
- ✅ Create test markets in each new category
- ✅ Verify filtering works
- ✅ Test market intelligence agent
- ✅ Verify user preferences

## What Gets Tested

1. **Market Creation**: Creates 4 test markets (one per new category)
2. **Filtering**: Verifies markets can be filtered by category via database and API
3. **Intelligence Agent**: Tests that the agent can assess markets in new categories
4. **User Preferences**: Verifies new categories can be saved as user preferences

## Expected Output

```
🧪 Testing New Market Categories Implementation
================================================================================
TEST 1: Creating test markets in new categories
================================================================================
✅ Created sports market: 123 - ¿Ganará la Selección Mexicana...
✅ Created financial-markets market: 124 - ¿El peso mexicano...
✅ Created weather market: 125 - ¿Habrá más de 200mm...
✅ Created social-incidents market: 126 - ¿Se reportará una manifestación...

TEST 2: Testing category filtering
================================================================================
✅ Category 'sports': Found 1 markets
✅ Category 'financial-markets': Found 1 markets
...

TEST 3: Testing market intelligence agent
================================================================================
📊 Testing sports market: ¿Ganará la Selección Mexicana...
   ✅ Assessment successful:
      - Yes probability: 45.2%
      - Confidence: 65.0%
      ...

TEST 4: Testing user preferences with new categories
================================================================================
✅ Preferences saved correctly: ['sports', 'financial-markets', 'weather']

TEST SUMMARY
================================================================================
Create Markets: ✅ PASSED
Filtering: ✅ PASSED
Intelligence Agent: ✅ PASSED
User Preferences: ✅ PASSED

🎉 All tests passed! New categories are working correctly.
```

## Troubleshooting

- **"DATABASE_URL not found"**: Make sure `.env` file exists in `backend/` directory
- **"Module not found"**: Activate virtual environment: `source venv/bin/activate`
- **"API not available"**: This is OK - some tests work without API, others will skip

For detailed testing instructions, see: `docs/testing/NEW_CATEGORIES_TESTING.md`

