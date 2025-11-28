# Frontend-Backend Connection Guide

## Current Configuration

### Backend (Railway)
- **Railway Domain**: `https://fact-checkr-production.up.railway.app`
- **Custom Domain**: `https://factcheck.mx` (waiting for DNS propagation)
- **Health Check**: ✅ Working at `/health` endpoint

### Frontend Configuration

#### For Local Development

Create/update `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=https://fact-checkr-production.up.railway.app
```

#### For Vercel Production

1. Go to **Vercel Dashboard** → Your Project → **Settings** → **Environment Variables**
2. Add/Update:
   ```
   NEXT_PUBLIC_API_URL=https://fact-checkr-production.up.railway.app
   ```
3. **Redeploy** your frontend

### Once DNS Propagates for `factcheck.mx`

After `factcheck.mx` DNS is fully propagated:

1. Update Railway backend CORS (if needed) via Variables:
   ```bash
   CORS_ORIGINS=https://factcheck.mx,https://www.factcheck.mx,http://localhost:3000
   ```

2. Update frontend environment:
   - Local: `frontend/.env.local`: `NEXT_PUBLIC_API_URL=https://factcheck.mx`
   - Vercel: Update `NEXT_PUBLIC_API_URL` to `https://factcheck.mx`
   - Redeploy frontend

## CORS Configuration

Backend currently allows:
- `http://localhost:3000` (local dev)
- `https://factcheck.mx`
- `https://www.factcheck.mx`
- `https://fact-checkr-production.up.railway.app`
- All Vercel preview deployments (`*.vercel.app`)

To add more origins, set `CORS_ORIGINS` environment variable in Railway:
```bash
CORS_ORIGINS=https://factcheck.mx,https://www.factcheck.mx,https://your-frontend.vercel.app
```

## Testing Connection

```bash
# Test backend health
curl https://fact-checkr-production.up.railway.app/health

# Expected response:
# {"status":"healthy","message":"API is operational"}

# Test from frontend (browser console)
fetch('https://fact-checkr-production.up.railway.app/health')
  .then(r => r.json())
  .then(console.log)
```

## Troubleshooting

### CORS Errors
- Check that your frontend origin is in the backend's `CORS_ORIGINS`
- Verify `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- Check browser console for exact CORS error message

### Connection Refused
- Verify Railway backend is running (check logs)
- Test health endpoint: `curl https://fact-checkr-production.up.railway.app/health`
- Check Railway service status

### DNS Issues
- Use Railway domain (`fact-checkr-production.up.railway.app`) until DNS propagates
- DNS propagation can take 24-48 hours

