# Frontend Environment Setup Guide

## Quick Setup

### For Local Development

1. Create `.env.local` in the `frontend/` directory:
```bash
cd frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

2. Make sure your backend is running locally:
```bash
cd backend
python -m uvicorn main:app --reload
```

3. Restart your Next.js dev server:
```bash
npm run dev
```

### For Production (Railway Backend)

1. **Find your Railway backend URL:**
   - Go to your Railway project dashboard
   - Navigate to your backend service
   - Copy the public URL (e.g., `https://your-project.up.railway.app`)

2. **Set environment variable in Vercel:**
   - Go to your Vercel project settings
   - Navigate to "Environment Variables"
   - Add: `NEXT_PUBLIC_API_URL=https://your-project.up.railway.app`
   - Make sure to set it for "Production", "Preview", and "Development" environments

3. **Or create `.env.local` for local testing with Railway:**
```bash
cd frontend
echo "NEXT_PUBLIC_API_URL=https://your-project.up.railway.app" > .env.local
```

## Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Optional | Stripe publishable key for payments | - |

## Troubleshooting

### "Network error - Backend may not be running"

This error means the frontend cannot connect to the backend.

**For local development:**
1. ✅ Check if backend is running: `curl http://localhost:8000/health`
2. ✅ Verify `.env.local` exists with `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. ✅ Restart Next.js dev server after changing `.env.local`
4. ✅ Check backend logs for errors

**For production (Railway):**
1. ✅ Verify Railway backend is deployed and running
2. ✅ Check Railway backend logs (dashboard → service → logs)
3. ✅ Test backend URL: `curl https://your-project.up.railway.app/health`
4. ✅ Verify `NEXT_PUBLIC_API_URL` is set in Vercel environment variables
5. ✅ Re-deploy frontend after setting environment variable
6. ✅ Ensure CORS is configured in backend to allow your frontend domain

### Backend Health Check

Test if your backend is accessible:
```bash
# For local
curl http://localhost:8000/health

# For Railway
curl https://your-project.up.railway.app/health
```

Expected response:
```json
{"status":"healthy","message":"API is operational"}
```

## Next Steps

1. **Set up backend URL** (see above)
2. **Restart dev server** after changing `.env.local`
3. **Check browser console** for any remaining errors
4. **Verify backend is running** using health check endpoint
