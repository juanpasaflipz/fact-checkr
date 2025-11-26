# Vercel Deployment Guide - Frontend

## Prerequisites
- Vercel account
- GitHub repository connected
- Backend deployed to Railway (to get API URL)

## Step 1: Import Project to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New** → **Project**
3. Import your GitHub repository `fact-checkr`
4. Configure:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `.next` (auto-detected)
   - **Install Command**: `npm ci` (auto-detected)

## Step 2: Configure Environment Variables

In Vercel project settings → Environment Variables, add:

### Required:
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### Optional (if using Stripe):
```
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Optional (Analytics):
```
NEXT_PUBLIC_GA_ID=G-...
```

**Important**: Make sure to add these to **Production**, **Preview**, and **Development** environments as needed.

## Step 3: Deploy

1. Click **Deploy**
2. Vercel will:
   - Install dependencies
   - Build the Next.js app
   - Deploy to global CDN
   - Provide a production URL (e.g., `https://factcheckr-mx.vercel.app`)

## Step 4: Update Backend CORS

After deployment, update your Railway backend environment variables:

```
FRONTEND_URL=https://factcheckr-mx.vercel.app
```

This allows the backend to accept requests from your frontend domain.

## Step 5: Custom Domain (Optional)

1. In Vercel project → **Settings** → **Domains**
2. Add your custom domain (e.g., `factcheckr.mx`)
3. Follow DNS configuration instructions
4. Update `FRONTEND_URL` in Railway backend to use custom domain

## Vercel Configuration

The project uses `vercel.json` at repo root with:
- Build command pointing to frontend directory
- Output directory configuration
- API proxy rules (if needed)

## Automatic Deployments

Vercel automatically deploys:
- **Production**: Every push to `main` branch
- **Preview**: Every push to other branches and PRs

## Monitoring

- **Build Logs**: Check in Vercel dashboard
- **Runtime Logs**: Available in Vercel dashboard
- **Analytics**: Enable Vercel Analytics for performance insights

## Troubleshooting

### Build Fails
- Check Node.js version (requires >=20.0.0)
- Verify all dependencies are in `package.json`
- Review build logs for specific errors

### API Calls Fail
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check backend CORS configuration includes Vercel domain
- Ensure backend is running and accessible

### Environment Variables Not Working
- Variables must start with `NEXT_PUBLIC_` to be exposed to browser
- Redeploy after adding/changing environment variables
- Check variable names match exactly in code

## Performance Optimization

Vercel automatically provides:
- Global CDN distribution
- Image optimization
- Automatic static optimization
- Edge caching

## Security

- All environment variables are encrypted
- Secrets (without `NEXT_PUBLIC_`) are only available server-side
- HTTPS enabled by default
- Security headers configured in `next.config.ts`

