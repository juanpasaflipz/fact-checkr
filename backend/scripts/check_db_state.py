#!/usr/bin/env python3
"""Check current database state"""
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text, inspect

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(database_url)
inspector = inspect(engine)

try:
    # Check alembic version
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        print(f"Current Alembic version: {version}")
    
    # Check if market intelligence tables exist
    tables = inspector.get_table_names()
    market_intel_tables = [
        'market_prediction_factors',
        'agent_performance', 
        'market_votes'
    ]
    
    print("\nMarket intelligence tables:")
    for table in market_intel_tables:
        exists = table in tables
        print(f"  {table}: {'✅ EXISTS' if exists else '❌ MISSING'}")
    
    # Check markets table columns
    if 'markets' in tables:
        columns = [col['name'] for col in inspector.get_columns('markets')]
        has_embedding = 'question_embedding' in columns
        print(f"\nMarkets table has question_embedding: {'✅ YES' if has_embedding else '❌ NO'}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    engine.dispose()
