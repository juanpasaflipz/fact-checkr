# Deployment Checklist

Quick checklist for deploying FactCheckr MX to production.

---

## Pre-Deployment

### Environment Setup
- [ ] Copy `.env.example` to `.env` (if using Docker)
- [ ] Set `DATABASE_URL` (Neon PostgreSQL)
- [ ] Set `REDIS_URL` (Redis Cloud or self-hosted)
- [ ] Set `JWT_SECRET_KEY` (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- [ ] Set `CORS_ORIGINS` to your frontend domain
- [ ] Set `FRONTEND_URL` to your frontend domain
- [ ] Set `ENVIRONMENT=production`

### Database
- [ ] Create Neon PostgreSQL database
- [ ] Run migrations: `cd backend && alembic upgrade head`
- [ ] Seed topics: `python seed_topics.py` (optional)

### Redis
- [ ] Set up Redis (Redis Cloud or self-hosted)
- [ ] Test connection: `redis-cli ping`

### Stripe (if using payments)
- [ ] Set `STRIPE_SECRET_KEY` (live key)
- [ ] Set `STRIPE_WEBHOOK_SECRET`
- [ ] Configure webhook endpoint
- [ ] Set price IDs

---

## Deployment Options

### Option 1: Docker Compose (Self-Hosted)

```bash
# 1. Configure
cp .env.example .env
# Edit .env with production values

# 2. Deploy
./deploy.sh docker

# 3. Verify
docker-compose ps
curl http://localhost:8000/health
```

**Checklist:**
- [ ] Docker and Docker Compose installed
- [ ] Environment variables configured
- [ ] Services running: `docker-compose ps`
- [ ] Backend health check passes
- [ ] Frontend accessible
- [ ] Workers processing tasks

---

### Option 2: Vercel (Frontend) + Railway (Backend)

#### Frontend - Vercel
- [ ] Import GitHub repository
- [ ] Set root directory: `frontend`
- [ ] Add environment variables:
  - `NEXT_PUBLIC_API_URL=https://your-backend.railway.app`
  - `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...`
- [ ] Deploy

#### Backend - Railway
- [ ] Create new project
- [ ] Connect GitHub repository
- [ ] Set root directory: `backend`
- [ ] Add all backend environment variables
- [ ] Set start command: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
- [ ] Set health check: `/health`
- [ ] Deploy

#### Workers - Railway (Separate Service)
- [ ] Add background worker service
- [ ] Set start command: `celery -A app.worker worker --loglevel=info --concurrency=2`
- [ ] Add environment variables (same as backend)
- [ ] Deploy

#### Beat Scheduler - Railway (Optional)
- [ ] Add beat service
- [ ] Set start command: `celery -A app.worker beat --loglevel=info`
- [ ] Deploy

**Checklist:**
- [ ] Frontend deployed and accessible
- [ ] Backend deployed and health check passes
- [ ] Workers deployed and processing tasks
- [ ] CORS configured correctly
- [ ] API endpoints responding

---

### Option 3: Fly.io

```bash
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

**Checklist:**
- [ ] Fly.io CLI installed
- [ ] Backend deployed
- [ ] Frontend deployed
- [ ] Workers deployed (separate app)

---

## Post-Deployment Verification

### Health Checks
- [ ] Backend: `curl https://api.yourdomain.com/health`
- [ ] Frontend: `curl https://yourdomain.com`
- [ ] API endpoints responding

### Functionality Tests
- [ ] Frontend loads without errors
- [ ] Claims API returns data
- [ ] Stats API returns data
- [ ] Search functionality works
- [ ] Authentication works (if enabled)
- [ ] Stripe checkout works (if enabled)

### Worker Verification
- [ ] Workers are running
- [ ] Tasks are being processed
- [ ] Hourly scraping is working
- [ ] Health check task runs every 5 minutes

### Monitoring Setup
- [ ] Uptime monitoring configured (Uptime Robot)
- [ ] Error tracking configured (Sentry - optional)
- [ ] Logs accessible
- [ ] Alerts configured

---

## Security Checklist

- [ ] `JWT_SECRET_KEY` is unique and secure
- [ ] `ENVIRONMENT=production` is set
- [ ] CORS only allows your frontend domain
- [ ] HTTPS enabled on all endpoints
- [ ] API keys are not exposed in frontend
- [ ] Database credentials are secure
- [ ] Stripe webhook signature verification enabled
- [ ] Rate limiting is appropriate

---

## Quick Commands

```bash
# Deploy with Docker
./deploy.sh docker

# Deploy backend only
./deploy.sh backend

# Deploy frontend only
./deploy.sh frontend

# Check status (Docker)
docker-compose ps
docker-compose logs -f

# Run migrations
cd backend && alembic upgrade head

# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Troubleshooting

### Backend won't start
- Check environment variables
- Check database connection
- Check logs: `docker-compose logs backend` or platform logs

### Workers not processing
- Check Redis connection
- Check worker logs
- Verify tasks are registered

### CORS errors
- Verify `CORS_ORIGINS` includes frontend domain
- Check protocol (https:// not http://)
- Restart backend after changing CORS

---

**Ready?** Choose your deployment option and follow the checklist!

