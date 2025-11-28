# Vercel Frontend Deployment Setup

## Quick Setup Steps

### 1. Connect Repository to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New"** → **"Project"**
3. Import your GitHub repository (`fact-checkr`)
4. Vercel will auto-detect Next.js

### 2. Configure Project Settings

**Root Directory:**
- Set to: `frontend`

**Build Settings:**
- Framework Preset: `Next.js`
- Build Command: `npm run build` (or leave default)
- Output Directory: `.next` (or leave default)
- Install Command: `npm ci` (or leave default)

**Environment Variables:**
Add the following in **Settings → Environment Variables**:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=https://fact-checkr-production.up.railway.app

# Add other frontend environment variables as needed
# STRIPE_PUBLISHABLE_KEY=pk_...
# etc.
```

**Important:** 
- Set these for **Production**, **Preview**, and **Development** environments
- After adding variables, **redeploy** the project

### 3. Domain Configuration (Optional)

If you want to use `factcheck.mx` for frontend:

1. **Settings → Domains**
2. Add domain: `factcheck.mx` (and `www.factcheck.mx` if desired)
3. Follow Vercel's DNS instructions
4. Update `NEXT_PUBLIC_API_URL` accordingly:
   - If frontend is at `factcheck.mx`, backend can be at `api.factcheck.mx` or stay on Railway
   - Or use `https://fact-checkr-production.up.railway.app` (current setup)

### 4. Deploy

1. Click **"Deploy"**
2. Wait for build to complete
3. Test your deployment

### 5. Verify Connection

After deployment, test in browser console:

```javascript
// Test backend connection
fetch('https://fact-checkr-production.up.railway.app/health')
  .then(r => r.json())
  .then(console.log)
// Should return: {status: "healthy", message: "API is operational"}
```

## Testing Locally Before Deploying

```bash
# 1. Make sure backend is running (Railway)
# 2. Start frontend locally
cd frontend
npm install
npm run dev

# 3. Open http://localhost:3000
# 4. Check browser console for any API errors
```

## Common Issues

### CORS Errors
- Verify `NEXT_PUBLIC_API_URL` is set in Vercel environment variables
- Check backend CORS allows your Vercel domain
- Backend should allow `*.vercel.app` (already configured)

### Build Failures
- Check Node.js version matches `package.json` engines (>=20.0.0)
- Verify all dependencies are in `package.json`
- Check build logs in Vercel dashboard

### API Connection Issues
- Test backend directly: `curl https://fact-checkr-production.up.railway.app/health`
- Verify `NEXT_PUBLIC_API_URL` in Vercel matches backend URL
- Check browser Network tab for failed requests

## Environment Variables Checklist

Required:
- [ ] `NEXT_PUBLIC_API_URL` - Backend API URL

Optional (depending on features):
- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` - Stripe public key
- [ ] Other public-facing keys/config

## After DNS Propagation

Once `factcheck.mx` DNS propagates:

1. **Update Backend CORS** (Railway Variables):
   ```bash
   CORS_ORIGINS=https://factcheck.mx,https://www.factcheck.mx,http://localhost:3000
   ```

2. **Update Frontend API URL** (Vercel):
   ```bash
   NEXT_PUBLIC_API_URL=https://factcheck.mx  # or api.factcheck.mx if using subdomain
   ```

3. **Redeploy both services**

