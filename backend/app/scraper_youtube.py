"""
YouTube Scraper for Mexico Political Content
Fetches videos, transcribes them, and stores as sources
"""
import os
import re
from typing import List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from app.models import SocialPost
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class YouTubeScraper:
    """Scraper for YouTube videos focused on Mexico political content"""
    
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.youtube = None
        
        if self.api_key:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize YouTube API: {e}")
        else:
            logger.warning("YouTube API key not found. YouTube scraping will be disabled.")
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _get_transcript(self, video_id: str) -> str:
        """Get transcript for a YouTube video"""
        try:
            # Create API instance and get transcript list
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            
            # Try Spanish (Mexico) first
            try:
                transcript = transcript_list.find_transcript(['es-MX', 'es', 'es-419'])
                transcript_data = transcript.fetch()
            except (TranscriptsDisabled, NoTranscriptFound):
                # Fallback to English
                try:
                    transcript = transcript_list.find_transcript(['en'])
                    transcript_data = transcript.fetch()
                except (TranscriptsDisabled, NoTranscriptFound):
                    # Get any available manually created transcript
                    try:
                        transcript = transcript_list.find_manually_created_transcript(['es', 'en'])
                        transcript_data = transcript.fetch()
                    except (TranscriptsDisabled, NoTranscriptFound):
                        # Last resort: get any generated transcript
                        try:
                            transcript = transcript_list.find_generated_transcript(['es', 'en'])
                            transcript_data = transcript.fetch()
                        except Exception:
                            return None
            
            # Combine all transcript text
            # FetchedTranscript is iterable - items can be dicts or objects with 'text' attribute
            text_parts = []
            for item in transcript_data:
                if isinstance(item, dict):
                    text_parts.append(item.get('text', ''))
                elif hasattr(item, 'text'):
                    text_parts.append(item.text)
                else:
                    # Try to access as dict anyway
                    try:
                        text_parts.append(item['text'])
                    except (TypeError, KeyError):
                        continue
            text = ' '.join(text_parts)
            return text if text else None
            
        except TranscriptsDisabled:
            logger.warning(f"Transcripts disabled for video {video_id}")
            return None
        except NoTranscriptFound:
            logger.warning(f"No transcript found for video {video_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting transcript for {video_id}: {e}")
            return None
    
    async def fetch_posts(self, keywords: List[str]) -> List[SocialPost]:
        """Fetch YouTube videos matching keywords for Mexico political content"""
        if not self.youtube:
            return []
        
        posts = []
        
        # Mexico political search terms
        mexico_terms = [
            "política mexicana",
            "México política",
            "Sheinbaum",
            "AMLO",
            "Morena",
            "Reforma Judicial México",
            "Congreso México",
            "elecciones México"
        ]
        
        # Combine user keywords with Mexico political terms
        search_terms = list(set(keywords + mexico_terms))
        
        # Search for videos from last 7 days
        from datetime import timezone
        published_after = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace('+00:00', 'Z')
        
        for search_term in search_terms[:5]:  # Limit to 5 searches to avoid quota
            try:
                # Search for videos
                search_response = self.youtube.search().list(
                    q=f"{search_term} política México",
                    part='id,snippet',
                    type='video',
                    maxResults=10,
                    order='date',
                    publishedAfter=published_after,
                    regionCode='MX',  # Mexico region
                    relevanceLanguage='es'  # Spanish
                ).execute()
                
                for item in search_response.get('items', []):
                    video_id = item['id']['videoId']
                    snippet = item['snippet']
                    
                    # Get video details for duration and channel info
                    try:
                        video_response = self.youtube.videos().list(
                            part='contentDetails,snippet,statistics',
                            id=video_id
                        ).execute()
                        
                        if not video_response.get('items'):
                            continue
                            
                        video_details = video_response['items'][0]
                        content_details = video_details.get('contentDetails', {})
                        duration = content_details.get('duration', '')
                        
                        # Parse duration (PT15M33S format)
                        # Skip videos longer than 2 hours
                        duration_seconds = self._parse_duration(duration)
                        if duration_seconds > 7200:  # 2 hours
                            continue
                        
                        # Get transcript (with timeout to prevent hanging)
                        try:
                            transcript = self._get_transcript(video_id)
                        except Exception as e:
                            logger.warning(f"Transcript fetch failed for {video_id}: {e}")
                            transcript = None
                        
                        if not transcript:
                            # Use description if no transcript
                            transcript = snippet.get('description', '')[:500] if snippet.get('description') else ''
                        
                        if not transcript or len(transcript) < 50:
                            # Skip videos without sufficient content
                            continue
                        
                        # Create post with transcript as content
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        
                        post = SocialPost(
                            id=f"youtube_{video_id}",
                            platform="YouTube",
                            content=f"{snippet.get('title', '')}\n\n{transcript}",
                            author=snippet.get('channelTitle', 'Unknown Channel'),
                            timestamp=snippet.get('publishedAt', datetime.now(timezone.utc).isoformat()),
                            url=video_url
                        )
                        
                        posts.append(post)
                        
                    except HttpError as e:
                        logger.error(f"YouTube API error for video {video_id}: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing video {video_id}: {e}")
                        continue
                        
            except HttpError as e:
                logger.error(f"YouTube API error for search '{search_term}': {e}")
                continue
            except Exception as e:
                logger.error(f"Error searching YouTube for '{search_term}': {e}")
                continue
        
        # Remove duplicates based on video ID
        seen_ids = set()
        unique_posts = []
        for post in posts:
            video_id = post.id.replace('youtube_', '')
            if video_id not in seen_ids:
                seen_ids.add(video_id)
                unique_posts.append(post)
        
        logger.info(f"Fetched {len(unique_posts)} YouTube videos")
        return unique_posts
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse YouTube duration format (PT15M33S) to seconds"""
        if not duration_str:
            return 0
        
        # Remove PT prefix
        duration_str = duration_str.replace('PT', '')
        
        hours = 0
        minutes = 0
        seconds = 0
        
        # Extract hours
        if 'H' in duration_str:
            hours_match = re.search(r'(\d+)H', duration_str)
            if hours_match:
                hours = int(hours_match.group(1))
        
        # Extract minutes
        if 'M' in duration_str:
            minutes_match = re.search(r'(\d+)M', duration_str)
            if minutes_match:
                minutes = int(minutes_match.group(1))
        
        # Extract seconds
        if 'S' in duration_str:
            seconds_match = re.search(r'(\d+)S', duration_str)
            if seconds_match:
                seconds = int(seconds_match.group(1))
        
        return hours * 3600 + minutes * 60 + seconds

