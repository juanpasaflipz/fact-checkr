# 🚀 Deployment Ready!

Your FactCheckr MX application is now ready for production deployment.

---

## 📦 What's Been Created

### Docker Files
- ✅ `backend/Dockerfile` - Backend API container
- ✅ `backend/Dockerfile.worker` - Celery worker container
- ✅ `frontend/Dockerfile` - Frontend Next.js container
- ✅ `docker-compose.yml` - Complete stack orchestration
- ✅ `.dockerignore` files - Optimized builds

### Deployment Scripts
- ✅ `deploy.sh` - Automated deployment script
- ✅ `backend/backend_manager.sh` - Backend process management
- ✅ `backend/worker_manager.sh` - Worker process management

### Platform Configs
- ✅ `railway.json` - Railway deployment config
- ✅ `vercel.json` - Vercel deployment config

### Documentation
- ✅ `PRODUCTION_DEPLOYMENT.md` - Complete deployment guide
- ✅ `DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist
- ✅ `DEPLOY_GUIDE.md` - Original deployment guide (updated)

---

## 🎯 Quick Start - Choose Your Path

### Path 1: Docker Compose (Self-Hosted VPS/Server)

**Best for:** Full control, cost-effective, dedicated server

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your production values

# 2. Deploy everything
./deploy.sh docker

# 3. Verify
docker-compose ps
curl http://localhost:8000/health
```

**What you get:**
- Backend API (port 8000)
- Frontend (port 3000)
- Redis
- Celery Worker
- Celery Beat Scheduler

---

### Path 2: Vercel + Railway (Serverless)

**Best for:** Easy scaling, managed infrastructure, zero DevOps

#### Frontend → Vercel
1. Go to [vercel.com](https://vercel.com)
2. Import GitHub repository
3. Set **Root Directory**: `frontend`
4. Add environment variables:
   - `NEXT_PUBLIC_API_URL=https://your-backend.railway.app`
   - `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...`
5. Deploy (automatic)

#### Backend → Railway
1. Go to [railway.app](https://railway.app)
2. New Project → GitHub Repo
3. Set **Root Directory**: `backend`
4. Add environment variables (see checklist)
5. Set **Start Command**: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
6. Deploy

#### Workers → Railway (Separate Service)
1. Add new service (same repo)
2. Set **Start Command**: `celery -A app.worker worker --loglevel=info --concurrency=2`
3. Deploy

**Cost:** ~$5-10/month (small scale)

---

### Path 3: Fly.io (Global Distribution)

**Best for:** Global edge deployment, low latency

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

## ✅ Pre-Deployment Checklist

### Required Environment Variables

**Backend:**
```bash
DATABASE_URL=postgresql://...          # Neon PostgreSQL
REDIS_URL=redis://...                  # Redis Cloud
JWT_SECRET_KEY=...                     # Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
ANTHROPIC_API_KEY=sk-ant-...           # Or OPENAI_API_KEY
CORS_ORIGINS=https://your-domain.com   # Your frontend domain
FRONTEND_URL=https://your-domain.com
ENVIRONMENT=production
```

**Frontend:**
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### Database Setup
```bash
# 1. Create Neon database
# 2. Run migrations
cd backend
source venv/bin/activate
alembic upgrade head

# 3. Seed topics (optional)
python seed_topics.py
```

---

## 🔧 Deployment Commands

### Docker Compose
```bash
# Deploy all services
./deploy.sh docker

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart
```

### Manual Deployment
```bash
# Backend
cd backend
./deploy.sh backend

# Frontend
cd frontend
./deploy.sh frontend
```

---

## 📊 Architecture

```
┌─────────────┐
│   Frontend  │  Next.js (Vercel)
│  (Port 3000)│
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────┐
│   Backend   │  FastAPI (Railway/Fly.io)
│  (Port 8000)│
└──────┬──────┘
       │
       ├──► PostgreSQL (Neon)
       │
       └──► Redis ──► Celery Workers
                      ├── Worker (scraping)
                      └── Beat (scheduler)
```

---

## 🎯 Recommended Setup for Production

### Small Scale (< 1K users/day)
- **Frontend:** Vercel (Free tier)
- **Backend:** Railway ($5/month)
- **Database:** Neon (Free tier)
- **Redis:** Redis Cloud (Free tier)
- **Workers:** Railway ($5/month)
- **Total:** ~$10/month

### Medium Scale (1K-10K users/day)
- **Frontend:** Vercel Pro ($20/month)
- **Backend:** Railway ($20/month, auto-scale)
- **Database:** Neon Pro ($19/month)
- **Redis:** Redis Cloud ($10/month)
- **Workers:** Railway ($20/month)
- **Total:** ~$90/month

---

## 🚨 Important Notes

1. **Generate JWT Secret:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Use Pooled Database Endpoint:**
   - Neon provides pooled endpoints for serverless
   - Format: `postgresql://user:pass@host-pooler.neon.tech/db?sslmode=require`

3. **CORS Configuration:**
   - Must include your frontend domain
   - Use `https://` in production
   - Example: `CORS_ORIGINS=https://your-app.vercel.app`

4. **Stripe Webhooks:**
   - Configure in Stripe Dashboard
   - Endpoint: `https://api.yourdomain.com/subscriptions/webhook`
   - Copy signing secret to `STRIPE_WEBHOOK_SECRET`

---

## 📚 Documentation

- **Full Guide:** `PRODUCTION_DEPLOYMENT.md`
- **Checklist:** `DEPLOYMENT_CHECKLIST.md`
- **Original Guide:** `DEPLOY_GUIDE.md`

---

## 🎉 Next Steps

1. **Choose deployment platform** (Docker, Vercel+Railway, or Fly.io)
2. **Set up environment variables**
3. **Run database migrations**
4. **Deploy backend**
5. **Deploy frontend**
6. **Deploy workers**
7. **Verify health checks**
8. **Set up monitoring**

---

**Ready to deploy?** Follow `DEPLOYMENT_CHECKLIST.md` for step-by-step instructions!

