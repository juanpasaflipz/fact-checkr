# Railway Deployment Guide

## Overview
The FactCheckr application consists of 4 Railway services:
1. **Backend API** - FastAPI server
2. **Celery Worker** - Background task processor
3. **Celery Beat** - Task scheduler
4. **Redis** - Message broker and result backend

## Prerequisites
- Railway account
- GitHub repository connected to Railway
- Neon PostgreSQL database (already set up)

## Step 1: Deploy Redis

1. In Railway dashboard, click **+ New**
2. Select **Database** → **Redis**
3. Name it: `factcheckr-redis`
4. Railway will automatically provision Redis and provide `REDIS_URL`

## Step 2: Deploy Backend API

1. In Railway dashboard, click **+ New**
2. Select **GitHub Repo** → Choose `fact-checkr`
3. Name it: `factcheckr-backend`
4. Configure:
   - **Root Directory**: Leave empty (monorepo root)
   - **Railway Config Path**: `backend/railway.json`
5. Add environment variables:
   ```
   DATABASE_URL=<from Neon>
   REDIS_URL=<from Redis service>
   OPENAI_API_KEY=<your key>
   ANTHROPIC_API_KEY=<your key>
   PERPLEXITY_API_KEY=<your key>
   FRONTEND_URL=<will add after Vercel deploy>
   ```
6. Deploy

## Step 3: Deploy Celery Worker

1. In Railway dashboard, click **+ New**
2. Select **GitHub Repo** → Choose `fact-checkr`
3. Name it: `factcheckr-worker`
4. Configure:
   - **Root Directory**: Leave empty
   - **Railway Config Path**: `backend/railway-worker.json`
5. Add same environment variables as backend (copy from backend service)
6. Deploy

## Step 4: Deploy Celery Beat (Scheduler)

1. In Railway dashboard, click **+ New**
2. Select **GitHub Repo** → Choose `fact-checkr`
3. Name it: `factcheckr-beat`
4. Configure:
   - **Root Directory**: Leave empty
   - **Railway Config Path**: `backend/railway-beat.json`
5. Add same environment variables as backend
6. Deploy

## Step 5: Verify Deployment

Check logs for each service:

### Backend API
```
✅ App module imported successfully
Starting gunicorn...
```

### Worker
```
✅ Redis connection successful
✅ Worker module imported successfully
[INFO] celery@... ready
```

### Beat
```
✅ Redis connection successful
✅ Worker module imported successfully
[INFO] beat: Starting...
```

## Environment Variables Reference

### Required for all services:
- `DATABASE_URL` - Neon PostgreSQL connection string
- `REDIS_URL` - Railway Redis connection string
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `PERPLEXITY_API_KEY` - Perplexity API key

### Backend API only:
- `FRONTEND_URL` - Vercel frontend URL (for CORS)

## Monitoring

- Backend API: Check `/health` endpoint
- Worker: Monitor task execution in logs
- Beat: Check scheduled task triggers in logs
- Redis: Monitor connection count and memory usage

## Troubleshooting

### Backend fails to start
- Verify `DATABASE_URL` is correct
- Check Neon database is accessible
- Review logs for import errors

### Worker can't connect to Redis
- Verify `REDIS_URL` is set correctly
- Ensure Redis service is running
- Check network connectivity

### Tasks not executing
- Verify worker is running
- Check beat scheduler is running
- Review task logs for errors

## Scaling

- **Backend**: Increase instances for more API capacity
- **Worker**: Add more worker instances for parallel task processing
- **Beat**: Only run 1 instance (scheduler should be singleton)
- **Redis**: Upgrade plan for more memory/connections

