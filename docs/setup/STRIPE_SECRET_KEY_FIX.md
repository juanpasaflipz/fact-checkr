# Fix: Stripe Secret Key Error

## Error Message

```
This API call cannot be made with a publishable API key. 
Please use a secret API key.
```

## Problem

Your `STRIPE_SECRET_KEY` in Railway is set to a **publishable key** (`pk_...`) instead of a **secret key** (`sk_...`).

## Quick Fix

### Step 1: Get Your Secret Key

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navigate to **Developers > API keys**
3. Find the **Secret key** (starts with `sk_test_...` or `sk_live_...`)
4. **Copy it** (you can reveal it by clicking "Reveal test key" or "Reveal live key")

### Step 2: Update Railway Variable

**Option A: Railway Dashboard**
1. Go to [Railway Dashboard](https://railway.app)
2. Select your **backend service**
3. Click **Variables** tab
4. Find `STRIPE_SECRET_KEY`
5. Click the edit icon (pencil)
6. **Replace** the value with your secret key (starts with `sk_`)
7. Click **Save**
8. Railway will automatically redeploy

**Option B: Railway CLI**
```bash
railway variables set STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
# or for production:
railway variables set STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
```

## Key Differences

| Key Type | Starts With | Used For | Where to Set |
|----------|------------|----------|--------------|
| **Secret Key** | `sk_test_` or `sk_live_` | Backend API calls | Railway backend `STRIPE_SECRET_KEY` |
| **Publishable Key** | `pk_test_` or `pk_live_` | Frontend checkout | Vercel frontend `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` |

## Verification

After updating, check Railway logs. You should see:

```
✅ Stripe configuration is valid
  - Secret Key: ********************...abcd
```

Instead of:

```
⚠️  Stripe configuration has issues:
  API errors: STRIPE_SECRET_KEY (error: This API call cannot be made with a publishable API key...)
```

## Important Notes

- **Never** use publishable keys (`pk_...`) in backend environment variables
- **Never** use secret keys (`sk_...`) in frontend code or environment variables
- Secret keys should **never** be exposed in client-side code
- Test keys (`sk_test_...`) are for development/testing
- Live keys (`sk_live_...`) are for production

## After Fixing

1. Wait for Railway to redeploy (usually 1-2 minutes)
2. Try creating a checkout session again
3. The error should be resolved

