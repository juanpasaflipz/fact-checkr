# Environment Variables Setup

Create a `.env` file in the `backend/` directory with the following variables:

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

# JWT Secret Key (for authentication - change in production!)
# Generate a secure random string for production
JWT_SECRET_KEY=your-secret-key-change-in-production
```

## Required vs Optional Variables

**Required:**

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection for Celery (defaults to `redis://localhost:6379/0` if not set)

**Optional but Recommended:**

- `ANTHROPIC_API_KEY` - Primary AI service for fact-checking using Claude Sonnet 3.5. Provides superior accuracy.
- `OPENAI_API_KEY` - Backup AI service. Automatically used if Anthropic fails, ensuring reliability. At least one AI API key is recommended.
- `SERPER_API_KEY` - Required for real web search and evidence gathering. Without it, the system will use mock search results.

**Optional:**

- Twitter credentials - If not provided, the app will use mock data for Twitter posts.
- `JWT_SECRET_KEY` - For authentication endpoints (defaults to insecure key if not set)

## Quick Setup

1. Copy this template to create your `.env` file:

```bash
cd backend
cp ENV_SETUP.md .env
# Then edit .env with your actual values
```

2. Or create manually:

```bash
cd backend
touch .env
# Add the variables above with your actual values
```

