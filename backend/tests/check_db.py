from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("❌ No DATABASE_URL found")
    exit(1)

# Mask password for display
masked_url = database_url.split("@")[1] if "@" in database_url else "unknown"
print(f"🔌 Connecting to: ...@{masked_url}")

try:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database(), current_user, version();")).fetchone()
        print(f"✅ Connected successfully!")
        print(f"   Database: {result[0]}")
        print(f"   User:     {result[1]}")
        print(f"   Version:  {result[2].split(',')[0]}") # Truncate long version string
except Exception as e:
    print(f"❌ Connection failed: {e}")

