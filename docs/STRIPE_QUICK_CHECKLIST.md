# ✅ Stripe Setup Quick Checklist

Use this checklist to quickly verify your Stripe integration is complete.

## 🔑 Step 1: Stripe Dashboard Setup (5-10 min)

- [ ] Created **Pro** product in Stripe
- [ ] Added **Pro Monthly** price ($19) → Copied Price ID
- [ ] Added **Pro Yearly** price ($190) → Copied Price ID
- [ ] Created **Team** product in Stripe
- [ ] Added **Team Monthly** price ($79) → Copied Price ID
- [ ] Added **Team Yearly** price ($790) → Copied Price ID
- [ ] Copied **Publishable Key** (pk_test_... or pk_live_...)
- [ ] Copied **Secret Key** (sk_test_... or sk_live_...)

## 🚂 Step 2: Railway Backend Variables

Add these 6 variables in Railway → Backend → Variables:

- [ ] `STRIPE_SECRET_KEY` = sk_test_... (or sk_live_...)
- [ ] `STRIPE_PRO_MONTHLY_PRICE_ID` = price_...
- [ ] `STRIPE_PRO_YEARLY_PRICE_ID` = price_...
- [ ] `STRIPE_TEAM_MONTHLY_PRICE_ID` = price_...
- [ ] `STRIPE_TEAM_YEARLY_PRICE_ID` = price_...
- [ ] `FRONTEND_URL` = https://factcheck.mx (your domain)

## 🎨 Step 3: Vercel Frontend Variables

Add this 1 variable in Vercel → Project → Settings → Environment Variables:

- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` = pk_test_... (or pk_live_...)

Then:
- [ ] Redeploy frontend after adding variable

## 🔔 Step 4: Stripe Webhook Setup

- [ ] Created webhook endpoint in Stripe Dashboard
- [ ] Webhook URL: `https://fact-checkr-production.up.railway.app/subscriptions/webhook`
- [ ] Selected events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
- [ ] Copied **Webhook Signing Secret** (whsec_...)
- [ ] Added `STRIPE_WEBHOOK_SECRET` to Railway backend variables

## 🧪 Step 5: Test

- [ ] Go to `/subscription` page
- [ ] Click "Iniciar Prueba Gratuita de 7 Días" (Pro plan)
- [ ] See Stripe checkout page (should be in Spanish)
- [ ] Use test card: `4242 4242 4242 4242`
- [ ] Complete payment
- [ ] Redirected to `/subscription/success`
- [ ] Check Stripe Dashboard → Payments (should see payment)
- [ ] Check Stripe Dashboard → Customers (should see customer)

## ✅ All Done!

If all checkboxes are checked, your Stripe integration is complete! 🎉

---

**Need help?** See the full guide: `docs/STRIPE_SETUP_GUIDE.md`

