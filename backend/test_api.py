import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("🔍 Testing API...")
    
    # Test Root
    try:
        resp = requests.get(f"{BASE_URL}/")
        print(f"Root: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"Root failed: {e}")
        return

    # Test Claims
    try:
        resp = requests.get(f"{BASE_URL}/claims")
        print(f"Claims: {resp.status_code}")
        if resp.status_code == 200:
            claims = resp.json()
            print(f"✅ Got {len(claims)} claims")
            if claims:
                print("Sample claim:")
                print(json.dumps(claims[0], indent=2))
        else:
            print(f"❌ Error: {resp.status_code}")
            try:
                err = resp.json()
                print(f"Message: {err.get('message')}")
                print("Traceback (last 3 lines):")
                print('\n'.join(err.get('traceback', '').split('\n')[-4:]))
            except:
                print(resp.text[:200])
    except Exception as e:
        print(f"Claims failed: {e}")

    # Test Search
    try:
        resp = requests.get(f"{BASE_URL}/claims/search?query=Sheinbaum")
        print(f"Search 'Sheinbaum': {resp.status_code}")
        if resp.status_code == 200:
            results = resp.json()
            print(f"✅ Found {len(results)} results")
    except Exception as e:
        print(f"Search failed: {e}")

    # Test Topics
    try:
        resp = requests.get(f"{BASE_URL}/topics")
        print(f"Topics: {resp.status_code}")
        if resp.status_code == 200:
            topics = resp.json()
            print(f"✅ Got {len(topics)} topics")
    except Exception as e:
        print(f"Topics failed: {e}")

if __name__ == "__main__":
    test_api()
