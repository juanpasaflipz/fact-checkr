
import asyncio
import os
import sys
import logging
from unittest.mock import MagicMock, patch, AsyncMock

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Configure logging to see all details
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_detection():
    print("----------------------------------------------------------------")
    print("DEBUGGING TRENDING TOPIC DETECTION (MOCKED DB)")
    print("----------------------------------------------------------------")
    
    # Mock Database Session to avoid connection errors
    with patch('app.database.connection.SessionLocal') as MockSession:
        # Configure Mock Session
        session = MockSession.return_value
        session.query.return_value.filter.return_value.all.return_value = [] # Return empty for DB queries
        
        # Mock TrendingDetector to simulate "Not enough sources"
        with patch('app.services.trending_detector.TrendingDetector.detect_trending_topics', return_value=[]) as mock_detect:
            try:
                from app.services.topic_prioritizer import TopicPrioritizer
                print("[+] Successfully imported TopicPrioritizer")
                
                prioritizer = TopicPrioritizer()
                print("[+] TopicPrioritizer initialized")
                
                # Mock ContextIntelligenceService to avoid API calls and DB usage
                prioritizer.context_service.assess_topic_relevance = AsyncMock(return_value={
                    'relevance_score': 0.8,
                    'should_fact_check': True,
                    'context_notes': 'Mock context'
                })
                
                # Mock _store_priority_queue to avoid DB writes
                prioritizer._store_priority_queue = AsyncMock(return_value=None)
                
                print("[ ] Calling prioritize_topics(limit=5)...")
                prioritized = await prioritizer.prioritize_topics(limit=5)
                
                print(f"[+] prioritize_topics returned {len(prioritized)} topics")
                
                for i, topic in enumerate(prioritized):
                    print(f"    {i+1}. {topic.get('topic_name')} (Score: {topic.get('final_priority_score')}) - Source: {topic.get('source')}")
                    
                if len(prioritized) == 0:
                    print("[!] WARNING: Returned 0 topics despite keyword fallback!")
                else:
                    print("[OK] Logic works: Keywords provide topics when detection empty.")
                    
            except ImportError as e:
                print(f"[!] ImportError: {e}")
            except Exception as e:
                print(f"[!] CRITICAL ERROR: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_detection())
