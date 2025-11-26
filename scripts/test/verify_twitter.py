import asyncio
import os
from dotenv import load_dotenv
from app.scraper import TwitterScraper

load_dotenv()

async def main():
    print("Testing Twitter Scraper...")
    scraper = TwitterScraper()
    if not scraper.client:
        print("Client not initialized (missing keys?)")
        return

    try:
        posts = await scraper.fetch_posts(["Sheinbaum"])
        print(f"Found {len(posts)} posts.")
        for post in posts:
            print(f"- {post.content[:50]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
