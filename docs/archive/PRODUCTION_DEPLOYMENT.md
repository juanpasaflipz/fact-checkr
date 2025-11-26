# Production Deployment Guide

Complete guide for deploying FactCheckr MX to production.

---

## Quick Start

### Option 1: Docker Compose (Recommended for VPS/Server)

```bash
# 1. Set environment variables
cp .env.example .env
# Edit .env with your production values

# 2. Deploy
chmod +x deploy.sh
./deploy.sh docker

# 3. Check status
docker-compose ps
docker-compose logs -f
```

### Option 2: Platform Deployment (Vercel + Railway/Render)

**Frontend (Vercel):**
1. Connect GitHub repo
2. Set root directory: `frontend`
3. Add environment variables
4. Deploy

**Backend (Railway/Render):**
1. Connect GitHub repo
2. Set root directory: `backend`
3. Add environment variables
4. Set start command: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
5. Deploy

---

## Pre-Deployment Checklist

### 1. Environment Variables

**Backend (.env or platform env vars):**
```bash
# Database
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

# AI APIs (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Authentication
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# CORS (your frontend domain)
CORS_ORIGINS=https://your-domain.vercel.app
FRONTEND_URL=https://your-domain.vercel.app

# Redis (for Celery)
REDIS_URL=redis://your-redis-host:6379/0

# Stripe (if using payments)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Optional APIs
SERPER_API_KEY=...
TWITTER_BEARER_TOKEN=...
YOUTUBE_API_KEY=...

# Environment
ENVIRONMENT=production
```

**Frontend (Vercel environment variables):**
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### 2. Database Setup

```bash
# Run migrations
cd backend
source venv/bin/activate
alembic upgrade head

# Seed initial data (optional)
python seed_topics.py
```

### 3. Generate JWT Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Deployment Options

### A. Docker Compose (Self-Hosted)

**Best for:** VPS, dedicated server, cloud VM

```bash
# 1. Install Docker & Docker Compose
# 2. Clone repository
git clone <your-repo>
cd fact-checkr

# 3. Configure environment
cp .env.example .env
# Edit .env with production values

# 4. Deploy
./deploy.sh docker

# 5. Monitor
docker-compose logs -f
docker-compose ps
```

**Services included:**
- Backend API (port 8000)
- Frontend (port 3000)
- Redis
- Celery Worker
- Celery Beat

### B. Vercel + Railway/Render

**Best for:** Serverless, easy scaling

#### Frontend (Vercel)

1. **Import Project**
   - Go to [vercel.com](https://vercel.com)
   - Import GitHub repository
   - Set **Root Directory**: `frontend`
   - Framework: Next.js (auto-detected)

2. **Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
   ```

3. **Deploy** - Vercel handles everything automatically

#### Backend (Railway)

1. **Create New Project**
   - Connect GitHub repository
   - Add new service → GitHub repo
   - Set **Root Directory**: `backend`

2. **Environment Variables**
   - Add all backend env vars from checklist above

3. **Settings**
   - **Start Command**: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
   - **Health Check Path**: `/health`

4. **Deploy** - Railway builds and deploys automatically

#### Workers (Railway - Separate Service)

1. **Add Background Worker**
   - Same repo, different service
   - **Start Command**: `celery -A app.worker worker --loglevel=info --concurrency=2`

2. **Add Beat Scheduler** (Optional - separate service)
   - **Start Command**: `celery -A app.worker beat --loglevel=info`

### C. Fly.io

**Best for:** Global distribution, edge computing

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Backend
cd backend
fly launch
fly secrets set DATABASE_URL="..." ANTHROPIC_API_KEY="..." ...
fly deploy

# Frontend
cd frontend
fly launch
fly secrets set NEXT_PUBLIC_API_URL="https://your-backend.fly.dev"
fly deploy
```

---

## Database Setup (Neon)

1. **Create Project** at [neon.tech](https://neon.tech)
2. **Copy Connection String**
   - Use **pooled endpoint** for serverless
   - Format: `postgresql://user:pass@host/db?sslmode=require`
3. **Run Migrations**
   ```bash
   cd backend
   alembic upgrade head
   ```
4. **Enable Connection Pooling** in Neon dashboard

---

## Redis Setup

### Option 1: Redis Cloud (Recommended)
1. Sign up at [redis.com](https://redis.com)
2. Create database
3. Copy connection string: `redis://:password@host:port`
4. Add to `REDIS_URL` environment variable

### Option 2: Self-Hosted (Docker)
```bash
docker run -d -p 6379:6379 redis:7-alpine
REDIS_URL=redis://localhost:6379/0
```

---

## Stripe Webhooks

1. **Stripe Dashboard** → Developers → Webhooks
2. **Add Endpoint**: `https://api.yourdomain.com/subscriptions/webhook`
3. **Select Events**:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. **Copy Signing Secret** → `STRIPE_WEBHOOK_SECRET`

---

## Post-Deployment

### 1. Verify Health

```bash
# Backend
curl https://api.yourdomain.com/health

# Expected: {"status":"healthy","database":"connected"}

# Frontend
curl https://yourdomain.com
```

### 2. Test API Endpoints

```bash
# Claims endpoint
curl https://api.yourdomain.com/claims?skip=0&limit=5

# Stats endpoint
curl https://api.yourdomain.com/stats
```

### 3. Monitor Workers

```bash
# Check worker status (if using Railway/Render)
# View logs in platform dashboard

# Or if using Docker
docker-compose logs celery-worker
docker-compose logs celery-beat
```

### 4. Set Up Monitoring

**Uptime Monitoring:**
- [Uptime Robot](https://uptimerobot.com)
- [Better Uptime](https://betteruptime.com)
- Monitor: `https://api.yourdomain.com/health`

**Error Tracking:**
- [Sentry](https://sentry.io) (recommended)
- Add to backend: `pip install sentry-sdk[fastapi]`

---

## Scaling

### Small (< 1K users/day)
- Backend: 1 instance
- Workers: 1 worker
- Database: Neon Free tier

### Medium (1K-10K users/day)
- Backend: 2 instances (auto-scale)
- Workers: 2 workers
- Database: Neon Pro tier

### Large (10K+ users/day)
- Backend: Auto-scale (4+ instances)
- Workers: 4+ workers
- Database: Neon Scale tier
- Redis: Dedicated instance
- CDN: Cloudflare for frontend

---

## Security Checklist

- [ ] Generate unique `JWT_SECRET_KEY` for production
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure CORS to only allow your frontend domain
- [ ] Enable HTTPS on all endpoints
- [ ] Review rate limits in `backend/app/rate_limit.py`
- [ ] Set up error monitoring (Sentry)
- [ ] Enable database connection pooling
- [ ] Use environment variables (never commit secrets)
- [ ] Enable Stripe webhook signature verification
- [ ] Set up firewall rules (if self-hosting)
- [ ] Regular security updates

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend
# Or in Railway/Render: View logs in dashboard

# Common issues:
# - Missing environment variables
# - Database connection failed
# - Port already in use
```

### Workers not processing tasks
```bash
# Check Redis connection
redis-cli ping

# Check worker logs
docker-compose logs celery-worker

# Verify tasks are registered
celery -A app.worker inspect registered
```

### CORS errors
```bash
# Verify CORS_ORIGINS includes frontend domain
echo $CORS_ORIGINS

# Check protocol (https:// not http://)
# Restart backend after changing CORS_ORIGINS
```

### Database connection timeout
```bash
# Check Neon is not suspended (free tier auto-suspends)
# Verify using pooled endpoint
# Check connection string format
```

---

## Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
./deploy.sh docker
# Or in Railway/Render: Redeploy from dashboard
```

### Database Migrations

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### Backup Database

Neon provides automatic backups. For manual backup:
```bash
pg_dump $DATABASE_URL > backup.sql
```

---

## Cost Estimation

### Small Scale (Vercel + Railway)
- Vercel: Free tier (hobby)
- Railway: ~$5-10/month
- Neon: Free tier
- Redis Cloud: Free tier
- **Total: ~$5-10/month**

### Medium Scale
- Vercel: Pro ($20/month)
- Railway: ~$20-30/month
- Neon: Pro ($19/month)
- Redis Cloud: $10/month
- **Total: ~$70-80/month**

---

## Support

For deployment issues:
1. Check logs: `docker-compose logs` or platform dashboard
2. Verify environment variables
3. Test health endpoints
4. Check database/Redis connectivity

---

**Ready to deploy?** Start with `./deploy.sh docker` or follow platform-specific guides above.

