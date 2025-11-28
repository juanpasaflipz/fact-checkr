# FactCheckr - Quick Deployment Guide

## 🚀 Deploy in 15 Minutes

### 1. Database (Neon) ✅ DONE
Already set up with connection string in Railway.

### 2. Redis (Railway) - 2 minutes

```
Railway Dashboard → + New → Database → Redis
Name: factcheckr-redis
Copy REDIS_URL
```

### 3. Backend API (Railway) ✅ DONE
Already deployed and running.

**Add Redis URL**:
```
Railway → factcheckr-backend → Variables → Add:
REDIS_URL=<from step 2>
```

### 4. Celery Worker (Railway) - 3 minutes

```
Railway Dashboard → + New → GitHub Repo → fact-checkr
Name: factcheckr-worker
Root Directory: (leave empty)
Railway Config Path: backend/railway-worker.json

Add Variables (copy from backend):
- DATABASE_URL
- REDIS_URL
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- PERPLEXITY_API_KEY

Deploy
```

### 5. Celery Beat (Railway) - 3 minutes

```
Railway Dashboard → + New → GitHub Repo → fact-checkr
Name: factcheckr-beat
Root Directory: (leave empty)
Railway Config Path: backend/railway-beat.json

Add Variables (same as worker):
- DATABASE_URL
- REDIS_URL
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- PERPLEXITY_API_KEY

Deploy
```

### 6. Frontend (Vercel) - 5 minutes

```
Vercel Dashboard → Add New → Project → Import fact-checkr
Framework: Next.js (auto-detected)
Root Directory: frontend

Add Variable:
NEXT_PUBLIC_API_URL=<Railway backend URL>

Deploy
```

### 7. Update Backend CORS - 1 minute

```
Railway → factcheckr-backend → Variables → Add/Update:
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

### 8. Verify Everything Works

```bash
# Backend health
curl https://your-backend.railway.app/health

# Frontend
open https://your-app.vercel.app

# Check Railway logs
- Worker: Should show "celery@... ready"
- Beat: Should show "beat: Starting..."
```

## 📋 Environment Variables Quick Reference

### Backend/Worker/Beat (Railway)
```bash
DATABASE_URL=postgresql://...@...neon.tech/...
REDIS_URL=redis://...railway.app:...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

### Frontend (Vercel)
```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

## 🎯 What Each Service Does

- **Backend API**: Serves REST API endpoints
- **Worker**: Processes background tasks (scraping, fact-checking)
- **Beat**: Schedules periodic tasks (hourly scraping)
- **Redis**: Message broker for Celery tasks
- **Database**: Stores all data (Neon PostgreSQL)
- **Frontend**: Next.js app served via Vercel CDN

## 📚 Detailed Guides

- **Railway Deployment**: See `docs/RAILWAY_DEPLOYMENT.md`
- **Vercel Deployment**: See `docs/VERCEL_DEPLOYMENT.md`
- **Full Checklist**: See `docs/DEPLOYMENT_CHECKLIST.md`

## 🆘 Quick Troubleshooting

**Worker not starting?**
→ Check REDIS_URL is set correctly

**Frontend can't reach API?**
→ Verify NEXT_PUBLIC_API_URL and CORS_ORIGINS

**Tasks not running?**
→ Ensure Beat scheduler is deployed and running

**Database errors?**
→ Check DATABASE_URL and Neon dashboard

## 🔗 Service URLs

After deployment, you'll have:
- Backend: `https://factcheckr-backend-production.up.railway.app`
- Frontend: `https://factcheckr-mx.vercel.app`
- Database: Neon dashboard
- Redis: Railway dashboard

## ✅ Success Criteria

- [ ] Backend `/health` returns 200
- [ ] Frontend homepage loads
- [ ] Worker logs show task processing
- [ ] Beat logs show scheduled tasks
- [ ] API calls work from frontend

