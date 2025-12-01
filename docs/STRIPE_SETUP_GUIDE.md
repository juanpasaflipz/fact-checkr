# 🎯 Stripe Setup Guide - Complete Walkthrough

This guide will help you connect your FactCheckr subscription pages to Stripe. Follow these steps in order.

---

## 📋 Prerequisites

- ✅ Stripe account (sign up at https://stripe.com)
- ✅ Access to your Railway backend dashboard
- ✅ Access to your Vercel frontend dashboard
- ✅ Your production domain URL (e.g., `https://factcheck.mx`)

---

## Step 1: Create Products & Prices in Stripe Dashboard

### 1.1 Login to Stripe Dashboard
1. Go to https://dashboard.stripe.com
2. Make sure you're in **Test Mode** (toggle in top right) for testing
3. Switch to **Live Mode** when ready for production

### 1.2 Create Pro Product
1. Navigate to **Products** → Click **+ Add product**
2. **Name**: `FactCheckr Pro`
3. **Description**: `Plan Pro para periodistas, investigadores y creadores de contenido`
4. Click **Save product**

### 1.3 Add Pro Monthly Price
1. In the Pro product page, click **Add another price**
2. **Pricing model**: Recurring
3. **Price**: `$199.00 MXN` (Mexican Pesos)
4. **Currency**: Select **MXN** (Mexican Peso)
5. **Billing period**: Monthly
6. Click **Add price**
7. **Copy the Price ID** (starts with `price_...`) → Save this as `STRIPE_PRO_MONTHLY_PRICE_ID`

### 1.4 Add Pro Yearly Price
1. Still in Pro product, click **Add another price**
2. **Pricing model**: Recurring
3. **Price**: `$1900.00 MXN` (Mexican Pesos)
4. **Currency**: Select **MXN** (Mexican Peso)
5. **Billing period**: Yearly
6. Click **Add price**
7. **Copy the Price ID** → Save this as `STRIPE_PRO_YEARLY_PRICE_ID`

### 1.5 Create Team Product
1. Go back to **Products** → Click **+ Add product**
2. **Name**: `FactCheckr Team`
3. **Description**: `Plan Equipo para redacciones pequeñas y ONGs (2-10 usuarios)`
4. Click **Save product**

### 1.6 Add Team Monthly Price
1. In Team product, click **Add another price**
2. **Pricing model**: Recurring
3. **Price**: `$79.00` (or convert to MXN if you want local currency)
4. **Currency**: Select **USD** or **MXN** (your choice)
5. **Billing period**: Monthly
6. Click **Add price**
7. **Copy the Price ID** → Save this as `STRIPE_TEAM_MONTHLY_PRICE_ID`

### 1.7 Add Team Yearly Price
1. Still in Team product, click **Add another price**
2. **Pricing model**: Recurring
3. **Price**: `$790.00` (or convert to MXN if you want local currency)
4. **Currency**: Select **USD** or **MXN** (your choice)
5. **Billing period**: Yearly
6. Click **Add price**
7. **Copy the Price ID** → Save this as `STRIPE_TEAM_YEARLY_PRICE_ID`

**Note**: Pro plan uses MXN (Mexican Pesos). Team plan can use USD or MXN - your choice.

---

## Step 2: Get Stripe API Keys

### 2.1 Get Publishable Key (Frontend)
1. In Stripe Dashboard, go to **Developers** → **API keys**
2. Find **Publishable key** (starts with `pk_test_...` or `pk_live_...`)
3. **Copy this** → Save as `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`

### 2.2 Get Secret Key (Backend)
1. In the same page, find **Secret key** (starts with `sk_test_...` or `sk_live_...`)
2. Click **Reveal test key** or **Reveal live key**
3. **Copy this** → Save as `STRIPE_SECRET_KEY`
4. ⚠️ **Never share this key publicly!**

---

## Step 3: Configure Backend Environment Variables (Railway)

### 3.1 Add Stripe Keys to Railway
1. Go to your Railway project dashboard
2. Select your **backend service**
3. Go to **Variables** tab
4. Add these variables:

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx  # or sk_live_... for production

# Stripe Price IDs (from Step 1)
STRIPE_PRO_MONTHLY_PRICE_ID=price_xxxxxxxxxxxxx
STRIPE_PRO_YEARLY_PRICE_ID=price_xxxxxxxxxxxxx
STRIPE_TEAM_MONTHLY_PRICE_ID=price_xxxxxxxxxxxxx
STRIPE_TEAM_YEARLY_PRICE_ID=price_xxxxxxxxxxxxx

# Frontend URL (for checkout redirects)
FRONTEND_URL=https://factcheck.mx  # or your Vercel URL
```

### 3.2 Verify Backend Variables
- ✅ All 6 variables should be set
- ✅ No typos in Price IDs
- ✅ `FRONTEND_URL` matches your production domain

---

## Step 4: Configure Frontend Environment Variables (Vercel)

### 4.1 Add Stripe Publishable Key to Vercel
1. Go to your Vercel project dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add:

```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx  # or pk_live_... for production
```

### 4.2 Redeploy Frontend
1. After adding the variable, go to **Deployments**
2. Click **Redeploy** on the latest deployment
3. Wait for deployment to complete

---

## Step 5: Set Up Stripe Webhook (CRITICAL)

### 5.1 Create Webhook Endpoint in Stripe
1. In Stripe Dashboard, go to **Developers** → **Webhooks**
2. Click **+ Add endpoint**
3. **Endpoint URL**: `https://fact-checkr-production.up.railway.app/subscriptions/webhook`
   - Replace with your actual Railway backend URL
4. **Description**: `FactCheckr Subscription Webhook`

### 5.2 Select Events to Listen For
Click **Select events** and choose:
- ✅ `checkout.session.completed`
- ✅ `customer.subscription.updated`
- ✅ `customer.subscription.deleted`

Click **Add events**

### 5.3 Get Webhook Signing Secret
1. After creating the endpoint, click on it
2. Find **Signing secret** (starts with `whsec_...`)
3. Click **Reveal** → **Copy**
4. Save this as `STRIPE_WEBHOOK_SECRET`

### 5.4 Add Webhook Secret to Railway
1. Go back to Railway → Backend service → **Variables**
2. Add:
```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

### 5.5 Test Webhook (Optional but Recommended)
1. In Stripe Dashboard → Webhooks → Your endpoint
2. Click **Send test webhook**
3. Select `checkout.session.completed`
4. Click **Send test webhook**
5. Check Railway logs to see if webhook was received

---

## Step 6: Test the Integration

### 6.1 Test Locally (Optional)
1. **Backend**: Make sure all env vars are in `backend/.env`
2. **Frontend**: Add `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` to `frontend/.env.local`
3. Start both services
4. Go to `http://localhost:3000/subscription`
5. Click "Iniciar Prueba Gratuita de 7 Días" on Pro plan
6. Use Stripe test card: `4242 4242 4242 4242`
7. Complete checkout

### 6.2 Test in Production
1. Go to `https://factcheck.mx/subscription`
2. Click on Pro or Team plan
3. Use Stripe test card (if in test mode) or real card (if in live mode)
4. Complete checkout
5. Verify you're redirected to `/subscription/success`
6. Check Stripe Dashboard → **Payments** to see the payment
7. Check Stripe Dashboard → **Customers** to see the customer created

---

## Step 7: Verify Everything Works

### ✅ Checklist

**Backend (Railway):**
- [ ] `STRIPE_SECRET_KEY` is set
- [ ] All 4 Price IDs are set correctly
- [ ] `STRIPE_WEBHOOK_SECRET` is set
- [ ] `FRONTEND_URL` matches your domain
- [ ] Backend is deployed and running

**Frontend (Vercel):**
- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` is set
- [ ] Frontend is deployed

**Stripe Dashboard:**
- [ ] 2 Products created (Pro and Team)
- [ ] 4 Prices created (2 monthly, 2 yearly)
- [ ] Webhook endpoint created
- [ ] Webhook events selected (3 events)
- [ ] Webhook signing secret copied

**Testing:**
- [ ] Can click "Subscribe" button
- [ ] Redirects to Stripe checkout (in Spanish)
- [ ] Can complete payment with test card
- [ ] Redirects to success page after payment
- [ ] Subscription appears in Stripe Dashboard
- [ ] Webhook is received (check Railway logs)

---

## 🔧 Troubleshooting

### Issue: "Failed to create checkout session"
**Solution:**
- Check Railway backend logs for errors
- Verify all Price IDs are correct in Railway variables
- Ensure `STRIPE_SECRET_KEY` is set correctly
- Check that user is authenticated (checkout requires login)

### Issue: "Webhook not received"
**Solution:**
- Verify webhook URL is correct: `https://your-railway-url/subscriptions/webhook`
- Check `STRIPE_WEBHOOK_SECRET` matches the one in Stripe Dashboard
- Ensure Railway backend is accessible (not behind firewall)
- Check Railway logs for webhook errors

### Issue: "Subscription not syncing to database"
**Solution:**
- Check webhook is receiving events (Stripe Dashboard → Webhooks → Your endpoint → Recent events)
- Verify webhook secret is correct
- Check Railway logs for webhook processing errors
- Ensure database connection is working

### Issue: "Checkout page not in Spanish"
**Solution:**
- Already fixed! The backend sets `locale="es"` in checkout session
- If still showing English, clear browser cache and try again

### Issue: "Payment succeeds but subscription not active"
**Solution:**
- Check webhook was received (Stripe Dashboard → Webhooks)
- Verify webhook secret matches
- Check Railway logs for webhook processing
- Manually trigger webhook from Stripe Dashboard if needed

---

## 🚀 Going Live

### Switch to Live Mode
1. In Stripe Dashboard, toggle **Test mode** → **Live mode**
2. Create products/prices again in Live mode (they're separate from test mode)
3. Get Live API keys (different from test keys)
4. Update Railway variables with Live keys and Price IDs
5. Update Vercel variable with Live publishable key
6. Create new webhook endpoint for Live mode
7. Redeploy both backend and frontend

---

## 📞 Support

If you encounter issues:
1. Check Railway backend logs
2. Check Stripe Dashboard → **Developers** → **Logs**
3. Check Vercel deployment logs
4. Verify all environment variables are set correctly

---

## ✅ Success Indicators

You'll know everything is working when:
- ✅ Users can click "Subscribe" and see Stripe checkout
- ✅ Checkout page is in Spanish
- ✅ Payment completes successfully
- ✅ User is redirected to success page
- ✅ Subscription appears in Stripe Dashboard
- ✅ Subscription is saved in your database
- ✅ User can access Pro/Team features

**You're all set! 🎉**

