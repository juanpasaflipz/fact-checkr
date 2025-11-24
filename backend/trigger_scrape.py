from app.tasks.scraper import scrape_all_sources
import asyncio

print("🚀 Triggering manual scrape...")
result = scrape_all_sources.delay()
print(f"✅ Task triggered! ID: {result.id}")
print("Check worker logs for progress.")
