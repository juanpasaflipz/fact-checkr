#!/usr/bin/env python3
"""
Test YouTube Data API v3 credentials and configuration
Based on YouTube Data API documentation requirements
"""
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta, timezone

load_dotenv()

def test_youtube_api():
    """Test YouTube API key and configuration"""
    print("=" * 80)
    print("YOUTUBE DATA API v3 - CREDENTIALS TEST")
    print("=" * 80)
    print()
    
    # 1. Check API key exists
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("❌ ERROR: YOUTUBE_API_KEY not found in environment")
        print("   Add to backend/.env: YOUTUBE_API_KEY=your_key_here")
        return False
    
    print(f"✅ API Key found (length: {len(api_key)} characters)")
    print(f"   Key preview: {api_key[:10]}...{api_key[-5:]}")
    print()
    
    # 2. Initialize YouTube API client
    # According to docs: Every request must specify an API key (with the key parameter)
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        print("✅ YouTube API client initialized successfully")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize YouTube API client: {e}")
        return False
    
    print()
    
    # 3. Test API key validity with a simple request
    # Using search.list as per documentation: GET /search
    print("Testing API key with search.list method...")
    try:
        # Simple test search
        search_response = youtube.search().list(
            q="México política",  # Test search term
            part='id,snippet',
            type='video',
            maxResults=1,  # Just 1 result for testing
            order='date',
            regionCode='MX',  # Mexico region
            relevanceLanguage='es'  # Spanish
        ).execute()
        
        print("✅ API key is VALID - Search request successful")
        print(f"   Found {len(search_response.get('items', []))} test result(s)")
        
    except HttpError as e:
        error_code = e.resp.status
        # Handle error_details safely - it may be a list or dict
        if e.error_details and isinstance(e.error_details, list) and len(e.error_details) > 0:
            error_reason = e.error_details[0].get('reason', 'Unknown') if isinstance(e.error_details[0], dict) else 'Unknown'
        elif e.error_details and isinstance(e.error_details, dict):
            error_reason = e.error_details.get('reason', 'Unknown')
        else:
            error_reason = 'Unknown'
        
        print(f"❌ API Error: HTTP {error_code}")
        print(f"   Reason: {error_reason}")
        
        if error_code == 400:
            print("   → Bad Request: Check API parameters")
        elif error_code == 401:
            print("   → Unauthorized: API key is invalid or expired")
        elif error_code == 403:
            if error_reason == 'quotaExceeded':
                print("   → Quota Exceeded: Daily quota limit reached")
            elif error_reason == 'accessNotConfigured':
                print("   → Access Not Configured: YouTube Data API v3 not enabled")
                print("   → Fix: Enable 'YouTube Data API v3' in Google Cloud Console")
            elif error_reason == 'forbidden':
                print("   → Forbidden: API key restrictions may be blocking access")
            else:
                print("   → Forbidden: Check API key permissions and restrictions")
        elif error_code == 404:
            print("   → Not Found: API endpoint issue")
        else:
            print(f"   → Unknown error: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
        return False
    
    print()
    
    # 4. Test with publishedAfter parameter (as used in scraper)
    print("Testing with publishedAfter parameter (last 7 days)...")
    try:
        published_after = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace('+00:00', 'Z')
        
        search_response = youtube.search().list(
            q="política mexicana",
            part='id,snippet',
            type='video',
            maxResults=1,
            order='date',
            publishedAfter=published_after,
            regionCode='MX',
            relevanceLanguage='es'
        ).execute()
        
        print("✅ publishedAfter parameter works correctly")
        print(f"   Found {len(search_response.get('items', []))} result(s) from last 7 days")
        
    except HttpError as e:
        print(f"⚠️  Warning: publishedAfter test failed: {e.resp.status}")
        if e.resp.status == 400:
            print("   → publishedAfter format may be incorrect")
    
    print()
    
    # 5. Test videos.list method (as used in scraper)
    print("Testing videos.list method...")
    try:
        # Use a known video ID for testing
        test_video_id = "dQw4w9WgXcQ"  # Example video ID
        
        video_response = youtube.videos().list(
            part='snippet,contentDetails',
            id=test_video_id
        ).execute()
        
        if video_response.get('items'):
            print("✅ videos.list method works correctly")
            print(f"   Retrieved details for test video")
        else:
            print("⚠️  videos.list returned no items (test video may not exist)")
            
    except HttpError as e:
        print(f"⚠️  Warning: videos.list test failed: {e.resp.status}")
        if e.resp.status == 403:
            print("   → Check if API key has permission for videos.list")
    
    print()
    
    # 6. Summary and recommendations
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("✅ API Key: Present and configured")
    print("✅ API Client: Initialized successfully")
    print("✅ Search API: Working")
    print()
    print("According to YouTube Data API documentation:")
    print("  • Every request must specify an API key (with the key parameter) ✓")
    print("  • API key is passed via developerKey parameter ✓")
    print("  • Search and video list methods are supported ✓")
    print()
    print("If scraping is still not working:")
    print("  1. Check Celery worker logs for errors")
    print("  2. Verify YouTube scraper is being called")
    print("  3. Check quota limits in Google Cloud Console")
    print("  4. Ensure 'YouTube Data API v3' is enabled in project")
    print()
    
    return True

if __name__ == "__main__":
    try:
        test_youtube_api()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

