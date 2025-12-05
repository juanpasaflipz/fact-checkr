# Stripe Webhook Endpoint Configuration

## Production Webhook URL

**Endpoint:** `https://abstrak.to/api/payments/stripe/webhook`

This is the production Stripe webhook endpoint URL configured in your Stripe Dashboard.

## Setup Instructions

### 1. Configure in Stripe Dashboard

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/) → **Developers** → **Webhooks**
2. Click **Add endpoint** (or edit existing endpoint)
3. Set endpoint URL: `https://abstrak.to/api/payments/stripe/webhook`
4. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Copy the **Webhook signing secret** (starts with `whsec_...`)

### 2. Set Environment Variable

Add the webhook secret to Railway (all 3 services):

```bash
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

### 3. Verify Webhook is Working

1. **Test in Stripe Dashboard:**
   - Go to the webhook endpoint in Stripe Dashboard
   - Click "Send test webhook"
   - Check Railway logs to see if webhook is received

2. **Check Railway Logs:**
   ```bash
   railway logs --service backend
   ```
   Look for webhook processing logs

3. **Test with Stripe CLI (Local):**
   ```bash
   # Forward webhooks to local backend
   stripe listen --forward-to localhost:8000/api/subscriptions/webhook
   ```

## Important Notes

- The webhook endpoint must be publicly accessible
- Stripe will verify the webhook signature using `STRIPE_WEBHOOK_SECRET`
- The webhook handler is at `/api/subscriptions/webhook` in the backend code
- The production URL `https://abstrak.to/api/payments/stripe/webhook` may be proxied/rewritten from the backend route

## Troubleshooting

### Webhook Not Receiving Events

1. **Check endpoint URL in Stripe Dashboard:**
   - Must match exactly: `https://abstrak.to/api/payments/stripe/webhook`
   - No trailing slashes
   - HTTPS required

2. **Verify `STRIPE_WEBHOOK_SECRET` is set:**
   ```bash
   railway variables --service backend | grep STRIPE_WEBHOOK_SECRET
   ```

3. **Check Railway logs for errors:**
   ```bash
   railway logs --service backend | grep webhook
   ```

### Signature Verification Failed

- Ensure `STRIPE_WEBHOOK_SECRET` matches the secret from Stripe Dashboard
- Secret must start with `whsec_`
- No extra spaces or quotes in the environment variable

### Webhook Returns 500 Error

- Check backend logs for processing errors
- Verify database connection is working
- Ensure all required tables exist (run migrations)

## Related Documentation

- [Stripe Environment Verification](../setup/STRIPE_ENV_VERIFICATION.md)
- [Missing Environment Variables](./MISSING_ENV_VARIABLES.md)
- [Latest Changes Deployment](./LATEST_CHANGES_DEPLOYMENT.md)

