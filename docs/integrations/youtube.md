# YouTube Integration Setup

Guide for setting up YouTube Data API for video scraping and transcription.

## Quick Start

1. **Get API Key** from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. **Enable YouTube Data API v3** in your project
3. **Add to Backend Environment**:
   ```bash
   YOUTUBE_API_KEY=your_youtube_api_key_here
   ```

## Detailed Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable billing (required for API access)

### 2. Enable YouTube Data API v3

1. Navigate to **APIs & Services > Library**
2. Search for "YouTube Data API v3"
3. Click **Enable**

### 3. Create API Key

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > API Key**
3. Copy the API key
4. (Optional) Restrict the key to YouTube Data API v3 for security

### 4. Configure Backend

Add to `backend/.env`:

```bash
YOUTUBE_API_KEY=your_youtube_api_key_here
```

## Usage

The YouTube integration is used for:
- Scraping video metadata
- Transcribing video content
- Fact-checking video claims

The scraper automatically uses this API key when processing YouTube URLs.

## Testing

Test the API key:

```bash
cd backend
python test_youtube_api.py
```

## Quota Limits

YouTube Data API v3 has default quotas:
- **10,000 units per day** (free tier)
- Each video search costs ~100 units
- Each video details request costs ~1 unit

Monitor usage in Google Cloud Console to avoid quota exhaustion.

## Troubleshooting

### API Key Invalid
- Verify key is copied correctly
- Check API is enabled in Google Cloud Console
- Ensure billing is enabled

### Quota Exceeded
- Wait for daily reset (midnight Pacific Time)
- Request quota increase in Google Cloud Console
- Optimize API calls (cache results)

### Rate Limiting
- The scraper includes rate limiting
- Adjust delays in `backend/app/scraper_youtube.py` if needed

