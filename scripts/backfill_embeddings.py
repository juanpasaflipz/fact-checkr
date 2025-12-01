#!/usr/bin/env python3
"""
Backfill Embeddings for Existing Claims

This script generates embeddings for all claims that don't have one yet.
Run this once after enabling pgvector to enable semantic search.

Usage:
    cd backend
    source venv/bin/activate
    python ../scripts/backfill_embeddings.py
"""
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

import openai
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration
BATCH_SIZE = 50  # Process 50 claims at a time
MODEL = "text-embedding-3-small"  # 1536 dimensions, cost-effective


def get_db_session():
    """Create database session"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        sys.exit(1)
    
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()


def get_openai_client():
    """Initialize OpenAI client"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        sys.exit(1)
    
    return openai.OpenAI(api_key=api_key)


def get_claims_without_embeddings(db, limit=BATCH_SIZE):
    """Fetch claims that don't have embeddings yet"""
    result = db.execute(text("""
        SELECT id, claim_text, original_text, status::text as status
        FROM claims
        WHERE embedding IS NULL
        ORDER BY created_at DESC
        LIMIT :limit
    """), {"limit": limit})
    
    return result.fetchall()


def generate_embeddings(client, texts):
    """Generate embeddings for a batch of texts"""
    try:
        response = client.embeddings.create(
            model=MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"❌ Error generating embeddings: {e}")
        return None


def update_claim_embedding(db, claim_id, embedding):
    """Update a claim's embedding in the database"""
    try:
        # Convert embedding list to PostgreSQL array format
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        db.execute(text("""
            UPDATE claims 
            SET embedding = :embedding
            WHERE id = :claim_id
        """), {
            "embedding": embedding_str,
            "claim_id": claim_id
        })
        return True
    except Exception as e:
        print(f"❌ Error updating claim {claim_id}: {e}")
        return False


def main():
    print("=" * 60)
    print("🚀 FactCheckr Embedding Backfill Script")
    print("=" * 60)
    
    # Initialize
    db = get_db_session()
    client = get_openai_client()
    
    # Get total count
    total_without = db.execute(text("""
        SELECT COUNT(*) FROM claims WHERE embedding IS NULL
    """)).scalar()
    
    total_with = db.execute(text("""
        SELECT COUNT(*) FROM claims WHERE embedding IS NOT NULL
    """)).scalar()
    
    print(f"\n📊 Current Status:")
    print(f"   - Claims WITH embeddings: {total_with}")
    print(f"   - Claims WITHOUT embeddings: {total_without}")
    
    if total_without == 0:
        print("\n✅ All claims already have embeddings!")
        return
    
    print(f"\n🔄 Processing {total_without} claims in batches of {BATCH_SIZE}...")
    print(f"   Estimated cost: ~${total_without * 0.00002:.4f} USD\n")
    
    processed = 0
    errors = 0
    start_time = datetime.now()
    
    while True:
        # Fetch batch
        claims = get_claims_without_embeddings(db, BATCH_SIZE)
        
        if not claims:
            break
        
        # Build texts for embedding
        texts = []
        for claim in claims:
            context = f"Afirmación: {claim.claim_text}"
            if claim.original_text:
                context += f"\nContexto: {claim.original_text[:500]}"
            if claim.status:
                context += f"\nEstado: {claim.status}"
            texts.append(context)
        
        # Generate embeddings
        print(f"   Generating embeddings for batch of {len(claims)}...", end=" ")
        embeddings = generate_embeddings(client, texts)
        
        if not embeddings:
            print("FAILED")
            errors += len(claims)
            continue
        
        # Update database
        batch_success = 0
        for claim, embedding in zip(claims, embeddings):
            if update_claim_embedding(db, claim.id, embedding):
                batch_success += 1
            else:
                errors += 1
        
        db.commit()
        processed += batch_success
        print(f"✓ {batch_success}/{len(claims)} updated (Total: {processed}/{total_without})")
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 60)
    print("📈 Backfill Complete!")
    print("=" * 60)
    print(f"   ✅ Successfully processed: {processed}")
    print(f"   ❌ Errors: {errors}")
    print(f"   ⏱️  Time elapsed: {elapsed:.1f} seconds")
    print(f"   📊 Rate: {processed/elapsed:.1f} claims/second" if elapsed > 0 else "")
    
    # Verify
    final_count = db.execute(text("""
        SELECT COUNT(*) FROM claims WHERE embedding IS NOT NULL
    """)).scalar()
    print(f"\n   Total claims with embeddings: {final_count}")
    
    db.close()


if __name__ == "__main__":
    main()

