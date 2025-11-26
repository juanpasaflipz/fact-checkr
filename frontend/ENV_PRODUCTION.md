# Production Environment Variables for Vercel

Copy these to Vercel project settings → Environment Variables:

## Required

```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

## Optional - Stripe (if using subscriptions)

```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Optional - Analytics

```bash
NEXT_PUBLIC_GA_ID=G-...
```

## Notes

- All variables starting with `NEXT_PUBLIC_` are exposed to the browser
- Other variables (like `STRIPE_SECRET_KEY`) are only available server-side
- After adding variables, trigger a new deployment for changes to take effect

