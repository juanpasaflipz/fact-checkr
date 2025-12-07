# Facebook & Instagram Integration Setup

This guide covers setting up Facebook Graph API and Instagram Basic Display API integration for expanded fact-checking coverage.

## Facebook Graph API Setup

### 1. Create Facebook App
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app or use existing one
3. Add "Facebook Login" product to your app

### 2. Configure Graph API
1. In your app dashboard, go to Settings > Basic
2. Note your App ID and App Secret
3. Add the following environment variables:

```bash
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_access_token
FACEBOOK_PAGE_ACCESS_TOKEN=page_specific_token
```

### 3. Generate Access Tokens

#### User Access Token (for public pages)
```bash
curl -X GET "https://graph.facebook.com/oauth/access_token?client_id={app-id}&client_secret={app-secret}&grant_type=client_credentials"
```

#### Page Access Token (for specific pages)
1. Get user access token first
2. Get page access token:
```bash
curl -X GET "https://graph.facebook.com/{user-id}/accounts?access_token={user-access-token}"
```

### 4. Required Permissions
- `pages_read_engagement` - Read page engagement
- `pages_show_list` - Access page list
- `public_profile` - Basic profile access

## Instagram Basic Display API Setup

### 1. Add Instagram Basic Display to Facebook App
1. In your Facebook app, add "Instagram Basic Display" product
2. Configure OAuth redirect URIs (can be localhost for development)

### 2. Generate Instagram Access Token
1. Go to [Instagram Basic Display](https://developers.facebook.com/docs/instagram-basic-display-api/getting-started)
2. Generate token for your Instagram account
3. Add environment variables:

```bash
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
INSTAGRAM_USER_ID=your_instagram_user_id
```

### 3. Required Permissions
- `user_profile` - Read user profile info
- `user_media` - Read user media

## Environment Variables Summary

Add these to your `.env` file:

```bash
# Facebook API
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_access_token
FACEBOOK_PAGE_ACCESS_TOKEN=page_specific_token

# Instagram API
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
INSTAGRAM_USER_ID=your_instagram_user_id
```

## Monitored Pages & Accounts

The system monitors these Mexican political entities:

### Facebook Pages
- gobierno.mexico (Official government)
- lopezobrador.org (President López Obrador)
- PRI.Nacional (PRI Party)
- PAN (PAN Party)
- prd.mx (PRD Party)
- MorenaOficial (Morena Party)
- claudia.sheinbaum (Claudia Sheinbaum)
- XochitlGalvez (Xóchitl Gálvez)

### Instagram Accounts
- Configurable via INSTAGRAM_USER_ID
- Can monitor political figures and organizations

## Rate Limits & Best Practices

### Facebook Graph API
- 200 calls per hour for most endpoints
- 100 posts per call maximum
- Use batch requests when possible

### Instagram Basic Display API
- 200 calls per hour
- 25 media objects per call maximum

### Best Practices
1. **Caching**: Cache API responses for 15-30 minutes
2. **Rate Limiting**: Implement exponential backoff
3. **Error Handling**: Handle token expiration gracefully
4. **Monitoring**: Track API usage and success rates

## Testing the Integration

### 1. Test Facebook Connection
```bash
# Test basic API connectivity
curl "https://graph.facebook.com/me?access_token=YOUR_TOKEN"
```

### 2. Test Instagram Connection
```bash
# Test Instagram API
curl "https://graph.instagram.com/me?fields=id,username&access_token=YOUR_TOKEN"
```

### 3. Run Scrapers
```python
from app.scraper import FacebookScraper, InstagramScraper

fb_scraper = FacebookScraper()
posts = await fb_scraper.fetch_posts(['amlo', 'reforma'])

ig_scraper = InstagramScraper()
posts = await ig_scraper.fetch_posts(['politica', 'mexico'])
```

## Troubleshooting

### Common Issues

1. **Token Expired**
   - Regenerate access tokens
   - Check token expiration dates

2. **Rate Limited**
   - Implement backoff strategy
   - Reduce request frequency

3. **Permission Denied**
   - Verify app permissions
   - Check page access tokens

4. **Invalid API Response**
   - Update API version
   - Check for deprecated endpoints

### Monitoring

Track these metrics:
- API success rate
- Token refresh frequency
- Posts collected per platform
- Duplicate detection effectiveness

## Security Considerations

1. **Token Storage**: Never commit tokens to version control
2. **Token Rotation**: Implement automatic token refresh
3. **Access Control**: Limit API access to necessary permissions
4. **Logging**: Don't log sensitive API responses

## Cost & Scaling

### Facebook Graph API
- Free tier: 200 calls/hour
- Paid tier available for higher limits

### Instagram Basic Display API
- Free tier: 200 calls/hour
- No paid tier available

### Optimization Strategies
1. **Batch Requests**: Combine multiple API calls
2. **Smart Polling**: Only check recently active pages
3. **Content Filtering**: Filter content before full processing
4. **Caching Layer**: Cache results to reduce API calls
