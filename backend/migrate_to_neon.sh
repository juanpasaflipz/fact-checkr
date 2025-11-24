#!/bin/bash
# Migration script to help migrate from Supabase to Neon

set -e  # Exit on error

echo "🚀 Neon Migration Helper Script"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found in backend directory"
    echo "Please create .env file first with your DATABASE_URL"
    exit 1
fi

# Check if DATABASE_URL is set
if ! grep -q "DATABASE_URL" .env; then
    echo "❌ Error: DATABASE_URL not found in .env file"
    echo "Please add DATABASE_URL to your .env file"
    exit 1
fi

echo "✓ .env file found"
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "⚠ Warning: venv not found, using system Python"
fi

echo ""
echo "Step 1: Testing current database connection..."
echo "-----------------------------------------------"

# Test current connection
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("❌ DATABASE_URL not set in .env")
    exit(1)

print(f"✓ DATABASE_URL found: {database_url[:50]}...")

try:
    from app.database.connection import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✓ Database connection successful!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("⚠ Make sure your Neon connection string is correct")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Connection test failed. Please check your DATABASE_URL in .env"
    exit 1
fi

echo ""
echo "Step 2: Running database migrations..."
echo "--------------------------------------"

# Run migrations
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✓ Migrations completed successfully!"
else
    echo "❌ Migration failed. Please check the error above."
    exit 1
fi

echo ""
echo "Step 3: Verifying database schema..."
echo "------------------------------------"

python3 << 'EOF'
from app.database.connection import engine
from sqlalchemy import inspect, text

inspector = inspect(engine)
tables = inspector.get_table_names()

expected_tables = ['sources', 'claims', 'topics', 'entities', 'claim_topics', 'alembic_version']
print(f"Found {len(tables)} tables:")

for table in sorted(tables):
    status = "✓" if table in expected_tables else "⚠"
    print(f"  {status} {table}")

missing = set(expected_tables) - set(tables)
if missing:
    print(f"\n⚠ Missing tables: {', '.join(missing)}")
else:
    print("\n✓ All expected tables found!")
EOF

echo ""
echo "✅ Migration complete!"
echo ""
echo "Next steps:"
echo "1. Restart your backend server"
echo "2. Restart your Celery workers"
echo "3. Test the API endpoints"
echo "4. Check the frontend loads data correctly"
echo ""

