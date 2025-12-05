# Environment Variables Setup

Complete guide for configuring environment variables for backend and frontend.

## Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Database Configuration
# PostgreSQL connection string
# Format: postgresql://[user[:password]@][host][:port][/database]
DATABASE_URL=postgresql://factcheckr_user:your_secure_password@localhost/factcheckr

# Redis Configuration (for Celery message broker and result backend)
REDIS_URL=redis://localhost:6379/0

# CORS Configuration (comma-separated list of allowed origins)
# Default: http://localhost:3000
CORS_ORIGINS=http://localhost:3000

# AI API Keys (at least one required for fact-checking functionality)
# Anthropic (Primary) - Claude Sonnet 3.5 for superior fact-checking accuracy
# Get your API key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenAI (Backup) - Used as fallback if Anthropic fails
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Market Intelligence Model (optional)
# Default: "haiku" (Claude Haiku 3.5 - fast and cheap, recommended)
# Options: "haiku", "sonnet", "gpt-mini", "gpt-4o"
# The system will automatically use Sonnet for high-value markets (politics, economy)
MARKET_INTELLIGENCE_MODEL=haiku

# Serper API Key (required for web search/evidence gathering)
# Get your API key from: https://serper.dev/
SERPER_API_KEY=your_serper_api_key_here

# Twitter/X API Credentials (optional - app will use mock data if not provided)
# Get credentials from: https://developer.twitter.com/en/portal/dashboard
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# YouTube Data API Key (required for YouTube video scraping and transcription)
# Get your API key from: https://console.cloud.google.com/apis/credentials
# Enable "YouTube Data API v3" in Google Cloud Console
YOUTUBE_API_KEY=your_youtube_api_key_here

# JWT Secret Key (for authentication - change in production!)
# Generate a secure random string for production
JWT_SECRET_KEY=your-secret-key-change-in-production

# Stripe Configuration (required for subscription management)
# Get your API keys from: https://dashboard.stripe.com/apikeys
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Stripe Price IDs (create products/prices in Stripe dashboard)
# Format: price_xxxxxxxxxxxxx
STRIPE_PRO_MONTHLY_PRICE_ID=price_your_pro_monthly_price_id
STRIPE_PRO_YEARLY_PRICE_ID=price_your_pro_yearly_price_id
STRIPE_TEAM_MONTHLY_PRICE_ID=price_your_team_monthly_price_id
STRIPE_TEAM_YEARLY_PRICE_ID=price_your_team_yearly_price_id

# Frontend URL (for Stripe checkout redirects)
FRONTEND_URL=http://localhost:3000

# WhatsApp Configuration (optional - for WhatsApp integration)
# Get credentials from: https://developers.facebook.com/docs/whatsapp
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token_here
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_ACCESS_TOKEN=your_access_token_here

# Telegraph Configuration (optional - auto-creates account if not provided)
# Get access token from: https://telegra.ph/api
TELEGRAPH_ACCESS_TOKEN=your_telegraph_access_token_here

# Environment
ENVIRONMENT=development  # or 'production'
```

## Frontend Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
# Backend API URL
# Default: http://localhost:8000
# Change this if your backend is running on a different host/port
NEXT_PUBLIC_API_URL=http://localhost:8000

# Stripe Publishable Key (required for Stripe checkout)
# Get your publishable key from: https://dashboard.stripe.com/apikeys
# Use test key (pk_test_...) for development, live key (pk_live_...) for production
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
```

## Required vs Optional Variables

### Backend - Required
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection for Celery (defaults to `redis://localhost:6379/0` if not set)

### Backend - Optional but Recommended
- `ANTHROPIC_API_KEY` - Primary AI service for fact-checking using Claude Sonnet 3.5. Provides superior accuracy.
- `OPENAI_API_KEY` - Backup AI service. Automatically used if Anthropic fails, ensuring reliability. At least one AI API key is recommended.
- `SERPER_API_KEY` - Required for real web search and evidence gathering. Without it, the system will use mock search results.

### Backend - Optional
- Twitter credentials - If not provided, the app will use mock data for Twitter posts.
- `JWT_SECRET_KEY` - For authentication endpoints (defaults to insecure key if not set)
- Stripe configuration - Required for subscription management. See Stripe Dashboard to create products/prices and get API keys.
- `YOUTUBE_API_KEY` - Required for YouTube video scraping and transcription. Get from [Google Cloud Console](https://console.cloud.google.com/apis/credentials). Enable "YouTube Data API v3".
- WhatsApp/Telegraph - Optional integrations

### Frontend - Required
- `NEXT_PUBLIC_API_URL` - Backend API URL (defaults to `http://localhost:8000` if not set)

### Frontend - Optional but Recommended
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` - Required for subscription checkout. Get from [Stripe Dashboard](https://dashboard.stripe.com/apikeys). Use `pk_test_...` for development, `pk_live_...` for production.

## Quick Setup

### Backend
```bash
cd backend
touch .env
# Add the variables above with your actual values
```

### Frontend
```bash
cd frontend
touch .env.local
# Add: NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Notes

- Next.js requires the `NEXT_PUBLIC_` prefix for environment variables that should be accessible in the browser
- The default value is `http://localhost:8000` if the variable is not set
- Restart the Next.js dev server after changing environment variables
- Never commit `.env` or `.env.local` files to version control

