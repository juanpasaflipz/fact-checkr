# Stripe Integration Setup Guide

This guide covers the complete Stripe integration for both backend and frontend.

## Installation Status

✅ **Backend**: Stripe Python SDK is already installed (see `backend/requirements.txt`)
✅ **Frontend**: Stripe JS SDK installed (`@stripe/stripe-js` v8.5.2)

## Quick Start

### 1. Get Stripe API Keys

1. Sign up at [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navigate to **Developers > API keys**
3. Copy your keys:
   - **Publishable key** (starts with `pk_test_...` or `pk_live_...`)
   - **Secret key** (starts with `sk_test_...` or `sk_live_...`)

### 2. Create Products and Prices in Stripe

1. Go to **Products** in Stripe Dashboard
2. Create products for each tier:
   - **Pro Monthly** - Create product, add monthly recurring price
   - **Pro Yearly** - Add yearly recurring price to same product
   - **Team Monthly** - Create product, add monthly recurring price
   - **Team Yearly** - Add yearly recurring price to same product
3. Copy the **Price IDs** (format: `price_xxxxxxxxxxxxx`)

### 3. Configure Backend Environment

Add to `backend/.env`:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Stripe Price IDs
STRIPE_PRO_MONTHLY_PRICE_ID=price_xxxxxxxxxxxxx
STRIPE_PRO_YEARLY_PRICE_ID=price_xxxxxxxxxxxxx
STRIPE_TEAM_MONTHLY_PRICE_ID=price_xxxxxxxxxxxxx
STRIPE_TEAM_YEARLY_PRICE_ID=price_xxxxxxxxxxxxx

# Frontend URL (for checkout redirects)
FRONTEND_URL=http://localhost:3000
```

### 4. Configure Frontend Environment

Add to `frontend/.env.local`:

```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
```

### 5. Set Up Webhook Endpoint

1. In Stripe Dashboard, go to **Developers > Webhooks**
2. Click **Add endpoint**
3. Set endpoint URL: `https://your-domain.com/subscriptions/webhook`
   - For local testing, use [Stripe CLI](https://stripe.com/docs/stripe-cli):
     ```bash
     stripe listen --forward-to localhost:8000/subscriptions/webhook
     ```
4. Select events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Copy the **Webhook signing secret** (starts with `whsec_...`) to `STRIPE_WEBHOOK_SECRET`

## Frontend Pages Created

✅ **Pricing/Subscription Page**: `/subscription`
- Shows all tiers (Free, Pro, Team) with features
- Monthly/Annual billing toggle
- Direct integration with Stripe checkout
- Matches Figma design specifications

✅ **Success Page**: `/subscription/success`
- Payment confirmation screen
- Subscription details display
- Next steps guidance
- Links to dashboard

✅ **Cancel Page**: `/subscription/cancel`
- Payment cancellation confirmation
- Option to try again

## Usage Examples

### Frontend: Redirect to Checkout

```typescript
import { redirectToCheckout } from '@/lib/stripe';

// In your component
const handleSubscribe = async () => {
  try {
    await redirectToCheckout('pro', 'month', 7); // 7-day trial
  } catch (error) {
    console.error('Checkout error:', error);
  }
};
```

### Frontend: Get Subscription Info

```typescript
const response = await fetch(`${apiUrl}/subscriptions/info`, {
  headers: {
    'Authorization': `Bearer ${token}`,
  },
});
const data = await response.json();
// data.subscription, data.tier, data.limits
```

### Accessing the Pricing Page

Users can access the subscription page via:
- Sidebar "Actualizar Plan" button
- Direct URL: `/subscription`
- Programmatic navigation: `router.push('/subscription')`

### Backend: Subscription Routes

- `GET /subscriptions/info` - Get current user's subscription
- `POST /subscriptions/create-checkout-session` - Create checkout session
- `POST /subscriptions/webhook` - Handle Stripe webhooks

## Testing

### Test Cards (Stripe Test Mode)

- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **3D Secure**: `4000 0025 0000 3155`

Use any future expiry date, any CVC, and any ZIP code.

### Local Webhook Testing

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/subscriptions/webhook
```

## Production Checklist

- [ ] Switch to live API keys (`pk_live_...` and `sk_live_...`)
- [ ] Update `FRONTEND_URL` to production domain
- [ ] Set up production webhook endpoint
- [ ] Test subscription flow end-to-end
- [ ] Verify webhook events are being received
- [ ] Test subscription cancellation
- [ ] Test subscription upgrades/downgrades

## Architecture

- **Backend** (`backend/app/subscriptions.py`): Handles Stripe API calls, customer/subscription management
- **Backend Router** (`backend/app/routers/subscriptions.py`): API endpoints for checkout and webhooks
- **Frontend Utility** (`frontend/src/lib/stripe.ts`): Client-side Stripe initialization and checkout helpers

## Security Notes

- Never expose secret keys in frontend code
- Always verify webhook signatures using `STRIPE_WEBHOOK_SECRET`
- Use HTTPS in production
- Validate user authentication before creating checkout sessions

