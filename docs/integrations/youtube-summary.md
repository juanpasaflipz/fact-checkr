# YouTube Integration Summary

## ✅ What's Been Implemented

### 1. YouTube Scraper (`backend/app/scraper_youtube.py`)
- ✅ Fetches videos from YouTube Data API v3
- ✅ Focuses on Mexico political content
- ✅ Automatic video transcription (Spanish/English)
- ✅ Filters videos (max 2 hours, last 7 days)
- ✅ Removes duplicates
- ✅ Stores with video URL for reference

### 2. Integration with Existing System
- ✅ Added to scraper task (`backend/app/tasks/scraper.py`)
- ✅ Runs alongside Twitter and Google News scrapers
- ✅ Stores as `Source` records (same as other sources)
- ✅ Automatically fact-checked via existing pipeline

### 3. Dependencies Installed
- ✅ `google-api-python-client` - YouTube Data API
- ✅ `youtube-transcript-api` - Video transcription
- ✅ `yt-dlp` - Video metadata extraction

### 4. Configuration
- ✅ Added `YOUTUBE_API_KEY` to `backend/ENV_SETUP.md`
- ✅ Updated `requirements.txt`
- ✅ Created setup guide (`YOUTUBE_SETUP.md`)

## 🎯 Features

### Search Strategy
Searches for Mexico political content using:
- User keywords
- "política mexicana"
- "Sheinbaum", "AMLO", "Morena"
- "Reforma Judicial México"
- "Congreso México"
- "elecciones México"

### Video Processing
1. **Search**: Finds videos from last 7 days in Mexico region
2. **Filter**: Skips videos longer than 2 hours
3. **Transcribe**: Gets Spanish transcript (falls back to English)
4. **Store**: Saves as Source with title + transcript
5. **Fact-Check**: Automatically processed by existing pipeline

### Data Stored
- **Platform**: "YouTube"
- **Content**: Video title + full transcript
- **Author**: Channel name
- **URL**: Full YouTube video URL (e.g., `https://www.youtube.com/watch?v=VIDEO_ID`)
- **Timestamp**: Video publish date

## 📋 Setup Required

### 1. Get YouTube API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable "YouTube Data API v3"
3. Create API key
4. Add to `backend/.env`:
   ```bash
   YOUTUBE_API_KEY=your_key_here
   ```

### 2. Restart Backend
```bash
pkill -f "uvicorn main:app"
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

## 🚀 Usage

### Automatic (Recommended)
The scraper runs automatically via Celery:
- Scheduled: Every hour (via `scrape_all_sources` task)
- Includes: YouTube, Twitter, Google News

### Manual Trigger
```bash
cd backend
python trigger_scrape.py
```

### Test Directly
```python
from app.scraper_youtube import YouTubeScraper

scraper = YouTubeScraper()
videos = await scraper.fetch_posts(["Sheinbaum"])
```

## 📊 API Quota

- **Default**: 10,000 units/day
- **Per scrape**: ~550 units
- **Scrapes/day**: ~18 full scrapes

Monitor usage in Google Cloud Console.

## 🔍 Verification

### Check if videos are being scraped:
```sql
SELECT platform, COUNT(*) 
FROM sources 
WHERE platform = 'YouTube' 
GROUP BY platform;
```

### View recent YouTube sources:
```sql
SELECT id, author, url, timestamp 
FROM sources 
WHERE platform = 'YouTube' 
ORDER BY timestamp DESC 
LIMIT 10;
```

### Check claims from YouTube:
```sql
SELECT c.id, c.claim_text, s.url 
FROM claims c 
JOIN sources s ON c.source_id = s.id 
WHERE s.platform = 'YouTube' 
ORDER BY c.created_at DESC;
```

## 📝 Files Modified/Created

1. **New**: `backend/app/scraper_youtube.py` - YouTube scraper implementation
2. **Updated**: `backend/app/tasks/scraper.py` - Added YouTube to scraping task
3. **Updated**: `backend/app/scraper.py` - Added YouTube import
4. **Updated**: `backend/requirements.txt` - Added YouTube dependencies
5. **Updated**: `backend/ENV_SETUP.md` - Added YouTube API key config
6. **Updated**: `backend/app/agent.py` - Removed YouTube exclusion comment
7. **New**: `YOUTUBE_SETUP.md` - Complete setup guide
8. **New**: `YOUTUBE_INTEGRATION_SUMMARY.md` - This file

## ✅ Next Steps

1. **Add API Key**: Get YouTube API key and add to `.env`
2. **Restart Backend**: Reload to pick up new scraper
3. **Test**: Run scraper manually or wait for scheduled run
4. **Verify**: Check database for YouTube sources
5. **Monitor**: Watch logs and API quota usage

## 🎉 Result

YouTube videos are now:
- ✅ Automatically scraped
- ✅ Transcribed (Spanish/English)
- ✅ Stored in database
- ✅ Fact-checked like other sources
- ✅ Linked with video URLs
- ✅ Focused on Mexico political content

