import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

print("Loading env...")
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Connecting to DB: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else '...'}")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Connected. Querying...")
        
        # Check counts
        sources = conn.execute(text("SELECT count(*) FROM sources")).scalar()
        print(f"✅ Sources before: {sources}")
        
        # Try to insert
        try:
            conn.execute(text("""
                INSERT INTO sources (id, platform, content, timestamp, processed)
                VALUES ('test_id_1', 'test', 'test content', NOW(), 0)
                ON CONFLICT (id) DO NOTHING
            """))
            conn.commit()
            print("Inserted test row.")
        except Exception as e:
            print(f"Insert failed: {e}")
            
        # Check counts again
        sources = conn.execute(text("SELECT count(*) FROM sources")).scalar()
        print(f"✅ Sources after: {sources}")
        
except Exception as e:
    print(f"❌ Error: {e}")
