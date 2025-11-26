# FactCheckr MX - Deployment Guide

## Prerequisites

- **Node.js** >= 20.x
- **Python** >= 3.11
- **PostgreSQL** (Neon recommended) 
- **Redis** (for Celery workers)
- **Stripe** account (for payments)

---

## Backend Deployment (FastAPI)

### Option A: Deploy to Railway / Render

1. **Connect your repository**
2. **Set environment variables** (see backend env vars below)
3. **Start command**: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

### Option B: Deploy to Fly.io

```bash
cd backend
fly launch
fly secrets set DATABASE_URL="postgresql://..." ANTHROPIC_API_KEY="..." ...
fly deploy
```

### Backend Environment Variables (Required)

```bash
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

# AI APIs (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Authentication
JWT_SECRET_KEY=generate-with-python-secrets-token-urlsafe-32

# Environment
ENVIRONMENT=production

# CORS (your frontend domain)
CORS_ORIGINS=https://your-domain.vercel.app
FRONTEND_URL=https://your-domain.vercel.app

# Stripe (if using payments)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Run Database Migrations

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### Seed Initial Data (Optional)

```bash
python seed_topics.py
```

---

## Frontend Deployment (Next.js)

### Deploy to Vercel (Recommended)

1. **Import** your GitHub repository to Vercel
2. **Framework Preset**: Next.js (auto-detected)
3. **Root Directory**: `frontend`
4. **Environment Variables**:

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

5. **Deploy** - Vercel handles build & CDN automatically

### Alternative: Self-hosted

```bash
cd frontend
npm ci --production
npm run build
npm start  # or use PM2
```

---

## Background Workers (Celery)

For production, run Celery workers separately:

```bash
# Install Redis or use Redis Cloud
export REDIS_URL=redis://...

# Start worker
celery -A app.worker worker --loglevel=info

# Start beat scheduler (for periodic tasks)
celery -A app.worker beat --loglevel=info
```

### Worker Hosting Options
- **Railway**: Add a separate service
- **Render**: Background worker service
- **Fly.io**: Separate machine for workers

---

## Database Setup (Neon)

1. Create a project at [neon.tech](https://neon.tech)
2. Copy the pooled connection string
3. Run migrations: `alembic upgrade head`

**Connection Tips:**
- Use **pooled endpoint** for serverless deployments
- Enable **connection pooling** in Neon dashboard
- Set `sslmode=require` in connection string

---

## Stripe Webhooks

1. In Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://api.yourdomain.com/subscriptions/webhook`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copy signing secret to `STRIPE_WEBHOOK_SECRET`

---

## Security Checklist

- [ ] Generate unique `JWT_SECRET_KEY` for production
- [ ] Set `ENVIRONMENT=production` 
- [ ] Configure CORS to only allow your frontend domain
- [ ] Enable HTTPS on all endpoints
- [ ] Review rate limits in `backend/app/rate_limit.py`
- [ ] Set up error monitoring (Sentry recommended)
- [ ] Enable database connection pooling

---

## Health Monitoring

Backend exposes `/health` endpoint for monitoring:

```bash
curl https://api.yourdomain.com/health
# Returns: {"status": "healthy", "database": "connected"}
```

Use this with:
- **Uptime Robot** / **Better Uptime** for alerts
- **Vercel / Railway** built-in health checks
- **Custom monitoring** via the HealthStatus component

---

## Performance Optimization

### Backend
- Connection pool: Already configured for Neon
- Rate limiting: 100 req/min for claims, 60/min for stats
- Caching: Consider Redis for frequent queries

### Frontend  
- Next.js Image optimization: Enabled
- Static optimization: Automatic
- API routes: None (uses external backend)

---

## Scaling Considerations

| Load Level | Backend | Workers | Database |
|------------|---------|---------|----------|
| < 1K users/day | 1 instance | 1 worker | Neon Free |
| 1K-10K users/day | 2 instances | 2 workers | Neon Pro |
| 10K+ users/day | Auto-scale | 4+ workers | Neon Scale |

---

## Troubleshooting

### "Database connection timeout"
- Check Neon is not suspended (auto-suspend on free tier)
- Verify DATABASE_URL is using pooled endpoint
- Increase `pool_timeout` in connection.py

### "CORS errors"
- Verify `CORS_ORIGINS` includes your frontend domain
- Check protocol (https:// vs http://)

### "502 Bad Gateway"
- Check backend logs for startup errors
- Verify all env vars are set
- Check if port binding is correct

---

## Quick Reference

```bash
# Local development
cd backend && source venv/bin/activate && uvicorn main:app --reload
cd frontend && npm run dev

# Build frontend
cd frontend && npm run build

# Run migrations
cd backend && alembic upgrade head

# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

