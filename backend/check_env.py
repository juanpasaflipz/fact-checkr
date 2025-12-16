import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pydantic import ValidationError

print("Checking environment configuration using Settings...")

try:
    from app.core.config import settings
    # Accessing properties to trigger any lazy loading if applicable
    # (Though Pydantic loading happens at instantiation time usually)
    print(f"✅ Configuration loaded successfully.")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database URL: {settings.DATABASE_URL.scheme}://***@{settings.DATABASE_URL.host}")
    print("\n🎉 All critical environment variables are set and valid!")
    
except ValidationError as e:
    print("\n❌ Configuration Error:")
    for error in e.errors():
        field = " -> ".join(str(loc) for loc in error['loc'])
        print(f"  - {field}: {error['msg']}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    sys.exit(1)
