# WhatsApp & Telegraph Integration Setup

This guide covers setting up WhatsApp and Telegraph (Telegra.ph) integrations for FactCheckr MX.

## Architecture Overview

The backend API now supports two new frontend channels:

1. **WhatsApp**: Users can send messages to verify claims via WhatsApp
2. **Telegraph**: Fact-check articles are automatically published to Telegraph

## WhatsApp Integration

### Prerequisites

1. **Meta Business Account**: You need a Meta Business account
2. **WhatsApp Business API**: Access to WhatsApp Business API (via Meta)
3. **Phone Number**: A verified phone number for WhatsApp Business

### Setup Steps

#### 1. Create Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new app or use existing
3. Add "WhatsApp" product to your app
4. Complete Business Verification (if required)

#### 2. Get Credentials

You'll need:
- **Phone Number ID**: Found in WhatsApp > API Setup
- **Access Token**: Generate a temporary token or use a permanent token
- **Verify Token**: Create a custom token (e.g., `factcheckr_verify_2024`)

#### 3. Configure Webhook

1. In Meta App Dashboard > WhatsApp > Configuration
2. Set Webhook URL: `https://your-domain.com/whatsapp/webhook`
3. Set Verify Token: (use the same token from step 2)
4. Subscribe to `messages` field

#### 4. Environment Variables

Add to `backend/.env`:

```bash
# WhatsApp Configuration
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token_here
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_ACCESS_TOKEN=your_access_token_here
```

#### 5. Test Webhook

```bash
# Verify webhook (Meta will call this)
curl "https://your-domain.com/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=your_custom_verify_token_here&hub.challenge=1234567890"
```

### API Endpoints

#### Webhook Verification
```
GET /whatsapp/webhook
```
Called by Meta to verify webhook URL.

#### Receive Messages
```
POST /whatsapp/webhook
```
Receives incoming WhatsApp messages.

#### Send Message (Admin)
```
POST /whatsapp/send?to=+1234567890&message=Hello
```
Manually send WhatsApp message (for testing).

#### Get Claim for WhatsApp
```
GET /whatsapp/claims/{claim_id}
```
Get claim formatted for WhatsApp display.

### How It Works

1. User sends text message to WhatsApp Business number
2. Meta sends webhook to `/whatsapp/webhook`
3. Backend searches database for matching claims
4. If found, sends formatted verification result
5. If not found, triggers fact-check process (async)

### Message Format

WhatsApp messages are formatted with:
- ✅/❌/⚠️/❓ emojis for status
- Bold text for headers
- Source links
- Explanation text

## Telegraph Integration

### Prerequisites

None! Telegraph API is public and doesn't require authentication for basic usage.

### Setup Steps

#### 1. Get Access Token (Optional)

For better control, create a Telegraph account:

1. Go to [Telegra.ph](https://telegra.ph/)
2. Create an account (optional)
3. Get access token from API response

#### 2. Environment Variables

Add to `backend/.env` (optional):

```bash
# Telegraph Configuration (optional)
TELEGRAPH_ACCESS_TOKEN=your_access_token_here
```

If not provided, the system will auto-create an account.

### API Endpoints

#### Publish Claim
```
POST /telegraph/publish/{claim_id}
```
Publishes a fact-check claim to Telegraph.

**Response:**
```json
{
  "path": "FactCheckr-MX-12-25",
  "url": "https://telegra.ph/FactCheckr-MX-12-25",
  "title": "✅ Verificación: ...",
  "author_name": "FactCheckr MX",
  "views": 0,
  "can_edit": true
}
```

#### Publish Batch
```
POST /telegraph/publish/batch
Body: ["claim_id_1", "claim_id_2", ...]
```
Publish multiple claims at once.

#### Get Recent Claims
```
GET /telegraph/recent?limit=10&status=verified
```
Get recent claims ready for publishing.

#### Create Custom Page
```
POST /telegraph/create-page
Body: {
  "title": "Custom Title",
  "content": [...],  # Telegraph content format
  "author_name": "FactCheckr MX"
}
```

### How It Works

1. Claim is verified by fact-checker
2. Backend formats claim as Telegraph article
3. Article is published to Telegraph
4. URL is returned for sharing

### Content Format

Telegraph articles include:
- Status emoji and title
- Claim text
- Verification explanation
- Evidence sources (with links)
- Original source link
- Publication metadata

## Testing

### Test WhatsApp Locally

Use [ngrok](https://ngrok.com/) to expose local server:

```bash
# Terminal 1: Start backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Expose with ngrok
ngrok http 8000

# Use ngrok URL in Meta webhook config:
# https://abc123.ngrok.io/whatsapp/webhook
```

### Test Telegraph

```bash
# Publish a claim
curl -X POST "http://localhost:8000/telegraph/publish/{claim_id}"

# Get recent claims
curl "http://localhost:8000/telegraph/recent?limit=5"
```

## Production Deployment

### WhatsApp

1. **Use Permanent Access Token**: Generate long-lived token in Meta Dashboard
2. **HTTPS Required**: Webhook must use HTTPS
3. **Rate Limits**: Meta has rate limits (check documentation)
4. **Error Handling**: Implement retry logic for failed messages

### Telegraph

1. **Store Access Token**: Save token securely (env var or secrets manager)
2. **Batch Publishing**: Use batch endpoint for multiple claims
3. **Content Validation**: Ensure content follows Telegraph guidelines

## Troubleshooting

### WhatsApp Issues

**Webhook not receiving messages:**
- Verify webhook URL is accessible (HTTPS required)
- Check verify token matches
- Ensure phone number is verified in Meta Dashboard

**Messages not sending:**
- Verify access token is valid
- Check phone number ID is correct
- Review Meta API error responses

### Telegraph Issues

**Page creation fails:**
- Check content format (must be Telegraph content structure)
- Verify title length (max 256 chars)
- Ensure content is valid HTML-like structure

## Security Considerations

1. **Verify Token**: Use strong, random verify token
2. **Access Tokens**: Store securely, never commit to git
3. **Webhook Validation**: Always validate webhook signatures (implement if needed)
4. **Rate Limiting**: Apply rate limits to public endpoints

## Next Steps

1. Set up Meta Business account
2. Configure WhatsApp webhook
3. Test with sample messages
4. Set up automated publishing to Telegraph
5. Monitor usage and errors

## Resources

- [Meta WhatsApp Business API Docs](https://developers.facebook.com/docs/whatsapp)
- [Telegraph API Docs](https://telegra.ph/api)
- [ngrok for Local Testing](https://ngrok.com/)

