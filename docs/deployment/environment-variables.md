# Environment Variables Guide

## Overview

**Frontend (Vercel)** and **Backend (Railway)** need different environment variables. Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser (client-side), while other variables are server-side only.

---

## 🎨 Frontend (Vercel) Environment Variables

### Required

```bash
NEXT_PUBLIC_API_URL=https://fact-checkr-production.up.railway.app
```
**Purpose:** Tells the frontend where to send API requests  
**Where:** Vercel Dashboard → Project → Settings → Environment Variables  
**When:** Set for Production, Preview, and Development

### Optional (if using Stripe)

```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...  # or pk_live_... for production
```
**Purpose:** Stripe checkout integration (publishable key is safe to expose)  
**Note:** Only needed if you're using subscription/payment features

---

## ⚙️ Backend (Railway) Environment Variables

### Required

```bash
# Database
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# Redis (for Celery background tasks)
REDIS_URL=redis://redis.railway.internal:6379/0
# OR if using Railway service reference:
# REDIS_URL=${{redis.REDIS_URL}}
```

### Optional (for full functionality)

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
SERPER_API_KEY=...
YOUTUBE_API_KEY=...

# Stripe (for subscriptions)
STRIPE_SECRET_KEY=sk_test_...  # or sk_live_... for production
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_MONTHLY_PRICE_ID=price_...
STRIPE_PRO_YEARLY_PRICE_ID=price_...
STRIPE_TEAM_MONTHLY_PRICE_ID=price_...
STRIPE_TEAM_YEARLY_PRICE_ID=price_...

# Frontend URL (for Stripe redirects)
FRONTEND_URL=https://your-frontend-domain.vercel.app

# CORS Origins (comma-separated)
CORS_ORIGINS=https://factcheck.mx,https://www.factcheck.mx,http://localhost:3000

# JWT Secret (for authentication)
JWT_SECRET_KEY=your-secret-key-here

# Twitter/X API (optional)
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_SECRET=...
TWITTER_BEARER_TOKEN=...

# Port (DO NOT SET - Railway sets this automatically)
# PORT=<Railway handles this>
```

---

## ❌ What NOT to Put in Vercel

**Never put these in Vercel (frontend):**

- ❌ `DATABASE_URL` - Only backend needs database access
- ❌ `REDIS_URL` - Only backend needs Redis
- ❌ `STRIPE_SECRET_KEY` - Secret keys should never be in frontend
- ❌ `JWT_SECRET_KEY` - Secret keys should never be in frontend
- ❌ Any API secret keys - Only publishable/client keys should be in frontend
- ❌ `PORT` - Not needed for Next.js frontend

**Why?** These are server-side secrets. The frontend runs in the browser where anyone can see the code. Only `NEXT_PUBLIC_*` variables are safe to expose.

---

## ✅ Quick Setup Checklist

### Vercel (Frontend)
- [ ] `NEXT_PUBLIC_API_URL` = `https://fact-checkr-production.up.railway.app`
- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` = `pk_...` (if using Stripe)

### Railway (Backend)
- [ ] `DATABASE_URL` = Your Neon PostgreSQL URL
- [ ] `REDIS_URL` = Redis connection string
- [ ] API keys (Anthropic, OpenAI, etc.) as needed
- [ ] `STRIPE_SECRET_KEY` (if using Stripe)
- [ ] `CORS_ORIGINS` (optional, defaults included)

---

## 🔒 Security Notes

1. **Frontend variables** (`NEXT_PUBLIC_*`):
   - Exposed to browser
   - Only use for non-sensitive config
   - Safe: API URLs, publishable keys

2. **Backend variables**:
   - Server-side only
   - Never exposed to browser
   - Use for: Database URLs, secret keys, API secrets

3. **Stripe Keys**:
   - Frontend: `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` (safe to expose)
   - Backend: `STRIPE_SECRET_KEY` (never expose)

---

## 📝 Example Configuration

### Vercel Environment Variables
```
NEXT_PUBLIC_API_URL=https://fact-checkr-production.up.railway.app
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_51AbCdEf...
```

### Railway Environment Variables
```
DATABASE_URL=postgresql://neondb_owner:password@ep-xxx.neon.tech/neondb?sslmode=require
REDIS_URL=${{redis.REDIS_URL}}
ANTHROPIC_API_KEY=sk-ant-...
STRIPE_SECRET_KEY=sk_test_...
FRONTEND_URL=https://your-app.vercel.app
```

---

## 🧪 Testing

After setting environment variables:

**Frontend:**
```bash
# Test locally
cd frontend
npm run dev
# Check browser console - should connect to backend

# Test in Vercel
# Deploy and check browser console on live site
```

**Backend:**
```bash
# Test health endpoint
curl https://fact-checkr-production.up.railway.app/health
```

---

## 🔄 After DNS Propagation

Once `factcheck.mx` DNS is ready:

1. **Update Frontend** (Vercel):
   - `NEXT_PUBLIC_API_URL=https://factcheck.mx` (if backend is on that domain)
   
2. **Update Backend** (Railway):
   - `CORS_ORIGINS=https://factcheck.mx,https://www.factcheck.mx,http://localhost:3000`
   - `FRONTEND_URL=https://factcheck.mx` (if frontend is on that domain)

