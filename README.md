# FactCheckr MX

A comprehensive fact-checking platform for Mexican politics news and media posts. Built with FastAPI (backend) and Next.js (frontend).

## Features

- 🔍 **Automated Fact-Checking** - AI-powered verification of claims using Claude Sonnet 3.5
- 📊 **Real-time Analytics** - Track trending topics, entities, and verification statistics
- 🔄 **Multi-Source Scraping** - Automatically scrape and verify content from Twitter, YouTube, and news sites
- 💳 **Subscription Management** - Stripe integration for Pro and Team tiers
- 📱 **WhatsApp Integration** - Receive and respond to fact-check requests via WhatsApp
- 🌐 **Telegraph Publishing** - Auto-publish verified claims to Telegraph
- 💹 **Prediction Markets** - Market-based consensus for truth verification


## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** (Neon) - Primary database
- **Redis** - Celery message broker
- **Celery** - Background task processing
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations

### Frontend
- **Next.js 16** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Component library

### AI & APIs
- **Anthropic Claude** - Primary fact-checking AI
- **OpenAI GPT** - Fallback AI service
- **Serper API** - Web search for evidence gathering
- **YouTube Data API** - Video scraping and transcription
- **Stripe** - Payment processing

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL (or Neon account)
- Redis

### 1. Clone Repository
```bash
git clone <repository-url>
cd fact-checkr
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file (see docs/setup/environment.md)
cp ENV_SETUP.md .env
# Edit .env with your API keys

# Run migrations
alembic upgrade head

# Seed topics (optional)
python ../scripts/seed_topics.py
```

### 3. Frontend Setup
```bash
cd frontend
npm install  # or pnpm install

# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### 4. Start Services

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Workers:**
```bash
cd backend
source venv/bin/activate
./start_local.sh
```

### 5. Verify
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Documentation

All documentation is organized in the [`docs/`](./docs/) directory:

- **[Setup Guides](./docs/setup/)** - Environment, database, and local development setup
- **[Deployment](./docs/deployment/)** - Production deployment guides and checklists
- **[Integrations](./docs/integrations/)** - Third-party service setup (Stripe, YouTube, etc.)
- **[Development](./docs/development/)** - Development guides and troubleshooting

### Quick Links
- [Environment Setup](./docs/setup/environment.md)
- [Local Development](./docs/development/local-setup.md)
- [Deployment Checklist](./docs/deployment/checklist.md)
- [Stripe Integration](./docs/integrations/stripe.md)

## Project Structure

```
fact-checkr/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── routers/      # API route handlers
│   │   ├── tasks/        # Celery background tasks
│   │   ├── database/     # Database models and connection
│   │   └── ...
│   ├── alembic/          # Database migrations
│   └── main.py           # FastAPI application entry
├── frontend/             # Next.js frontend
│   ├── src/
│   │   ├── app/          # Next.js app router pages
│   │   ├── components/   # React components
│   │   └── lib/          # Utility functions
│   └── ...
├── docs/                  # Documentation
├── scripts/               # Utility scripts
└── docker-compose.yml     # Docker setup
```

## Environment Variables

### Backend (`.env`)
Required:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection for Celery

Recommended:
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` - AI service for fact-checking
- `SERPER_API_KEY` - Web search API
- `YOUTUBE_API_KEY` - YouTube scraping

See [Environment Setup](./docs/setup/environment.md) for complete list.

### Frontend (`.env.local`)
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` - Stripe publishable key

## Deployment

### Automated Deployment (Recommended)

Use the comprehensive deployment script for full automation:

```bash
# Full deployment (migrations + backend + frontend)
./scripts/deploy.sh

# Verify deployment status only
./scripts/deploy.sh --verify-only

# Skip specific steps if needed
./scripts/deploy.sh --skip-migrations
./scripts/deploy.sh --skip-backend
./scripts/deploy.sh --skip-frontend
```

**See:** [Deployment Script Guide](./docs/deployment/DEPLOYMENT_SCRIPT_GUIDE.md) for detailed usage.

### Manual Deployment

#### Quick Deploy (Docker)
```bash
./deploy.sh docker
```

#### Platform Deployment
- **Frontend**: Deploy to Vercel (recommended)
- **Backend**: Deploy to Railway or Render
- **Workers**: Separate service on Railway/Render

See [Deployment Guide](./docs/deployment/production.md) for detailed instructions.

## Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Code Quality
```bash
# Backend
cd backend
black .  # Format code
flake8 .  # Lint code

# Frontend
cd frontend
npm run lint
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
- Check [Documentation](./docs/)
- Review [Troubleshooting Guide](./docs/development/troubleshooting.md)
- Open an issue on GitHub

---

**Built for accurate fact-checking of Mexican political news and media.**

