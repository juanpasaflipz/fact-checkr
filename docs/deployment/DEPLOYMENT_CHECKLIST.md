# Deployment Checklist

## ✅ Backend (Railway) - COMPLETE

- [x] Backend service deployed on Railway
- [x] Health check passing (`/health` returns 200)
- [x] Database connected (Neon PostgreSQL)
- [x] Redis configured (for Celery tasks)
- [x] Public domain: `https://fact-checkr-production.up.railway.app`
- [x] Custom domain: `factcheck.mx` (waiting for DNS)
- [x] CORS configured for frontend origins
- [x] Environment variables set in Railway

## 🔄 Frontend (Vercel) - IN PROGRESS

### Setup Steps

1. **Connect Repository**
   - [ ] Go to vercel.com
   - [ ] Import GitHub repository
   - [ ] Set root directory to `frontend`

2. **Configure Build Settings**
   - [ ] Framework: Next.js (auto-detected)
   - [ ] Root Directory: `frontend`
   - [ ] Build Command: `npm run build` (default)
   - [ ] Output Directory: `.next` (default)

3. **Set Environment Variables**
   - [ ] `NEXT_PUBLIC_API_URL=https://fact-checkr-production.up.railway.app`
   - [ ] Any Stripe/public keys needed
   - [ ] Set for Production, Preview, and Development

4. **Deploy**
   - [ ] Click "Deploy"
   - [ ] Wait for build to complete
   - [ ] Get deployment URL

5. **Test**
   - [ ] Visit deployed URL
   - [ ] Check browser console for errors
   - [ ] Test API connection
   - [ ] Verify data loads from backend

### Local Testing (Before Deploying)

- [ ] `cd frontend && npm install`
- [ ] Verify `.env.local` has `NEXT_PUBLIC_API_URL`
- [ ] `npm run dev`
- [ ] Open http://localhost:3000
- [ ] Check browser console - should connect to backend
- [ ] Verify data loads correctly

## 📋 Quick Test Commands

```bash
# Test backend
curl https://fact-checkr-production.up.railway.app/health

# Test CORS
curl -H "Origin: http://localhost:3000" \
  https://fact-checkr-production.up.railway.app/health

# Run connection test script
./test-connection.sh
```

## 🐛 Troubleshooting

### Backend Issues
- Check Railway logs: Dashboard → Service → Logs
- Verify health endpoint: `curl https://fact-checkr-production.up.railway.app/health`
- Check environment variables in Railway

### Frontend Issues
- Verify `NEXT_PUBLIC_API_URL` in Vercel environment variables
- Check browser console for CORS errors
- Test backend directly (should work)
- Check Vercel build logs for errors

### Connection Issues
- Backend health check must pass first
- CORS must allow frontend origin
- Network requests must not be blocked
- Check browser Network tab for failed requests

## 📝 After DNS Propagation

When `factcheck.mx` DNS is ready:

1. **Backend** (Railway):
   - Update CORS to include `factcheck.mx`
   - Or keep using Railway domain

2. **Frontend** (Vercel):
   - Update `NEXT_PUBLIC_API_URL` if needed
   - Configure custom domain in Vercel
   - Redeploy

## 🎯 Success Criteria

- [ ] Backend health check returns 200
- [ ] Frontend builds successfully on Vercel
- [ ] Frontend loads in browser without errors
- [ ] API calls from frontend succeed
- [ ] Data displays correctly on frontend
- [ ] No CORS errors in browser console

