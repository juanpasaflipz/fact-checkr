# Latest Changes Deployment Guide

## Overview

This document outlines what needs to be deployed and upgraded based on the latest changes in the codebase.

## 🔴 Critical: Database Migrations (MUST RUN FIRST)

### New Migrations to Apply

Three new database migrations need to be applied in order:

1. **`h8i9j0k1l2m3_add_market_tier_restrictions.py`**
   - Adds `created_by_user_id` to `markets` table
   - Creates `market_proposals` table
   - Creates `user_market_stats` table
   - Creates `market_notifications` table

2. **`i9j0k1l2m3n4_add_referral_system.py`**
   - Adds `referred_by_user_id` and `referral_code` to `users` table
   - Creates `referral_bonuses` table

3. **`j0k1l2m3n4o5_add_trending_intelligence.py`**
   - Creates `trending_topics` table
   - Creates `trending_topic_sources` association table
   - Creates `context_intelligence` table
   - Creates `topic_priority_queue` table
   - Adds `trending_topic_id` to `sources` table

### How to Apply Migrations

**For Railway (Production):**
```bash
# Option 1: Using deployment script
./scripts/deploy-production.sh railway

# Option 2: Manual Railway CLI
railway run --service backend sh -c "cd backend && alembic upgrade head"
```

**For Local Testing:**
```bash
cd backend
alembic upgrade head
```

**Verify Migrations:**
```bash
./scripts/deploy-production.sh verify
```

---

## 🔧 Backend Changes

### Modified Files (Need Redeployment)

1. **Docker Configuration**
   - `backend/Dockerfile` - Updated
   - `backend/Dockerfile.beat` - Updated
   - `backend/Dockerfile.worker` - Updated
   - `railway.json` - Updated startup command

2. **Core Backend**
   - `backend/main.py` - Router updates, Stripe validation
   - `backend/app/auth.py` - Authentication updates
   - `backend/app/models.py` - Model updates
   - `backend/app/database/models.py` - Database model changes
   - `backend/app/middleware.py` - Middleware updates
   - `backend/app/utils.py` - Utility updates
   - `backend/app/worker.py` - Worker updates

3. **Routers**
   - `backend/app/routers/auth.py` - Google OAuth implementation
   - `backend/app/routers/markets.py` - Market updates
   - `backend/app/routers/__init__.py` - Router registration

4. **Services & Agents**
   - `backend/app/agents/market_intelligence_agent.py` - Updates
   - `backend/app/services/market_seeding.py` - Updates
   - `backend/app/tasks/scraper.py` - Updates

### New Files (Need Deployment)

1. **New Routers**
   - `backend/app/routers/trending.py` - Trending topics API
   - `backend/app/routers/analytics.py` - Analytics API

2. **New Services**
   - `backend/app/services/trending_detector.py` - Trending detection
   - `backend/app/services/context_intelligence.py` - Context analysis
   - `backend/app/services/topic_prioritizer.py` - Topic prioritization
   - `backend/app/services/market_analytics.py` - Market analytics
   - `backend/app/services/ai_insights.py` - AI insights
   - `backend/app/services/export.py` - Data export

3. **New Tasks**
   - `backend/app/tasks/market_intelligence.py` - Market intelligence
   - `backend/app/tasks/market_notifications.py` - Notifications
   - `backend/app/tasks/credit_topup.py` - Credit top-ups

4. **Configuration**
   - `backend/config/` - New config directory structure

### Backend Deployment Steps

1. **Commit and Push Changes**
   ```bash
   git add .
   git commit -m "feat: add trending intelligence, referral system, and market tier restrictions"
   git push origin main
   ```

2. **Railway Auto-Deploy** (if enabled)
   - Railway will automatically detect the push and redeploy
   - Ensure all 3 services redeploy:
     - Backend (API)
     - Celery Beat (Scheduler)
     - Celery Worker (Task Executor)

3. **Manual Railway Deployment**
   - Go to Railway dashboard
   - Trigger redeploy for all 3 services
   - Monitor logs for errors

4. **Verify Backend Health**
   ```bash
   curl https://fact-checkr-production.up.railway.app/health
   ```

---

## 🎨 Frontend Changes

### Modified Files

1. **Core Pages**
   - `frontend/src/app/page.tsx` - Homepage updates
   - `frontend/src/app/signin/page.tsx` - Google OAuth integration
   - `frontend/src/app/signup/page.tsx` - Google OAuth integration
   - `frontend/src/app/markets/[id]/page.tsx` - Market page updates

2. **Components**
   - `frontend/src/components/Header.tsx` - Header updates

3. **Libraries**
   - `frontend/src/lib/auth.ts` - Google OAuth implementation
   - `frontend/src/lib/stripe.ts` - Stripe updates

4. **Dependencies**
   - `frontend/package.json` - Dependency updates
   - `frontend/package-lock.json` - Lock file updates

### New Files (Need Deployment)

1. **New Pages**
   - `frontend/src/app/admin/` - Admin pages
   - `frontend/src/app/analytics/` - Analytics pages
   - `frontend/src/app/markets/[id]/analytics/` - Market analytics
   - `frontend/src/app/markets/leaderboard/` - Leaderboard
   - `frontend/src/app/markets/propose/` - Market proposal
   - `frontend/src/app/notifications/` - Notifications

2. **New Components**
   - `frontend/src/components/Leaderboard.tsx`
   - `frontend/src/components/MarketAnalytics.tsx`
   - `frontend/src/components/MarketProposalForm.tsx`
   - `frontend/src/components/NotificationBell.tsx`
   - `frontend/src/components/TrendingTopics.tsx`
   - `frontend/src/components/charts/` - Chart components

### Frontend Deployment Steps

1. **Build Locally (Test First)**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Deploy to Vercel**
   - Push to GitHub (Vercel auto-deploys if connected)
   - Or manually trigger deployment in Vercel dashboard
   - Ensure root directory is set to `frontend`

3. **Verify Frontend**
   - Visit deployed URL
   - Check browser console for errors
   - Test Google OAuth login
   - Test API connections

---

## 🔐 Environment Variables

### Backend (Railway) - Required Updates

Verify these are set in Railway for all services (Backend, Celery Beat, Celery Worker):

#### Google OAuth (NEW - Required)
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-client-secret
GOOGLE_REDIRECT_URI=https://fact-checkr-production.up.railway.app/api/auth/google/callback
FRONTEND_URL=https://www.factcheck.mx  # or your frontend URL
```

#### Existing Variables (Verify Still Set)
```bash
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
JWT_SECRET_KEY=...
ANTHROPIC_API_KEY=...  # or OPENAI_API_KEY
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...  # Webhook endpoint: https://abstrak.to/api/payments/stripe/webhook
YOUTUBE_API_KEY=...
```

#### CORS Configuration
```bash
CORS_ORIGINS=https://factcheck.mx,https://www.factcheck.mx,http://localhost:3000
```

### Frontend (Vercel) - Required Updates

Verify these are set in Vercel:

```bash
NEXT_PUBLIC_API_URL=https://fact-checkr-production.up.railway.app
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...  # or pk_test_... for staging
```

---

## ✅ Pre-Deployment Checklist

### Database
- [ ] All 3 new migrations committed to repository
- [ ] Run migrations on production database
- [ ] Verify all new tables created successfully
- [ ] Check foreign key constraints are valid

### Backend
- [ ] All code changes committed
- [ ] Dockerfiles updated and tested
- [ ] Environment variables set in Railway
- [ ] Google OAuth credentials configured
- [ ] All 3 Railway services configured (Backend, Beat, Worker)
- [ ] Health check endpoint working

### Frontend
- [ ] All code changes committed
- [ ] Dependencies installed (`npm install`)
- [ ] Build succeeds locally (`npm run build`)
- [ ] Environment variables set in Vercel
- [ ] Google OAuth redirect URI matches backend

### Testing
- [ ] Test Google OAuth login flow
- [ ] Test market creation (Pro users)
- [ ] Test referral system
- [ ] Test trending topics
- [ ] Test analytics endpoints
- [ ] Verify Stripe integration still works

---

## 🚀 Deployment Order

### Automated Deployment (Recommended)

Use the comprehensive deployment script:

```bash
# Full automated deployment
./scripts/deploy.sh

# Or verify-only mode
./scripts/deploy.sh --verify-only

# Skip specific steps if needed
./scripts/deploy.sh --skip-migrations
./scripts/deploy.sh --skip-backend
./scripts/deploy.sh --skip-frontend
```

**See:** [Deployment Script Guide](./DEPLOYMENT_SCRIPT_GUIDE.md) for detailed usage.

### Manual Deployment Steps

1. **Database Migrations** (CRITICAL - Do First)
   ```bash
   ./scripts/deploy-production.sh railway
   ```

2. **Backend Deployment**
   - Push code to trigger Railway auto-deploy
   - Or manually redeploy in Railway dashboard
   - Monitor logs for errors

3. **Frontend Deployment**
   - Push code to trigger Vercel auto-deploy
   - Or manually deploy in Vercel dashboard
   - Verify build succeeds

4. **Verification**
   ```bash
   # Verify backend
   curl https://fact-checkr-production.up.railway.app/health
   
   # Verify migrations
   ./scripts/deploy-production.sh verify
   
   # Test frontend
   # Visit deployed URL and test features
   ```

---

## 🐛 Troubleshooting

### Migration Fails
- Check `DATABASE_URL` is correct
- Verify database user has CREATE TABLE permissions
- Check migration logs in Railway

### Google OAuth Not Working
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set
- Check redirect URI matches exactly (no trailing slashes)
- Verify redirect URI is added in Google Cloud Console
- Check CORS configuration includes frontend URL

### Frontend Build Fails
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify all dependencies in `package.json` are compatible
- Check build logs in Vercel dashboard

### Services Not Starting
- Check Railway logs for each service
- Verify environment variables are set for all services
- Check Redis connection (required for Celery)

---

## 📝 Post-Deployment

After successful deployment:

1. **Monitor Logs**
   ```bash
   railway logs --service backend
   railway logs --service celery-beat
   railway logs --service celery-worker
   ```

2. **Test Critical Features**
   - User registration/login (including Google OAuth)
   - Market creation (Pro tier)
   - Referral system
   - Trending topics
   - Analytics

3. **Check Database**
   - Verify all new tables exist
   - Check indexes are created
   - Verify foreign keys are valid

4. **Performance Monitoring**
   - Monitor API response times
   - Check Celery task execution
   - Monitor database query performance

---

## 📚 Related Documentation

- [Production Deployment Script Guide](./PRODUCTION_DEPLOYMENT_SCRIPT.md)
- [Google OAuth Quick Checklist](../setup/GOOGLE_AUTH_QUICK_CHECKLIST.md)
- [Environment Variables Setup](../setup/environment.md)
- [Railway Deployment Guide](./RAILWAY_DEPLOYMENT.md)
- [Vercel Deployment Guide](./VERCEL_DEPLOYMENT.md)

