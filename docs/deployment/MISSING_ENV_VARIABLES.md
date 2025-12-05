# Missing Environment Variables Report

Generated: $(date)

## Summary

This report identifies missing environment variables by comparing:
- Variables currently set in local `.env` files
- Variables required by the codebase
- Variables documented as needed for latest features

---

## 🔴 Backend - Missing Critical Variables

### Required for Production

| Variable | Status | Priority | Notes |
|----------|--------|----------|-------|
| `REDIS_URL` | ⚠️ Missing | **CRITICAL** | Required for Celery tasks. Has default but should be explicit in production |
| `STRIPE_WEBHOOK_SECRET` | ❌ Missing | **CRITICAL** | Required for Stripe subscription webhooks. Format: `whsec_...` |
| `ENVIRONMENT` | ⚠️ Missing | Recommended | Should be `production` in production, `development` locally |

### Currently Set (✅)

- ✅ `DATABASE_URL` - PostgreSQL connection
- ✅ `JWT_SECRET_KEY` - Authentication
- ✅ `ANTHROPIC_API_KEY` - AI service (primary)
- ✅ `OPENAI_API_KEY` - AI service (backup)
- ✅ `SERPER_API_KEY` - Web search
- ✅ `YOUTUBE_API_KEY` - YouTube integration
- ✅ `GOOGLE_CLIENT_ID` - Google OAuth (NEW)
- ✅ `GOOGLE_CLIENT_SECRET` - Google OAuth (NEW)
- ✅ `GOOGLE_REDIRECT_URI` - Google OAuth (NEW)
- ✅ `FRONTEND_URL` - Frontend URL
- ✅ `CORS_ORIGINS` - CORS configuration
- ✅ `STRIPE_SECRET_KEY` - Stripe API key
- ✅ `STRIPE_PRO_MONTHLY_PRICE_ID` - Stripe pricing
- ✅ `STRIPE_PRO_YEARLY_PRICE_ID` - Stripe pricing
- ✅ `STRIPE_TEAM_MONTHLY_PRICE_ID` - Stripe pricing
- ✅ `STRIPE_TEAM_YEARLY_PRICE_ID` - Stripe pricing
- ✅ Twitter API credentials (all 5 variables)

### Issues Found

1. **Duplicate `FRONTEND_URL`** - Appears twice in `.env` file (should be cleaned up)
2. **Legacy variables** - `NEXTAUTH_URL`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET` (may be unused)
3. **`STRIPE_PUBLISHABLE_KEY`** - This should be in frontend, not backend

---

## 🔴 Frontend - Missing Critical Variables

### Required for Production

| Variable | Status | Priority | Notes |
|----------|--------|----------|-------|
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | ❌ Missing | **CRITICAL** | Required for Stripe checkout. Format: `pk_test_...` or `pk_live_...` |

### Currently Set (✅)

- ✅ `NEXT_PUBLIC_API_URL` - Backend API URL

---

## 📋 Complete Environment Variable Checklist

### Backend (Railway Production)

#### Database & Infrastructure
```bash
DATABASE_URL=postgresql://...          # ✅ Set
REDIS_URL=redis://...                  # ❌ MISSING - Required for Celery
```

#### Authentication
```bash
JWT_SECRET_KEY=...                     # ✅ Set
GOOGLE_CLIENT_ID=...                   # ✅ Set (NEW)
GOOGLE_CLIENT_SECRET=...               # ✅ Set (NEW)
GOOGLE_REDIRECT_URI=...                # ✅ Set (NEW)
```

#### AI Services
```bash
ANTHROPIC_API_KEY=...                  # ✅ Set
OPENAI_API_KEY=...                     # ✅ Set
SERPER_API_KEY=...                     # ✅ Set
```

#### Stripe (Payment Processing)
```bash
STRIPE_SECRET_KEY=...                   # ✅ Set
STRIPE_WEBHOOK_SECRET=...              # ❌ MISSING - Required for webhooks
STRIPE_PRO_MONTHLY_PRICE_ID=...        # ✅ Set
STRIPE_PRO_YEARLY_PRICE_ID=...         # ✅ Set
STRIPE_TEAM_MONTHLY_PRICE_ID=...       # ✅ Set
STRIPE_TEAM_YEARLY_PRICE_ID=...        # ✅ Set
```

#### Frontend Configuration
```bash
FRONTEND_URL=...                       # ✅ Set
CORS_ORIGINS=...                        # ✅ Set
```

#### Other Services
```bash
YOUTUBE_API_KEY=...                    # ✅ Set
TWITTER_API_KEY=...                    # ✅ Set
TWITTER_API_SECRET=...                  # ✅ Set
TWITTER_ACCESS_TOKEN=...                # ✅ Set
TWITTER_ACCESS_SECRET=...               # ✅ Set
TWITTER_BEARER_TOKEN=...                # ✅ Set
```

#### Environment
```bash
ENVIRONMENT=production                  # ⚠️ MISSING - Should be set to 'production'
```

### Frontend (Vercel Production)

#### API Configuration
```bash
NEXT_PUBLIC_API_URL=...                 # ✅ Set
```

#### Stripe
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=...  # ❌ MISSING - Required for checkout
```

---

## 🚨 Action Items

### Immediate (Before Deployment)

1. **Add `REDIS_URL` to backend**
   ```bash
   # In Railway, add:
   REDIS_URL=redis://your-redis-host:6379/0
   ```

2. **Add `STRIPE_WEBHOOK_SECRET` to backend**
   ```bash
   # Get from Stripe Dashboard > Developers > Webhooks
   # Webhook endpoint URL: https://abstrak.to/api/payments/stripe/webhook
   # Format: whsec_...
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
   ```

3. **Add `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` to frontend**
   ```bash
   # In Vercel, add:
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...  # or pk_test_... for staging
   ```

4. **Set `ENVIRONMENT` in backend**
   ```bash
   # In Railway, add:
   ENVIRONMENT=production
   ```

### Recommended (For Better Configuration)

5. **Clean up backend `.env`**
   - Remove duplicate `FRONTEND_URL`
   - Remove `STRIPE_PUBLISHABLE_KEY` (should be in frontend only)
   - Remove legacy variables if unused: `NEXTAUTH_URL`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`

---

## 📝 Railway Environment Variables Setup

### For Backend Service

Add these in Railway Dashboard → Your Project → Backend Service → Variables:

```bash
# Missing Critical Variables
REDIS_URL=redis://your-redis-host:6379/0
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
ENVIRONMENT=production
```

### For Celery Beat Service

Same variables as backend (all services need same env vars).

### For Celery Worker Service

Same variables as backend (all services need same env vars).

---

## 📝 Vercel Environment Variables Setup

### For Frontend

Add in Vercel Dashboard → Your Project → Settings → Environment Variables:

```bash
# Missing Critical Variable
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_your_publishable_key_here
```

**Important:** 
- Use `pk_test_...` for preview/staging deployments
- Use `pk_live_...` for production
- Set for Production, Preview, and Development environments

---

## 🔍 How to Verify

### Backend (Railway)

1. Check Railway logs for startup validation:
   ```bash
   railway logs --service backend
   ```
   Look for:
   - ✅ Stripe configuration validation
   - ⚠️ Warnings about missing variables

2. Test Stripe webhook endpoint:
   ```bash
   # Production webhook URL: https://abstrak.to/api/payments/stripe/webhook
   curl https://abstrak.to/api/payments/stripe/webhook
   # Should not return "webhook secret missing" error
   ```

3. Test Celery connection:
   - Check Railway logs for Celery worker/beat
   - Should not see Redis connection errors

### Frontend (Vercel)

1. Check browser console when loading checkout:
   - Should not see "Stripe publishable key not found" warning

2. Test Stripe checkout:
   - Navigate to subscription page
   - Click "Subscribe"
   - Should redirect to Stripe checkout (not error)

---

## 📚 Related Documentation

- [Environment Variables Setup](../setup/environment.md)
- [Stripe Environment Verification](../setup/STRIPE_ENV_VERIFICATION.md)
- [Google OAuth Quick Checklist](../setup/GOOGLE_AUTH_QUICK_CHECKLIST.md)
- [Latest Changes Deployment Guide](./LATEST_CHANGES_DEPLOYMENT.md)

---

## ✅ Verification Checklist

Before deploying, verify:

- [ ] `REDIS_URL` is set in Railway (all 3 services)
- [ ] `STRIPE_WEBHOOK_SECRET` is set in Railway (all 3 services)
- [ ] `ENVIRONMENT=production` is set in Railway (all 3 services)
- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` is set in Vercel
- [ ] Stripe webhook endpoint is configured in Stripe Dashboard: `https://abstrak.to/api/payments/stripe/webhook`
- [ ] Webhook secret matches `STRIPE_WEBHOOK_SECRET` in Railway
- [ ] All Google OAuth variables are set (already done ✅)
- [ ] CORS includes frontend domain
- [ ] Frontend URL matches production domain

---

## 🎯 Quick Fix Commands

### For Railway (Backend)

```bash
# Add missing variables via Railway CLI
railway variables set REDIS_URL=redis://your-redis-host:6379/0
railway variables set STRIPE_WEBHOOK_SECRET=whsec_your_secret
railway variables set ENVIRONMENT=production
```

### For Vercel (Frontend)

```bash
# Add via Vercel CLI
vercel env add NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY production
# Then enter: pk_live_your_key_here
```

Or use the Vercel Dashboard → Settings → Environment Variables.

