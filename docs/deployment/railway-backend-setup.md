# Railway Backend Deployment - Fresh Start Guide

This guide walks through deploying the FactCheckr backend to Railway from scratch.

## Prerequisites

- Railway account (sign up at railway.app)
- GitHub repository connected to Railway
- Neon PostgreSQL database URL
- Redis instance (Railway or external)

## Step 1: Railway Project Setup

1. **Create New Project in Railway**
   - Go to railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `fact-checkr` repository

2. **Create Services**
   - **Backend Service**: From the repo root
   - **Redis Service** (optional): Add from Railway's template or use external Redis

## Step 2: Configure Backend Service

### A. Source Configuration

1. Go to your backend service
2. **Settings → Source**
   - Root Directory: `backend` (if deploying from monorepo)
   - OR leave empty if using `backend/Dockerfile` path in `railway.json`

### B. Build Configuration

1. **Settings → Build**
   - Build Command: Leave empty (uses Dockerfile)
   - Dockerfile Path: Should auto-detect, or set to `backend/Dockerfile`

2. Verify `backend/railway.json` exists with:
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "DOCKERFILE",
       "dockerfilePath": "backend/Dockerfile",
       "watchPatterns": ["backend/**"]
     },
     "deploy": {
       "startCommand": "sh /app/start.sh",
       "healthcheckPath": "/health",
       "healthcheckTimeout": 300
     }
   }
   ```

### C. Deploy Settings

1. **Settings → Deploy**
   - Pre-deploy Command: **Leave empty** (migrations run in start.sh)
   - Custom Start Command: `sh /app/start.sh` (should read from railway.json)
   - Healthcheck Path: `/health`
   - Healthcheck Timeout: `300` seconds

### D. Networking

1. **Settings → Networking**
   - **IMPORTANT**: Do NOT manually set a port
   - Railway automatically sets `$PORT` environment variable
   - Your app should listen on `0.0.0.0:${PORT}`
   - Enable "Generate Domain" to get public URL

## Step 3: Environment Variables

Go to **Variables** tab and add:

### Required Variables

```bash
# Database (from Neon)
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# Redis (if using Railway Redis service, use the shared variable)
REDIS_URL=${{redis.REDIS_URL}}
# OR if external Redis:
# REDIS_URL=redis://default:password@host:6379

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
# ... other API keys
```

### Optional Variables

```bash
# CORS Origins (comma-separated)
CORS_ORIGINS=https://factcheck.mx,https://www.factcheck.mx

# Port (Railway sets this automatically, don't override)
# PORT=<Railway sets this>
```

## Step 4: Verify Files

Ensure these files exist in your repo:

```
backend/
├── Dockerfile          # Docker build configuration
├── start.sh            # Startup script (executable)
├── main.py             # FastAPI app entry point
├── railway.json        # Railway configuration
├── requirements.txt    # Python dependencies
└── alembic/            # Database migrations
```

## Step 5: Deployment

1. **Trigger Deployment**
   - Push to `main` branch, OR
   - Go to Deployments → "Redeploy"

2. **Monitor Build**
   - Watch build logs
   - Should see: "Build time: X seconds"

3. **Watch Startup Logs**
   - After build, watch runtime logs
   - Look for:
     ```
     🚀 Starting FactCheckr Backend
     Listening on port: <port>
     Starting Gunicorn...
     ```

4. **Health Check**
   - Railway will check `/health` endpoint
   - Should see "Attempt #1" succeed after ~10-30 seconds

## Step 6: Troubleshooting

### No Startup Logs Visible

- Check **Logs** tab (not Deployments tab)
- Verify start command: `sh /app/start.sh`
- Check that `start.sh` is executable (has `chmod +x`)

### Health Check Fails

1. **Check Runtime Logs**
   - Look for Python import errors
   - Check database connection errors
   - Verify `$PORT` is set correctly

2. **Manual Health Check**
   - Get public domain from Networking
   - Visit: `https://your-service.up.railway.app/health`
   - Should return: `{"status":"healthy","message":"API is operational"}`

3. **Common Issues**
   - Missing `DATABASE_URL` → Add in Variables
   - Port mismatch → Don't set PORT manually, let Railway handle it
   - Import errors → Check requirements.txt installed correctly
   - Migration failures → Check DATABASE_URL is valid

### App Crashes on Start

1. Check logs for:
   - Import errors
   - Missing environment variables
   - Database connection failures

2. Test locally:
   ```bash
   cd backend
   export PORT=8000
   export DATABASE_URL=your_db_url
   sh start.sh
   ```

## Step 7: Connect Frontend

Once backend is running:

1. Get backend URL: **Networking → Public Domain**
   - Example: `https://fact-checkr-production.up.railway.app`

2. Update frontend environment:
   - Vercel: Add `NEXT_PUBLIC_API_URL=https://your-backend-url`
   - Or update `frontend/.env.local` for local dev

## Verification Checklist

- [ ] Build completes successfully
- [ ] Runtime logs show "Starting Gunicorn..."
- [ ] Health check passes (`/health` returns 200)
- [ ] Public domain accessible
- [ ] `curl https://your-domain/health` works
- [ ] Database migrations ran (check logs)
- [ ] Environment variables set correctly

## Quick Reference

**Service URL**: Railway Dashboard → Service → Networking → Public Domain
**Logs**: Railway Dashboard → Service → Logs tab
**Variables**: Railway Dashboard → Service → Variables tab
**Health Check**: `https://your-domain/health`

