#!/usr/bin/env python3
"""
Check Celery scraping status and generate report on data scraped in last 24 hours
"""
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import SessionLocal
from app.database.models import Source, Claim, VerificationStatus

load_dotenv()

def check_worker_status():
    """Check if Celery workers are running"""
    import subprocess
    
    try:
        # Check for celery worker processes
        result = subprocess.run(
            ['pgrep', '-f', 'celery.*worker'],
            capture_output=True,
            text=True
        )
        workers_running = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        # Check for celery beat processes
        beat_result = subprocess.run(
            ['pgrep', '-f', 'celery.*beat'],
            capture_output=True,
            text=True
        )
        beat_running = len(beat_result.stdout.strip().split('\n')) if beat_result.stdout.strip() else 0
        
        return {
            'workers': workers_running > 0,
            'worker_count': workers_running,
            'beat': beat_running > 0,
            'beat_count': beat_running
        }
    except Exception as e:
        return {
            'workers': False,
            'worker_count': 0,
            'beat': False,
            'beat_count': 0,
            'error': str(e)
        }

def get_scraping_report(db, hours=24):
    """Generate report on scraping activity"""
    now = datetime.utcnow()
    since = now - timedelta(hours=hours)
    
    # Sources scraped in last 24 hours
    sources_24h = db.query(Source).filter(
        Source.scraped_at >= since
    ).all()
    
    total_sources_24h = len(sources_24h)
    
    # Sources by platform
    sources_by_platform = db.query(
        Source.platform,
        func.count(Source.id).label('count')
    ).filter(
        Source.scraped_at >= since
    ).group_by(Source.platform).all()
    
    # Sources by processing status
    sources_by_status = db.query(
        Source.processed,
        func.count(Source.id).label('count')
    ).filter(
        Source.scraped_at >= since
    ).group_by(Source.processed).all()
    
    # Claims created from sources in last 24 hours
    claims_24h = db.query(Claim).filter(
        Claim.created_at >= since
    ).all()
    
    total_claims_24h = len(claims_24h)
    
    # Claims by verification status
    claims_by_status = db.query(
        Claim.status,
        func.count(Claim.id).label('count')
    ).filter(
        Claim.created_at >= since
    ).group_by(Claim.status).all()
    
    # Sources that were scraped but not yet processed
    pending_sources = db.query(Source).filter(
        and_(
            Source.scraped_at >= since,
            Source.processed == 0
        )
    ).count()
    
    # Sources that were processed
    processed_sources = db.query(Source).filter(
        and_(
            Source.scraped_at >= since,
            Source.processed == 1
        )
    ).count()
    
    # Hourly breakdown (last 24 hours)
    hourly_breakdown = []
    for i in range(24):
        hour_start = now - timedelta(hours=i+1)
        hour_end = now - timedelta(hours=i)
        
        hour_sources = db.query(func.count(Source.id)).filter(
            and_(
                Source.scraped_at >= hour_start,
                Source.scraped_at < hour_end
            )
        ).scalar() or 0
        
        hour_claims = db.query(func.count(Claim.id)).filter(
            and_(
                Claim.created_at >= hour_start,
                Claim.created_at < hour_end
            )
        ).scalar() or 0
        
        hourly_breakdown.append({
            'hour': hour_start.strftime('%Y-%m-%d %H:00'),
            'sources': hour_sources,
            'claims': hour_claims
        })
    
    hourly_breakdown.reverse()  # Oldest to newest
    
    return {
        'period_hours': hours,
        'period_start': since,
        'period_end': now,
        'total_sources': total_sources_24h,
        'total_claims': total_claims_24h,
        'sources_by_platform': {p.platform: p.count for p in sources_by_platform},
        'sources_by_processing_status': {
            'pending': pending_sources,
            'processed': processed_sources,
            'skipped': db.query(Source).filter(
                and_(
                    Source.scraped_at >= since,
                    Source.processed == 2
                )
            ).count()
        },
        'claims_by_status': {
            str(s.status): s.count for s in claims_by_status
        },
        'hourly_breakdown': hourly_breakdown
    }

def print_report(worker_status, report):
    """Print formatted report"""
    print("=" * 80)
    print("🔍 FACTCHECKR MX - SCRAPING STATUS REPORT")
    print("=" * 80)
    print()
    
    # Worker Status
    print("📊 CELERY WORKER STATUS")
    print("-" * 80)
    if worker_status.get('error'):
        print(f"⚠️  Error checking workers: {worker_status['error']}")
    else:
        worker_status_icon = "✅" if worker_status['workers'] else "❌"
        beat_status_icon = "✅" if worker_status['beat'] else "❌"
        
        print(f"{worker_status_icon} Workers Running: {worker_status['worker_count']} process(es)")
        print(f"{beat_status_icon} Beat Scheduler: {'Running' if worker_status['beat'] else 'NOT RUNNING'}")
        
        if not worker_status['beat']:
            print("   ⚠️  WARNING: Beat scheduler not running! Hourly scraping will NOT execute.")
            print("   💡 Start with: celery -A app.worker worker --beat --loglevel=info")
    
    print()
    
    # Scraping Report
    print(f"📈 SCRAPING ACTIVITY (Last {report['period_hours']} Hours)")
    print("-" * 80)
    print(f"Period: {report['period_start'].strftime('%Y-%m-%d %H:%M:%S')} to {report['period_end'].strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    print(f"📥 Sources Scraped: {report['total_sources']}")
    if report['sources_by_platform']:
        print("   By Platform:")
        for platform, count in sorted(report['sources_by_platform'].items(), key=lambda x: x[1], reverse=True):
            print(f"     • {platform}: {count}")
    else:
        print("   ⚠️  No sources scraped in this period")
    
    print()
    print(f"📊 Processing Status:")
    status_map = {
        'pending': '⏳ Pending',
        'processed': '✅ Processed',
        'skipped': '⏭️  Skipped'
    }
    for status, label in status_map.items():
        count = report['sources_by_processing_status'].get(status, 0)
        print(f"     {label}: {count}")
    
    print()
    print(f"🔍 Claims Created: {report['total_claims']}")
    if report['claims_by_status']:
        print("   By Verification Status:")
        status_labels = {
            'Verified': '✅ Verified',
            'Debunked': '❌ Debunked',
            'Misleading': '⚠️  Misleading',
            'Unverified': '⏳ Unverified'
        }
        for status, count in sorted(report['claims_by_status'].items(), key=lambda x: x[1], reverse=True):
            status_key = status.replace("VerificationStatus.", "")
            label = status_labels.get(status_key, status_key)
            print(f"     {label}: {count}")
    else:
        print("   ⚠️  No claims created in this period")
    
    print()
    print("⏰ HOURLY BREAKDOWN (Last 24 Hours)")
    print("-" * 80)
    print(f"{'Hour':<20} {'Sources':<12} {'Claims':<12}")
    print("-" * 80)
    
    for hour_data in report['hourly_breakdown']:
        hour_label = hour_data['hour'].split(' ')[1]  # Just the time
        sources = hour_data['sources']
        claims = hour_data['claims']
        
        # Highlight hours with activity
        if sources > 0 or claims > 0:
            print(f"{hour_label:<20} {sources:<12} {claims:<12} ⭐")
        else:
            print(f"{hour_label:<20} {sources:<12} {claims:<12}")
    
    print()
    print("=" * 80)
    
    # Summary and recommendations
    print("💡 SUMMARY & RECOMMENDATIONS")
    print("-" * 80)
    
    if not worker_status.get('beat'):
        print("❌ CRITICAL: Beat scheduler is not running. Hourly scraping is disabled.")
        print("   Action: Start workers with --beat flag")
    elif report['total_sources'] == 0:
        print("⚠️  WARNING: No sources scraped in last 24 hours.")
        print("   Possible causes:")
        print("     • API keys missing (Twitter, Google News, YouTube)")
        print("     • Scrapers encountering errors (check worker logs)")
        print("     • No new content matching keywords")
    elif report['sources_by_processing_status']['pending'] > 0:
        pending = report['sources_by_processing_status']['pending']
        print(f"⚠️  {pending} sources are pending fact-checking.")
        print("   This is normal if workers are processing, but check if fact-check tasks are running.")
    else:
        print("✅ Scraping appears to be working normally!")
    
    print()
    print("=" * 80)

def main():
    """Main function"""
    db = SessionLocal()
    try:
        # Check worker status
        worker_status = check_worker_status()
        
        # Get scraping report
        report = get_scraping_report(db, hours=24)
        
        # Print report
        print_report(worker_status, report)
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()


