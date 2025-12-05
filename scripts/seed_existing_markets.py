"""
Script to manually seed existing markets with agent assessments.

This script can be run directly to seed markets that were created before
the agent system was deployed, or to test the seeding functionality.

Usage:
    python scripts/seed_existing_markets.py
    python scripts/seed_existing_markets.py --limit 10
    python scripts/seed_existing_markets.py --market-id 5
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

from app.database import SessionLocal
from app.database.models import Market, MarketStatus, MarketTrade
from app.services.market_seeding import seed_market_with_agent_assessment
from app.services.markets import yes_probability
import argparse

def main():
    parser = argparse.ArgumentParser(description='Seed existing markets with agent assessments')
    parser.add_argument('--limit', type=int, default=50, help='Maximum number of markets to seed')
    parser.add_argument('--market-id', type=int, help='Seed a specific market by ID')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be seeded without actually seeding')
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        if args.market_id:
            # Seed specific market
            market = db.query(Market).filter(Market.id == args.market_id).first()
            if not market:
                print(f"❌ Market {args.market_id} not found")
                return
            
            if market.status != MarketStatus.OPEN:
                print(f"❌ Market {args.market_id} is not open (status: {market.status.value})")
                return
            
            print(f"\n📊 Market: {market.question[:80]}...")
            print(f"   Current probability: {yes_probability(market):.1%}")
            
            if args.dry_run:
                print("   [DRY RUN] Would seed this market")
                return
            
            print("   Seeding...")
            result = asyncio.run(seed_market_with_agent_assessment(market, db))
            
            if result["seeded"]:
                db.refresh(market)
                new_prob = yes_probability(market)
                print(f"   ✅ Seeded! New probability: {new_prob:.1%}")
                print(f"   Model used: {result.get('model_used', 'unknown')}")
            else:
                print(f"   ❌ Not seeded: {result.get('reason', 'unknown')}")
                if result.get('confidence'):
                    print(f"   Confidence: {result['confidence']:.2f}")
        else:
            # Find markets with no trades
            markets = db.query(Market).filter(
                Market.status == MarketStatus.OPEN,
                ~Market.trades.any()  # No trades yet
            ).order_by(Market.created_at.desc()).limit(args.limit).all()
            
            if not markets:
                print("✅ No unseeded markets found")
                return
            
            print(f"\n🔍 Found {len(markets)} unseeded markets")
            
            if args.dry_run:
                print("\n[DRY RUN] Would seed these markets:")
                for market in markets:
                    print(f"  - Market {market.id}: {market.question[:60]}...")
                return
            
            print("\n🌱 Seeding markets...\n")
            
            seeded_count = 0
            skipped_count = 0
            
            for market in markets:
                try:
                    print(f"Market {market.id}: {market.question[:60]}...", end=" ")
                    
                    result = asyncio.run(seed_market_with_agent_assessment(market, db))
                    
                    if result["seeded"]:
                        db.refresh(market)
                        new_prob = yes_probability(market)
                        seeded_count += 1
                        print(f"✅ {yes_probability(market):.1%}")
                    else:
                        skipped_count += 1
                        reason = result.get('reason', 'unknown')
                        print(f"⏭️  {reason}")
                        
                except Exception as e:
                    skipped_count += 1
                    print(f"❌ Error: {e}")
            
            print(f"\n📊 Summary:")
            print(f"   ✅ Seeded: {seeded_count}")
            print(f"   ⏭️  Skipped: {skipped_count}")
            print(f"   📈 Total: {len(markets)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

