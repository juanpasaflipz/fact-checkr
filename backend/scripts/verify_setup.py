#!/usr/bin/env python3
"""
Verification script to check database migrations and Celery worker configuration.
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

from alembic.config import Config
from alembic import script
from alembic.runtime import migration
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

def check_database_migrations():
    """Check if database is up to date with migrations."""
    print("=" * 60)
    print("DATABASE MIGRATION STATUS")
    print("=" * 60)
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL not set in environment")
        return False
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Get Alembic config
        alembic_cfg = Config(str(backend_dir / "alembic.ini"))
        script_dir = script.ScriptDirectory.from_config(alembic_cfg)
        
        # Get current database revision
        with engine.connect() as connection:
            context = migration.MigrationContext.configure(connection)
            current_heads = set(context.get_current_heads())
        
        # Get expected head revisions from migration files
        expected_heads = set(script_dir.get_heads())
        
        print(f"Current database revision(s): {current_heads if current_heads else 'None (no migrations applied)'}")
        print(f"Expected head revision(s): {expected_heads}")
        
        if not current_heads:
            print("\n⚠️  WARNING: No migrations have been applied to the database")
            print("   Run: alembic upgrade head")
            return False
        
        if current_heads != expected_heads:
            print("\n⚠️  WARNING: Database is not up to date")
            missing = expected_heads - current_heads
            if missing:
                print(f"   Missing revisions: {missing}")
            extra = current_heads - expected_heads
            if extra:
                print(f"   Extra revisions (not in codebase): {extra}")
            print("   Run: alembic upgrade head")
            return False
        
        print("\n✅ Database is up to date with migrations")
        return True
        
    except Exception as e:
        print(f"❌ ERROR checking migrations: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        engine.dispose()


def check_celery_tasks():
    """Check if all Celery tasks are properly configured."""
    print("\n" + "=" * 60)
    print("CELERY WORKER CONFIGURATION")
    print("=" * 60)
    
    try:
        from app.worker import celery_app
        
        # Get all registered tasks
        registered_tasks = set(celery_app.tasks.keys())
        
        # Expected task modules from worker.py
        expected_modules = [
            "app.tasks.scraper",
            "app.tasks.fact_check",
            "app.tasks.health_check",
            "app.tasks.credit_topup",
            "app.tasks.market_notifications",
            "app.tasks.market_intelligence",
            "app.tasks.blog_generation"
        ]
        
        print(f"Registered tasks: {len(registered_tasks)}")
        print(f"Expected modules: {len(expected_modules)}")
        
        # Check if modules can be imported
        missing_modules = []
        for module_name in expected_modules:
            try:
                __import__(module_name)
                print(f"  ✅ {module_name}")
            except ImportError as e:
                print(f"  ❌ {module_name} - {e}")
                missing_modules.append(module_name)
        
        # Check Redis connection
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        print(f"\nRedis URL: {redis_url[:50]}...")
        
        try:
            from app.utils import get_redis_url
            actual_redis_url = get_redis_url()
            print(f"Resolved Redis URL: {actual_redis_url[:50]}...")
            
            # Try to connect
            import redis
            from urllib.parse import urlparse
            parsed = urlparse(actual_redis_url)
            r = redis.Redis(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 6379,
                db=int(parsed.path.lstrip('/')) if parsed.path else 0,
                socket_timeout=5
            )
            r.ping()
            print("  ✅ Redis connection successful")
        except Exception as e:
            print(f"  ⚠️  Redis connection test failed: {e}")
            print("     (This is OK if Redis is not running locally)")
        
        if missing_modules:
            print(f"\n⚠️  WARNING: {len(missing_modules)} task module(s) could not be imported")
            return False
        
        print("\n✅ All Celery task modules are properly configured")
        return True
        
    except Exception as e:
        print(f"❌ ERROR checking Celery configuration: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_database_connection():
    """Check if database connection works."""
    print("\n" + "=" * 60)
    print("DATABASE CONNECTION")
    print("=" * 60)
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL not set in environment")
        return False
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()
            if value == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection returned unexpected value")
                return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        if 'engine' in locals():
            engine.dispose()


def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("FACT-CHECKR SETUP VERIFICATION")
    print("=" * 60)
    print()
    
    results = []
    
    # Check database connection
    results.append(("Database Connection", check_database_connection()))
    
    # Check migrations
    results.append(("Database Migrations", check_database_migrations()))
    
    # Check Celery
    results.append(("Celery Configuration", check_celery_tasks()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("✅ All checks passed! System is ready.")
        return 0
    else:
        print("⚠️  Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
