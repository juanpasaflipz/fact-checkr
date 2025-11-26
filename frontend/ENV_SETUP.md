# Frontend Environment Variables Setup

Create a `.env.local` file in the `frontend/` directory with the following variables:

```bash
# Backend API URL
# Default: http://localhost:8000
# Change this if your backend is running on a different host/port
NEXT_PUBLIC_API_URL=http://localhost:8000

# Stripe Publishable Key (required for Stripe checkout)
# Get your publishable key from: https://dashboard.stripe.com/apikeys
# Use test key (pk_test_...) for development, live key (pk_live_...) for production
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
```

## Quick Setup

1. Create the `.env.local` file:
```bash
cd frontend
touch .env.local
# Add: NEXT_PUBLIC_API_URL=http://localhost:8000
```

2. Or copy from this template:
```bash
cd frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

## Required vs Optional Variables

**Required:**
- `NEXT_PUBLIC_API_URL` - Backend API URL (defaults to `http://localhost:8000` if not set)

**Optional but Recommended:**
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` - Required for subscription checkout. Get from [Stripe Dashboard](https://dashboard.stripe.com/apikeys). Use `pk_test_...` for development, `pk_live_...` for production.

## Notes

- Next.js requires the `NEXT_PUBLIC_` prefix for environment variables that should be accessible in the browser
- The default value is `http://localhost:8000` if the variable is not set
- Restart the Next.js dev server after changing environment variables

