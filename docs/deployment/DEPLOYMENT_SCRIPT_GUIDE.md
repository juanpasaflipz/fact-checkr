# Deployment Script Guide

Automated deployment script for FactCheckr MX that handles the complete deployment process.

## Quick Start

```bash
# Full deployment (migrations + backend + frontend)
./scripts/deploy.sh

# Verify-only mode (check status without deploying)
./scripts/deploy.sh --verify-only

# Skip specific steps
./scripts/deploy.sh --skip-migrations
./scripts/deploy.sh --skip-backend
./scripts/deploy.sh --skip-frontend
```

## Usage

### Basic Deployment

```bash
./scripts/deploy.sh
```

This will:
1. ✅ Check prerequisites (Git, Python, Node, Railway CLI, Vercel CLI)
2. ✅ Verify git status and branch
3. ✅ Check Railway and Vercel connections
4. ✅ Run database migrations
5. ✅ Deploy backend to Railway
6. ✅ Deploy frontend to Vercel
7. ✅ Verify deployment status

### Options

| Option | Description |
|--------|-------------|
| `--skip-migrations` | Skip database migration step |
| `--skip-backend` | Skip backend deployment to Railway |
| `--skip-frontend` | Skip frontend deployment to Vercel |
| `--verify-only` | Only verify deployment status, don't deploy |

### Examples

```bash
# Deploy only backend (skip frontend)
./scripts/deploy.sh --skip-frontend

# Deploy only frontend (skip backend and migrations)
./scripts/deploy.sh --skip-backend --skip-migrations

# Verify current deployment status
./scripts/deploy.sh --verify-only

# Deploy after migrations are already run
./scripts/deploy.sh --skip-migrations
```

## Prerequisites

The script checks for and requires:

### Required
- **Git** - Version control
- **Python 3** - For backend and migrations
- **Node.js** - For frontend (if deploying frontend)

### Optional (but recommended)
- **Railway CLI** - For backend deployment
  ```bash
  npm i -g @railway/cli
  railway login
  ```
- **Vercel CLI** - For frontend deployment
  ```bash
  npm i -g vercel
  vercel login
  ```
- **Alembic** - For database migrations
  ```bash
  pip install alembic
  ```

## What the Script Does

### 1. Prerequisites Check
- Verifies all required tools are installed
- Checks Railway and Vercel CLI availability
- Validates git repository status

### 2. Git Status Check
- Verifies you're in a git repository
- Checks for uncommitted changes
- Shows current branch
- Warns if not on main/master branch

### 3. Platform Connections
- **Railway**: Checks login status and project linkage
- **Vercel**: Checks login status

### 4. Database Migrations
- Runs `alembic upgrade head` via Railway CLI
- Verifies migrations completed successfully
- Can be skipped with `--skip-migrations`

### 5. Backend Deployment
- Checks if code is pushed to GitHub
- Triggers Railway auto-deploy (if code is pushed)
- Provides manual deployment instructions if needed
- Verifies Railway service configuration

### 6. Frontend Deployment
- Tests frontend build locally
- Checks Vercel project linkage
- Deploys to Vercel production
- Can trigger auto-deploy via GitHub push

### 7. Verification
- Backend health check: `GET /health`
- Frontend deployment status
- Database migration verification

## Interactive Prompts

The script will ask for confirmation in certain situations:

1. **Uncommitted changes**: Asks if you want to continue
2. **Push to GitHub**: Asks if you want to push code for auto-deploy
3. **Vercel link**: Asks if you want to link Vercel project
4. **Vercel deployment**: Asks if you want to deploy to production

## Deployment Flow

```
┌─────────────────────────────────────┐
│  1. Check Prerequisites             │
│     - Git, Python, Node, CLIs      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  2. Check Git Status                │
│     - Uncommitted changes?          │
│     - Current branch                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  3. Check Platform Connections      │
│     - Railway login?                │
│     - Vercel login?                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  4. Run Database Migrations         │
│     - Via Railway CLI               │
│     - Verify success                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  5. Deploy Backend (Railway)        │
│     - Push to GitHub?               │
│     - Auto-deploy or manual        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  6. Deploy Frontend (Vercel)         │
│     - Test build                    │
│     - Deploy to production         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  7. Verify Deployment               │
│     - Backend health check          │
│     - Migration verification        │
└─────────────────────────────────────┘
```

## Troubleshooting

### "Railway CLI not found"
```bash
npm i -g @railway/cli
railway login
railway link  # Link to your project
```

### "Vercel CLI not found"
```bash
npm i -g vercel
vercel login
cd frontend
vercel link  # Link to your project
```

### "Not logged in to Railway"
```bash
railway login
```

### "Not logged in to Vercel"
```bash
vercel login
```

### "Migration failed"
- Check `DATABASE_URL` is set correctly in Railway
- Verify database user has CREATE TABLE permissions
- Check Railway logs: `railway logs --service backend`

### "Frontend build failed"
- Check `NEXT_PUBLIC_API_URL` is set in Vercel
- Verify all dependencies: `cd frontend && npm install`
- Check build errors: `cd frontend && npm run build`

### "Git push failed"
- Check you have write access to the repository
- Verify remote is configured: `git remote -v`
- Push manually: `git push origin main`

## Manual Deployment Steps

If the script can't automate certain steps, here are manual alternatives:

### Manual Backend Deployment

1. **Push to GitHub** (if auto-deploy enabled):
   ```bash
   git push origin main
   ```

2. **Or deploy via Railway Dashboard**:
   - Go to https://railway.app
   - Select your project
   - Click "Deploy" or trigger redeploy

3. **Or via Railway CLI**:
   ```bash
   railway up
   ```

### Manual Frontend Deployment

1. **Push to GitHub** (if auto-deploy enabled):
   ```bash
   git push origin main
   ```

2. **Or deploy via Vercel Dashboard**:
   - Go to https://vercel.com
   - Select your project
   - Click "Deploy"

3. **Or via Vercel CLI**:
   ```bash
   cd frontend
   vercel --prod
   ```

### Manual Migrations

```bash
# Via Railway CLI
railway run --service backend sh -c "cd backend && alembic upgrade head"

# Or use the migration script
./scripts/deploy-production.sh railway
```

## Best Practices

1. **Always run migrations first** (unless using `--skip-migrations`)
2. **Commit and push changes** before deploying
3. **Test locally** before deploying:
   ```bash
   # Backend
   cd backend && python -m uvicorn main:app --reload
   
   # Frontend
   cd frontend && npm run dev
   ```
4. **Verify deployment** after completion
5. **Monitor logs** during and after deployment:
   ```bash
   railway logs --service backend
   ```

## Post-Deployment Checklist

After successful deployment:

- [ ] Backend health check passes: `curl https://fact-checkr-production.up.railway.app/health`
- [ ] Frontend loads without errors
- [ ] Database migrations verified: `./scripts/deploy-production.sh verify`
- [ ] Test Google OAuth login
- [ ] Test Stripe checkout
- [ ] Test new features (trending topics, analytics, etc.)
- [ ] Monitor Railway logs for errors
- [ ] Check Vercel build logs

## Related Documentation

- [Latest Changes Deployment Guide](./LATEST_CHANGES_DEPLOYMENT.md)
- [Missing Environment Variables](./MISSING_ENV_VARIABLES.md)
- [Production Deployment Script](./PRODUCTION_DEPLOYMENT_SCRIPT.md)
- [Stripe Webhook Endpoint](./STRIPE_WEBHOOK_ENDPOINT.md)

