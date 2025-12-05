# Production Deployment Script Guide

Automated deployment script for FactCheckr premium features.

## Quick Start

### For Railway Deployment

**Important:** If your environment variables are already set in Railway, you don't need to set them locally. Railway CLI automatically uses Railway's environment variables.

```bash
# 1. Make sure you're logged into Railway
railway login

# 2. Link to your project (if not already linked)
railway link

# 3. Run deployment script - it uses Railway's environment automatically
./scripts/deploy-production.sh railway
```

**Note:** The script uses Railway's environment variables automatically. You only need to set local variables if you want to test connections locally before deploying.

### For Local/Manual Deployment

```bash
# 1. Set environment variables
export DATABASE_URL="your-database-url"
export REDIS_URL="your-redis-url"
export JWT_SECRET_KEY="your-secret-key"

# 2. Run deployment script
./scripts/deploy-production.sh local
```

### Verify Deployment

```bash
# Check if all premium features are deployed
./scripts/deploy-production.sh verify
```

## What the Script Does

### 1. **Requirements Check**
   - Verifies Python 3 is installed
   - Checks Alembic is available
   - Optionally checks Railway CLI

### 2. **Environment Variables**
   - Validates required variables (`DATABASE_URL`, `JWT_SECRET_KEY`)
   - Warns about missing optional variables (`REDIS_URL`, API keys)
   - Masks sensitive data in output

### 3. **Connection Tests**
   - Tests PostgreSQL connection
   - Tests Redis connection (if configured)

### 4. **Database Migrations**
   - Runs `alembic upgrade head`
   - Verifies new tables are created:
     - `market_proposals`
     - `user_market_stats`
     - `market_notifications`
     - `referral_bonuses`
   - Checks new columns in `users` table

### 5. **Service Verification**
   - Checks Railway configuration files exist
   - Verifies all 3 services are configured:
     - Main Backend (API)
     - Celery Beat (Scheduler)
     - Celery Worker (Task Executor)

## Commands

### `railway` - Deploy to Railway
- Requires Railway CLI installed and logged in
- Runs migrations on Railway production database
- Provides next steps for deployment

### `local` - Local Deployment Preparation
- Prepares environment for local deployment
- Runs all checks and migrations
- Provides commands to start services locally

### `verify` - Verify Deployment
- Checks if all premium feature tables exist
- Verifies new columns are added
- Reports deployment status

## Required Environment Variables

### For Railway Deployment
**You don't need to set these locally!** Railway CLI automatically uses the environment variables you've already configured in your Railway project dashboard.

The script will:
- Use Railway's `DATABASE_URL` automatically
- Use Railway's `REDIS_URL` automatically  
- Use all other Railway environment variables

### For Local Testing
If you want to test locally before deploying, you can set these locally:

### Required
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret key for JWT tokens

### Recommended
- `REDIS_URL` - Redis connection (required for Celery)
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` - AI service keys
- `STRIPE_SECRET_KEY` - For subscription management

## Railway Deployment Steps

1. **Verify Environment Variables in Railway** (if already set, skip this)
   - Go to your Railway project dashboard
   - Check that all required environment variables are set for each service:
     - Backend service
     - Celery Beat service  
     - Celery Worker service
   - If missing, add them in Railway dashboard (not locally)

2. **Run Migrations Using Railway's Environment**
   ```bash
   # The script automatically uses Railway's environment variables
   ./scripts/deploy-production.sh railway
   ```
   
   Or manually:
   ```bash
   # Railway CLI automatically uses Railway's DATABASE_URL
   railway run --service backend alembic upgrade head
   ```
   
   **No need to export variables locally!** Railway CLI uses your Railway project's environment automatically.

3. **Deploy Services**
   - Push code to GitHub (if using auto-deploy)
   - Or manually trigger deployment in Railway dashboard
   - Ensure all 3 services are running:
     - Backend (API server)
     - Celery Beat (scheduler)
     - Celery Worker (task executor)

4. **Verify Deployment**
   ```bash
   ./scripts/deploy-production.sh verify
   ```

## Troubleshooting

### Migration Fails
- Check `DATABASE_URL` is correct
- Verify database is accessible
- Check database user has CREATE TABLE permissions

### Redis Connection Fails
- Celery won't work without Redis
- Verify `REDIS_URL` is set correctly
- Check Redis service is running

### Tables Missing After Migration
- Run `./scripts/deploy-production.sh verify` to check
- Re-run migrations: `alembic upgrade head`
- Check migration logs for errors

### Railway CLI Not Found
- Install: `npm i -g @railway/cli`
- Login: `railway login`
- Or deploy manually via Railway dashboard

## Post-Deployment Checklist

- [ ] All migrations applied successfully
- [ ] All premium feature tables exist
- [ ] Backend service is running
- [ ] Celery Beat service is running
- [ ] Celery Worker service is running
- [ ] Health check endpoint responds: `GET /health`
- [ ] Test premium feature (e.g., create market as Pro user)

## Next Steps After Deployment

1. **Monitor Logs**
   ```bash
   # Railway
   railway logs --service backend
   railway logs --service celery-beat
   railway logs --service celery-worker
   ```

2. **Test Premium Features**
   - Create a Pro user account
   - Test market creation
   - Test market proposals
   - Verify monthly credit top-ups (on 1st of month)

3. **Set Up Monitoring**
   - Monitor error rates
   - Track conversion metrics
   - Set up alerts for failed tasks

