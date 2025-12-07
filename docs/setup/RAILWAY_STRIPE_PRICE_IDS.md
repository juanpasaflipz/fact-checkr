# Setting Stripe Price IDs in Railway

## Quick Fix for "Price ID not configured" Error

If you're seeing the error:
```
Price ID not configured for pro month
```

This means the Stripe Price IDs are missing from your **backend Railway environment variables**.

## Required Environment Variables

Add these 4 variables to your **Railway backend service**:

1. `STRIPE_PRO_MONTHLY_PRICE_ID` = `price_xxxxxxxxxxxxx`
2. `STRIPE_PRO_YEARLY_PRICE_ID` = `price_xxxxxxxxxxxxx`
3. `STRIPE_TEAM_MONTHLY_PRICE_ID` = `price_xxxxxxxxxxxxx`
4. `STRIPE_TEAM_YEARLY_PRICE_ID` = `price_xxxxxxxxxxxxx`

## How to Add in Railway Dashboard

1. Go to [Railway Dashboard](https://railway.app)
2. Select your **backend service** (not frontend)
3. Click on the **Variables** tab
4. Click **+ New Variable**
5. Add each variable:
   - **Name**: `STRIPE_PRO_MONTHLY_PRICE_ID`
   - **Value**: Your Price ID from Stripe (starts with `price_`)
6. Repeat for all 4 Price IDs
7. Railway will automatically redeploy after adding variables

## How to Add via Railway CLI

```bash
# Login to Railway
railway login

# Link to your project
railway link

# Add each Price ID
railway variables set STRIPE_PRO_MONTHLY_PRICE_ID=price_xxxxxxxxxxxxx
railway variables set STRIPE_PRO_YEARLY_PRICE_ID=price_xxxxxxxxxxxxx
railway variables set STRIPE_TEAM_MONTHLY_PRICE_ID=price_xxxxxxxxxxxxx
railway variables set STRIPE_TEAM_YEARLY_PRICE_ID=price_xxxxxxxxxxxxx
```

## Where to Get Price IDs

1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Navigate to **Products**
3. Click on your product (e.g., "Pro Plan")
4. Under **Pricing**, you'll see the Price IDs
5. Copy the ID (format: `price_xxxxxxxxxxxxx`)

**Important**: 
- Use **Live** Price IDs if you're in production mode
- Use **Test** Price IDs if you're testing (they start with `price_` too)

## Verify Configuration

After adding the variables, check Railway logs:

```bash
railway logs --service backend
```

Look for any errors about missing Price IDs. The backend should start successfully.

## Quick Test

Once configured, try creating a checkout session again. The error should be resolved.

## Notes

- **Backend only**: Price IDs are only needed in the backend, not frontend
- **Frontend needs**: Only `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` (different from Price IDs)
- **Format**: All Price IDs must start with `price_`
- **No spaces**: Make sure there are no extra spaces in the Price ID values

