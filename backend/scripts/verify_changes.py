
import sys
import os
import traceback

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("Sanity Check: Verifying imports...")

errors = []

try:
    print("1. Importing app.routers.share...")
    import app.routers.share
    print("✅ app.routers.share imported successfully")
except Exception as e:
    errors.append(f"share.py import failed: {e}")
    traceback.print_exc()

try:
    print("2. Importing app.main...")
    import app.main
    print("✅ app.main imported successfully")
except Exception as e:
    errors.append(f"main.py import failed: {e}")
    traceback.print_exc()

if errors:
    print("\n❌ Verification FAILED with errors:")
    for err in errors:
        print(f"- {err}")
    sys.exit(1)
else:
    print("\n✅ All checks passed!")
