
import sys
import os
import traceback

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("Attempting to import app.routers.chat...")

try:
    import app.routers.chat
    print("✅ Successfully imported app.routers.chat")
except Exception as e:
    print("❌ Failed to import app.routers.chat")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {e}")
    print("\nTraceback:")
    traceback.print_exc()

print("\nChecking dependencies...")
dependencies = [
    "fastapi",
    "pydantic",
    "sqlalchemy",
    "app.database.connection",
    "app.database.models",
    "app.agent",
    "app.utils"
]

for dep in dependencies:
    try:
        if dep.startswith("app."):
             __import__(dep, fromlist=[''])
        else:
             __import__(dep)
        print(f"✅ Dependency '{dep}' loaded")
    except Exception as e:
        print(f"❌ Dependency '{dep}' failed: {e}")
