#!/usr/bin/env python3
"""Test Supabase database connection"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found in .env file")
    exit(1)

print(f"🔍 Testing connection to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'database'}")

try:
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        
        print("✅ Connection successful!")
        print(f"📊 PostgreSQL version: {version.split(',')[0]}")
        
        # Check if tables exist
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result.fetchall()]
        
        if tables:
            print(f"\n📋 Existing tables ({len(tables)}):")
            for table in tables:
                print(f"   - {table}")
        else:
            print("\n📋 No tables found (run migrations to create them)")
            
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)
