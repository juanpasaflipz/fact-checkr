import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

print(f"Effective CORS_ORIGINS: {settings.CORS_ORIGINS}")
is_allowed = "http://localhost:3000" in settings.assemble_cors_origins(settings.CORS_ORIGINS)
print(f"Is http://localhost:3000 allowed? {is_allowed}")
