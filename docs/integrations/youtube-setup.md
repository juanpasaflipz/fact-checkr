# YouTube Integration Setup Guide

## Overview

The YouTube scraper fetches Mexico political content from YouTube, transcribes videos, and stores them in the database for fact-checking.

## Features

- ✅ Fetches videos from last 7 days
- ✅ Focuses on Mexico political content
- ✅ Automatic video transcription (Spanish/English)
- ✅ Stores transcript as source content
- ✅ Includes video URL for reference
- ✅ Filters videos longer than 2 hours
- ✅ Removes duplicates

## Setup Instructions

### 1. Get YouTube Data API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable "YouTube Data API v3":
   - Navigate to "APIs & Services" > "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy the API key

### 2. Add to Environment Variables

Add to `backend/.env`:

```bash
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### 3. Install Dependencies

```bash
cd backend
source venv/bin/activate
pip install google-api-python-client youtube-transcript-api yt-dlp
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 4. Restart Backend

```bash
# Kill existing backend
pkill -f "uvicorn main:app"

# Start fresh
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

## How It Works

### Search Strategy

The scraper searches for Mexico political content using these terms:
- User-provided keywords
- "política mexicana"
- "México política"
- "Sheinbaum"
- "AMLO"
- "Morena"
- "Reforma Judicial México"
- "Congreso México"
- "elecciones México"

### Video Selection

- **Region**: Mexico (MX)
- **Language**: Spanish (es)
- **Time Range**: Last 7 days
- **Max Duration**: 2 hours (videos longer are skipped)
- **Order**: By date (newest first)

### Transcription Process

1. Attempts to get Spanish transcript (es-MX, es, es-419)
2. Falls back to English if Spanish not available
3. Falls back to any available transcript
4. If no transcript available, uses video description (limited to 500 chars)

### Storage

Videos are stored as `Source` records with:
- **Platform**: "YouTube"
- **Content**: Video title + transcript
- **Author**: Channel name
- **URL**: Full YouTube video URL
- **Timestamp**: Video publish date

## Usage

### Automatic Scraping

The scraper runs automatically via Celery task:

```python
# In app/tasks/scraper.py
@shared_task
def scrape_all_sources():
    keywords = [
        "Reforma Judicial", 
        "Sheinbaum", 
        "México", 
        "Morena",
        "política mexicana",
        "AMLO",
        "Congreso México"
    ]
    # ... fetches from YouTube, Twitter, Google News
```

### Manual Trigger

```bash
cd backend
source venv/bin/activate
python trigger_scrape.py
```

## API Quota Limits

YouTube Data API v3 has daily quotas:
- **Default**: 10,000 units per day
- **Search**: 100 units per request
- **Video details**: 1 unit per request
- **Transcript**: Free (uses youtube-transcript-api, no quota)

**Estimated usage per scrape:**
- ~5 searches × 100 units = 500 units
- ~50 videos × 1 unit = 50 units
- **Total**: ~550 units per scrape

You can run ~18 full scrapes per day with default quota.

## Troubleshooting

### "YouTube API key not found"
- Check `YOUTUBE_API_KEY` in `backend/.env`
- Restart backend after adding key

### "YouTube API error: 403"
- API key may be invalid
- Quota may be exceeded
- Check quota in Google Cloud Console

### "No transcript found"
- Video may not have captions enabled
- Video may be too new (captions not processed yet)
- Falls back to video description

### "ModuleNotFoundError: No module named 'googleapiclient'"
```bash
pip install google-api-python-client youtube-transcript-api yt-dlp
```

### Videos not appearing
- Check logs: `tail -f backend/backend.log`
- Verify API key is valid
- Check if videos match search criteria
- Ensure videos are from last 7 days

## Testing

Test the scraper directly:

```python
from app.scraper_youtube import YouTubeScraper

scraper = YouTubeScraper()
videos = await scraper.fetch_posts(["Sheinbaum", "México"])
print(f"Found {len(videos)} videos")
for video in videos:
    print(f"- {video.author}: {video.url}")
```

## Security Notes

- Keep API key secure (never commit to git)
- Use environment variables only
- Monitor API usage in Google Cloud Console
- Set up quota alerts if needed

## Next Steps

1. Add YouTube API key to `.env`
2. Install dependencies
3. Restart backend
4. Run scraper (automatic or manual)
5. Check database for YouTube sources
6. Videos will be automatically fact-checked

