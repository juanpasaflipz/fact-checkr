# WhatsApp & Telegraph Integration Summary

## Overview

The FactCheckr MX backend now supports two new frontend channels:

1. **WhatsApp**: Users can verify claims by sending messages via WhatsApp
2. **Telegraph**: Fact-check articles are automatically published to Telegraph (Telegra.ph)

## Architecture Changes

### New Routers

- `app/routers/whatsapp.py` - WhatsApp webhook and message handling
- `app/routers/telegraph.py` - Telegraph publishing integration

### API Endpoints

#### WhatsApp Endpoints

- `GET /whatsapp/webhook` - Webhook verification (Meta calls this)
- `POST /whatsapp/webhook` - Receive incoming messages
- `POST /whatsapp/send?to={phone}&message={text}` - Send message (admin/testing)
- `GET /whatsapp/claims/{claim_id}` - Get claim formatted for WhatsApp

#### Telegraph Endpoints

- `POST /telegraph/publish/{claim_id}` - Publish claim to Telegraph
- `POST /telegraph/publish/batch` - Publish multiple claims
- `GET /telegraph/recent?limit=10&status=verified` - Get recent claims
- `POST /telegraph/create-page` - Create custom Telegraph page

## How It Works

### WhatsApp Flow

1. User sends text message to WhatsApp Business number
2. Meta sends webhook to `/whatsapp/webhook`
3. Backend searches database for matching claims
4. If found: sends formatted verification result
5. If not found: triggers fact-check process (async)

### Telegraph Flow

1. Claim is verified by fact-checker
2. Backend formats claim as Telegraph article
3. Article is published to Telegraph via API
4. URL is returned for sharing

## Setup Required

### WhatsApp

1. Meta Business Account
2. WhatsApp Business API access
3. Environment variables:
   - `WHATSAPP_VERIFY_TOKEN`
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_ACCESS_TOKEN`

### Telegraph

1. No setup required (auto-creates account)
2. Optional: `TELEGRAPH_ACCESS_TOKEN` for persistent account

## Testing

### Local Development

Use ngrok to expose local server for WhatsApp webhooks:

```bash
ngrok http 8000
# Use ngrok URL in Meta webhook config
```

### Test Endpoints

```bash
# Test WhatsApp send
curl -X POST "http://localhost:8000/whatsapp/send?to=+1234567890&message=Test"

# Test Telegraph publish
curl -X POST "http://localhost:8000/telegraph/publish/{claim_id}"
```

## Next Steps

1. Set up Meta Business account for WhatsApp
2. Configure webhook URL in Meta Dashboard
3. Test with sample messages
4. Set up automated publishing workflow
5. Monitor usage and errors

## Documentation

- Full setup guide: `WHATSAPP_TELEGRAPH_SETUP.md`
- Environment variables: `ENV_SETUP.md`

