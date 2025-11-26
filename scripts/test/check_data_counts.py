#!/usr/bin/env python3
"""Check data counts in current database"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    exit(1)

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    print("📊 Current database data counts:")
    print("-" * 40)
    for table in ['sources', 'claims', 'topics', 'entities', 'claim_topics']:
        try:
            count = conn.execute(text(f"SELECT count(*) FROM {table}")).scalar()
            print(f"  {table:20} {count:>6} rows")
        except Exception as e:
            print(f"  {table:20} Error: {e}")

