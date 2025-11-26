#!/usr/bin/env python3
"""
Quick script to test Neon database connection
Run this after updating DATABASE_URL in .env
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("❌ Error: DATABASE_URL not found in .env file")
    print("Please add your Neon connection string to .env:")
    print("DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require")
    sys.exit(1)

print("🔍 Testing Neon Database Connection...")
print(f"Connection string: {database_url[:50]}...")
print("")

try:
    from app.database.connection import engine
    from sqlalchemy import text, inspect
    
    # Test basic connection
    print("1. Testing basic connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        if row and row[0] == 1:
            print("   ✓ Connection successful!")
        else:
            print("   ❌ Connection test failed")
            sys.exit(1)
    
    # Check PostgreSQL version
    print("\n2. Checking PostgreSQL version...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"   ✓ {version.split(',')[0]}")
    
    # List tables
    print("\n3. Checking database schema...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if tables:
        print(f"   ✓ Found {len(tables)} tables:")
        for table in sorted(tables):
            print(f"     - {table}")
    else:
        print("   ⚠ No tables found. Run migrations: alembic upgrade head")
    
    # Test query performance
    print("\n4. Testing query performance...")
    import time
    start = time.time()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    elapsed = (time.time() - start) * 1000
    print(f"   ✓ Query completed in {elapsed:.2f}ms")
    
    if elapsed > 1000:
        print("   ⚠ Warning: Query is slow (>1s). Check your connection.")
    else:
        print("   ✓ Connection speed is good!")
    
    print("\n✅ All tests passed! Neon connection is working correctly.")
    print("\nNext steps:")
    print("1. Run migrations: alembic upgrade head")
    print("2. Restart your backend server")
    print("3. Test the API endpoints")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the backend directory and venv is activated")
    sys.exit(1)
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check your DATABASE_URL in .env file")
    print("2. Make sure ?sslmode=require is in the connection string")
    print("3. Verify your Neon project is active")
    print("4. Check firewall/network settings")
    sys.exit(1)

