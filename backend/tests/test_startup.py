#!/usr/bin/env python3
"""Test if the app can start without errors"""
import sys
import os

print("Testing app startup...")

try:
    print("1. Importing main...")
    import main
    print("✅ Main module imported successfully")
    
    print("2. Checking app object...")
    if hasattr(main, 'app'):
        print("✅ App object exists")
    else:
        print("❌ App object not found")
        sys.exit(1)
    
    print("3. Testing health endpoint...")
    from fastapi.testclient import TestClient
    client = TestClient(main.app)
    response = client.get("/health")
    print(f"✅ Health endpoint returned: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    print("\n✅ All startup tests passed!")
    
except Exception as e:
    print(f"\n❌ Startup test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

