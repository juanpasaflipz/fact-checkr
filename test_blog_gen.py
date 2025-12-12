
import asyncio
import os
import sys

# Ensure backend and current dir are in path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.services.blog_generator import BlogArticleGenerator
from backend.app.database import SessionLocal

async def test_blog_generation():
    print("Initialize DB session")
    db = SessionLocal()
    try:
        print("Initialize generator")
        generator = BlogArticleGenerator(db)
        
        print("Triggering morning edition generation...")
        article = await generator.generate_morning_edition()
        
        print("\nSUCCESS!")
        print(f"Title: {article.title}")
        print(f"Slug: {article.slug}")
        print(f"ID: {article.id}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_blog_generation())
