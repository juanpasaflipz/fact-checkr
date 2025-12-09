# Railway Configuration Guide

This guide ensures all Railway services are configured correctly for the FactCheckr application.

## Railway Service Setup

### Backend Service (Main API)

**Railway Dashboard Settings:**
1. **Root Directory**: Set to `backend`
2. **Dockerfile Path**: `Dockerfile` (auto-detected when Root Directory is set)
3. **Start Command**: `sh /app/scripts/start.sh`
4. **Health Check Path**: `/health`

**Configuration File**: Uses `railway.toml` at repo root OR `backend/railway.json`

**Build Context**: When Root Directory is set to `backend`, Railway uses `backend/` as the build context, so Dockerfiles reference files directly (e.g., `COPY requirements.txt .` not `COPY backend/requirements.txt .`)

---

### Worker Service (Celery Worker)

**Railway Dashboard Settings:**
1. **Root Directory**: Set to `backend`
2. **Dockerfile Path**: `Dockerfile.worker`
3. **Start Command**: `sh /app/scripts/start-worker.sh`
4. **Restart Policy**: `ON_FAILURE`

**Configuration File**: `backend/config/railway-worker.json`

**Note**: Make sure Root Directory is set to `backend` in Railway dashboard, not the repo root.

---

### Beat Service (Celery Beat Scheduler)

**Railway Dashboard Settings:**
1. **Root Directory**: Set to `backend`
2. **Dockerfile Path**: `Dockerfile.beat`
3. **Start Command**: `sh /app/scripts/start-beat.sh`
4. **Restart Policy**: `ON_FAILURE`

**Configuration File**: `backend/config/railway-beat.json`

---

## Important: Root Directory Configuration

**CRITICAL**: All Railway services (backend, worker, beat) must have their **Root Directory** set to `backend` in the Railway dashboard.

### How to Set Root Directory:

1. Go to Railway dashboard
2. Select your service
3. Go to **Settings** tab
4. Find **Root Directory** setting
5. Set it to: `backend`
6. Save changes

### Why This Matters:

- When Root Directory is `backend`, Railway uses `backend/` as the build context
- Dockerfiles can then reference files directly: `COPY requirements.txt .`
- If Root Directory is not set (or set to repo root), Dockerfiles would need: `COPY backend/requirements.txt .`

---

## Verification Checklist

- [ ] Backend service has Root Directory = `backend`
- [ ] Worker service has Root Directory = `backend`
- [ ] Beat service has Root Directory = `backend` (if using)
- [ ] All services can build successfully
- [ ] Backend health check responds at `/health`
- [ ] Worker processes tasks correctly
- [ ] Beat schedules tasks correctly

---

## Troubleshooting

### Build Error: "requirements.txt not found"

**Problem**: Dockerfile can't find `requirements.txt`

**Solution**: 
1. Verify Root Directory is set to `backend` in Railway dashboard
2. Check that `backend/requirements.txt` exists in your repo
3. Ensure `.dockerignore` is not excluding `requirements.txt`

### Build Error: "/backend not found"

**Problem**: Dockerfile tries to copy from `backend/` but can't find it

**Solution**:
1. Set Root Directory to `backend` in Railway dashboard
2. Update Dockerfile to use direct paths (e.g., `COPY requirements.txt .` not `COPY backend/requirements.txt .`)

### Service Builds But Doesn't Start

**Problem**: Build succeeds but service crashes on startup

**Solution**:
1. Check Start Command is correct: `sh /app/scripts/start.sh`
2. Verify all environment variables are set
3. Check service logs in Railway dashboard
4. Ensure database connection string is valid

---

## Current Configuration Summary

✅ **Backend Dockerfile**: Uses direct paths (assumes Root Directory = `backend`)
✅ **Worker Dockerfile**: Uses direct paths (assumes Root Directory = `backend`)
✅ **Beat Dockerfile**: Uses direct paths (assumes Root Directory = `backend`)
✅ **Railway Configs**: All point to correct Dockerfile paths

**Action Required**: Verify Root Directory is set to `backend` for all services in Railway dashboard.
