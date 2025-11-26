#!/usr/bin/env python3
"""
Scraping Activity Report - Last 24 Hours
Analyzes database scraping activity and Celery task execution
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, func
from datetime import datetime, timedelta
from collections import defaultdict

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL not found in environment")
    exit(1)

engine = create_engine(DATABASE_URL)

def format_timestamp(dt):
    """Format datetime for display"""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    return "N/A"

def analyze_scraping_activity():
    """Analyze scraping activity in the last 24 hours"""
    print("=" * 80)
    print("SCRAPING ACTIVITY REPORT - LAST 24 HOURS")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Calculate time range
        from datetime import timezone
        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)
        
        print(f"📅 Report Period: {format_timestamp(last_24h)} to {format_timestamp(now)}")
        print()
        
        # 1. Total sources scraped in last 24h
        total_query = text("""
            SELECT COUNT(*) 
            FROM sources 
            WHERE scraped_at >= :last_24h
        """)
        total_count = conn.execute(total_query, {"last_24h": last_24h}).scalar() or 0
        
        print(f"📊 TOTAL SOURCES SCRAPED (Last 24h): {total_count}")
        print()
        
        # 2. Breakdown by platform
        platform_query = text("""
            SELECT 
                platform,
                COUNT(*) as count,
                COUNT(DISTINCT DATE_TRUNC('hour', scraped_at)) as hours_active
            FROM sources 
            WHERE scraped_at >= :last_24h
            GROUP BY platform
            ORDER BY count DESC
        """)
        platform_results = conn.execute(platform_query, {"last_24h": last_24h}).fetchall()
        
        print("📱 BREAKDOWN BY PLATFORM:")
        print("-" * 80)
        total_by_platform = 0
        for platform, count, hours_active in platform_results:
            percentage = (count / total_count * 100) if total_count > 0 else 0
            print(f"  {platform:20s} | {count:5d} sources ({percentage:5.1f}%) | Active in {hours_active} hours")
            total_by_platform += count
        print()
        
        # 3. Hourly scraping activity (check if running every hour)
        hourly_query = text("""
            SELECT 
                DATE_TRUNC('hour', scraped_at) as hour,
                COUNT(*) as sources_count,
                COUNT(DISTINCT platform) as platforms_count
            FROM sources 
            WHERE scraped_at >= :last_24h
            GROUP BY DATE_TRUNC('hour', scraped_at)
            ORDER BY hour DESC
        """)
        hourly_results = conn.execute(hourly_query, {"last_24h": last_24h}).fetchall()
        
        print("⏰ HOURLY SCRAPING ACTIVITY:")
        print("-" * 80)
        
        # Expected hours (should be 24 if running every hour)
        expected_hours = 24
        actual_hours = len(hourly_results)
        coverage = (actual_hours / expected_hours * 100) if expected_hours > 0 else 0
        
        print(f"  Expected hourly runs: {expected_hours}")
        print(f"  Actual hourly runs: {actual_hours}")
        print(f"  Coverage: {coverage:.1f}%")
        print()
        
        # Show last 12 hours of activity
        print("  Last 12 hours of activity:")
        for hour, sources_count, platforms_count in hourly_results[:12]:
            hour_str = hour.strftime("%Y-%m-%d %H:00") if hour else "N/A"
            status = "✅" if sources_count > 0 else "⚠️"
            print(f"    {status} {hour_str} UTC | {sources_count:3d} sources | {platforms_count} platforms")
        
        if len(hourly_results) > 12:
            print(f"    ... ({len(hourly_results) - 12} more hours)")
        print()
        
        # 4. Processing status
        processing_query = text("""
            SELECT 
                processed,
                COUNT(*) as count,
                CASE 
                    WHEN processed = 0 THEN 'Pending'
                    WHEN processed = 1 THEN 'Processed'
                    WHEN processed = 2 THEN 'Skipped'
                    ELSE 'Unknown'
                END as status_name
            FROM sources 
            WHERE scraped_at >= :last_24h
            GROUP BY processed
            ORDER BY processed
        """)
        processing_results = conn.execute(processing_query, {"last_24h": last_24h}).fetchall()
        
        print("🔄 PROCESSING STATUS:")
        print("-" * 80)
        for processed, count, status_name in processing_results:
            percentage = (count / total_count * 100) if total_count > 0 else 0
            print(f"  {status_name:15s} | {count:5d} sources ({percentage:5.1f}%)")
        print()
        
        # 5. Most recent scraping activity
        recent_query = text("""
            SELECT 
                platform,
                scraped_at,
                content,
                author
            FROM sources 
            WHERE scraped_at >= :last_24h
            ORDER BY scraped_at DESC
            LIMIT 10
        """)
        recent_results = conn.execute(recent_query, {"last_24h": last_24h}).fetchall()
        
        print("🆕 MOST RECENT SOURCES (Last 10):")
        print("-" * 80)
        for platform, scraped_at, content, author in recent_results:
            content_preview = (content[:60] + "...") if content and len(content) > 60 else (content or "N/A")
            print(f"  [{format_timestamp(scraped_at)}] {platform:15s} | {author or 'N/A':20s}")
            print(f"    {content_preview}")
        print()
        
        # 6. Check for gaps in scraping (missing hours)
        all_hours_query = text("""
            SELECT generate_series(
                DATE_TRUNC('hour', :last_24h),
                DATE_TRUNC('hour', :now),
                '1 hour'::interval
            ) as hour
        """)
        all_hours = [row[0] for row in conn.execute(all_hours_query, {"last_24h": last_24h, "now": now}).fetchall()]
        
        active_hours = {row[0] for row in hourly_results}
        missing_hours = [h for h in all_hours if h not in active_hours]
        
        if missing_hours:
            print("⚠️  MISSING SCRAPING HOURS (Gaps detected):")
            print("-" * 80)
            for hour in missing_hours[:10]:  # Show first 10 gaps
                hour_str = hour.strftime("%Y-%m-%d %H:00") if hour else "N/A"
                print(f"  ❌ {hour_str} UTC - No scraping activity")
            if len(missing_hours) > 10:
                print(f"  ... ({len(missing_hours) - 10} more missing hours)")
            print()
        else:
            print("✅ No gaps detected - scraping has been running consistently!")
            print()
        
        # 7. Summary statistics
        print("=" * 80)
        print("📈 SUMMARY:")
        print("=" * 80)
        print(f"  Total Sources Scraped: {total_count}")
        print(f"  Hourly Coverage: {coverage:.1f}% ({actual_hours}/{expected_hours} hours)")
        print(f"  Platforms Active: {len(platform_results)}")
        print(f"  Missing Hours: {len(missing_hours)}")
        
        if total_count == 0:
            print()
            print("⚠️  WARNING: No scraping activity detected in the last 24 hours!")
            print("   - Check if Celery worker is running")
            print("   - Check if Celery Beat scheduler is running")
            print("   - Check worker logs for errors")
        elif len(missing_hours) > 0:
            print()
            print("⚠️  WARNING: Some hourly scraping runs are missing!")
            print("   - This may indicate Celery Beat is not running consistently")
            print("   - Check worker logs for errors or failures")
        else:
            print()
            print("✅ Scraping appears to be running normally!")
        
        print()
        print("=" * 80)

if __name__ == "__main__":
    try:
        analyze_scraping_activity()
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()

