# Stripe Environment Variable Verification Guide

This guide explains how to verify that your Stripe environment variables are correctly configured for FactCheckr MX.

## Overview

The backend automatically validates Stripe configuration at startup. This ensures that all required environment variables are present and properly formatted before the application starts accepting payments.

## Required Environment Variables

### Backend Variables

All of these must be set in your backend `.env` file or environment:

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_test_... or sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Price IDs (from Stripe Dashboard)
STRIPE_PRO_MONTHLY_PRICE_ID=price_...
STRIPE_PRO_YEARLY_PRICE_ID=price_...
STRIPE_TEAM_MONTHLY_PRICE_ID=price_...
STRIPE_TEAM_YEARLY_PRICE_ID=price_...

# Frontend URL (for redirects)
FRONTEND_URL=http://localhost:3000  # or your production URL
```

### Frontend Variables

Set in `frontend/.env.local`:

```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_... or pk_live_...
```

## Validation Checks

The backend performs the following validations at startup:

### 1. Presence Check
- Verifies all required variables are set (not empty)

### 2. Format Validation
- **STRIPE_SECRET_KEY**: Must start with `sk_test_` or `sk_live_`
- **STRIPE_WEBHOOK_SECRET**: Must start with `whsec_`
- **Price IDs**: Must start with `price_`

### 3. API Connection Test
- Attempts to authenticate with Stripe using the secret key
- Verifies the key is valid and active

## Startup Logs

When the backend starts, you'll see validation results in the logs:

### Success Example
```
==================================================
Validating Stripe configuration...
==================================================
✅ Stripe configuration is valid
  - Secret Key: ********************...abcd
  - Webhook Secret: ********************...xyz
  - All price IDs configured
==================================================
```

### Warning Example
```
==================================================
Validating Stripe configuration...
==================================================
⚠️  Stripe configuration has issues:
  Missing variables: STRIPE_TEAM_MONTHLY_PRICE_ID
  Invalid format: STRIPE_SECRET_KEY (must start with sk_test_ or sk_live_)
  API errors: STRIPE_SECRET_KEY (authentication failed - invalid key)
  Stripe features may not work correctly until these are fixed.
  See docs/setup/STRIPE_ENV_VERIFICATION.md for setup instructions.
==================================================
```

## Setup Instructions

### Step 1: Get Stripe API Keys

1. Sign up at [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navigate to **Developers > API keys**
3. Copy your keys:
   - **Publishable key** (starts with `pk_test_...` or `pk_live_...`)
   - **Secret key** (starts with `sk_test_...` or `sk_live_...`)

### Step 2: Create Products and Prices

1. Go to **Products** in Stripe Dashboard
2. Create products for each tier:
   - **Pro Monthly**: Create product, add monthly recurring price
   - **Pro Yearly**: Add yearly recurring price to same product
   - **Team Monthly**: Create product, add monthly recurring price
   - **Team Yearly**: Add yearly recurring price to same product
3. Copy the **Price IDs** (format: `price_xxxxxxxxxxxxx`)

### Step 3: Set Up Webhook

1. In Stripe Dashboard, go to **Developers > Webhooks**
2. Click **Add endpoint**
3. Set endpoint URL: `https://abstrak.to/api/payments/stripe/webhook` (Production)
   - For local testing, use [Stripe CLI](https://stripe.com/docs/stripe-cli):
     ```bash
     stripe listen --forward-to localhost:8000/api/subscriptions/webhook
     ```
4. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Copy the **Webhook signing secret** (starts with `whsec_...`)

### Step 4: Configure Environment Variables

#### Backend (`.env` or platform environment variables)

```bash
# Use test keys for development
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Price IDs from Step 2
STRIPE_PRO_MONTHLY_PRICE_ID=price_xxxxxxxxxxxxx
STRIPE_PRO_YEARLY_PRICE_ID=price_xxxxxxxxxxxxx
STRIPE_TEAM_MONTHLY_PRICE_ID=price_xxxxxxxxxxxxx
STRIPE_TEAM_YEARLY_PRICE_ID=price_xxxxxxxxxxxxx

# Frontend URL
FRONTEND_URL=http://localhost:3000  # Development
# FRONTEND_URL=https://your-domain.com  # Production
```

#### Frontend (`.env.local` or Vercel environment variables)

```bash
# Use test key for development
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
```

### Step 5: Verify Configuration

1. Restart your backend server
2. Check the startup logs for validation results
3. If there are warnings, fix the issues and restart

## Testing

### Test Mode

Use Stripe test mode for development:

- Test cards: `4242 4242 4242 4242` (always succeeds)
- Test webhook events: Use Stripe CLI to forward webhooks locally

### Local Webhook Testing

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local backend
stripe listen --forward-to localhost:8000/api/subscriptions/webhook
```

## Production Checklist

Before going live:

- [ ] Switch to live API keys (`sk_live_...` and `pk_live_...`)
- [ ] Update `FRONTEND_URL` to production domain
- [ ] Create production webhook endpoint in Stripe Dashboard: `https://abstrak.to/api/payments/stripe/webhook`
- [ ] Update `STRIPE_WEBHOOK_SECRET` with production webhook secret
- [ ] Verify all price IDs are correct for production products
- [ ] Test checkout flow end-to-end
- [ ] Verify webhook events are being received

## Troubleshooting

### "Stripe configuration has issues" Warning

1. **Missing variables**: Add all required variables to your `.env` file
2. **Invalid format**: Check that keys start with correct prefixes
3. **API errors**: Verify your secret key is correct and active

### Checkout Not Working

1. Verify `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` is set in frontend
2. Check browser console for errors
3. Verify backend logs for API errors
4. Ensure user is authenticated (checkout requires login)

### Webhook Not Receiving Events

1. Verify webhook endpoint URL is correct in Stripe Dashboard
2. Check webhook secret matches `STRIPE_WEBHOOK_SECRET`
3. Test with Stripe CLI locally
4. Check backend logs for webhook processing errors

## Additional Resources

- [Stripe API Documentation](https://stripe.com/docs/api)
- [Stripe Testing Guide](https://stripe.com/docs/testing)
- [Stripe Webhooks Guide](https://stripe.com/docs/webhooks)

