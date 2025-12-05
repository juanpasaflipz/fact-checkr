# Google OAuth Setup Summary

## What You Need to Do

Your Google OAuth implementation is **already coded correctly**. You just need to configure it properly.

## The Problem

Google OAuth requires:
1. **Google Cloud Console setup** - OAuth client with redirect URIs
2. **Backend environment variables** - Client ID, Secret, and Redirect URI
3. **Matching configuration** - Everything must match exactly

## Quick Start (5 Steps)

### 1. Google Cloud Console (5 minutes)
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create OAuth 2.0 Client ID (Web application)
- Add redirect URIs:
  - `http://localhost:8000/api/auth/google/callback` (for localhost)
  - `https://your-backend-domain.com/api/auth/google/callback` (for production)
- Copy Client ID and Client Secret

### 2. Backend Local (.env)
Add to `backend/.env`:
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
FRONTEND_URL=http://localhost:3000
```

### 3. Backend Production (Railway)
Add to Railway environment variables:
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret
GOOGLE_REDIRECT_URI=https://your-backend-domain.com/api/auth/google/callback
FRONTEND_URL=https://www.factcheck.mx
```

### 4. Test Locally
```bash
# Start backend
cd backend && uvicorn main:app --reload

# Start frontend
cd frontend && npm run dev

# Visit http://localhost:3000/signin
# Click "Continuar con Google"
```

### 5. Deploy to Production
- Update Railway environment variables
- Redeploy backend
- Test on https://www.factcheck.mx/signin

## Files Already Implemented ✅

- ✅ `backend/app/routers/auth.py` - OAuth routes (`/api/auth/google/login`, `/api/auth/google/callback`)
- ✅ `frontend/src/lib/auth.ts` - `googleLogin()` function
- ✅ `frontend/src/app/signin/page.tsx` - OAuth callback handling
- ✅ CORS configuration in `backend/main.py`

## Common Mistakes to Avoid

1. **Redirect URI mismatch** - Must match EXACTLY between Google Cloud Console and backend `.env`
2. **Missing environment variables** - Backend won't work without `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
3. **Wrong redirect URI** - Must be `/api/auth/google/callback` (not `/auth/google/callback`)
4. **Trailing slashes** - No trailing slashes in redirect URIs
5. **Not restarting backend** - Environment variables require restart

## Verification

### Check if OAuth is configured:
```bash
cd backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('GOOGLE_CLIENT_ID:', 'SET' if os.getenv('GOOGLE_CLIENT_ID') else 'NOT SET')"
```

### Test OAuth endpoint:
```bash
curl -I http://localhost:8000/api/auth/google/login
# Should redirect to Google (302 redirect)
```

## Documentation

- **Full Guide**: `docs/setup/GOOGLE_AUTH_FIX_GUIDE.md`
- **Quick Checklist**: `docs/setup/GOOGLE_AUTH_QUICK_CHECKLIST.md`
- **Original Guide**: `docs/setup/GOOGLE_OAUTH_SETUP.md`

## Need Help?

1. Check the troubleshooting section in `GOOGLE_AUTH_FIX_GUIDE.md`
2. Verify all environment variables are set correctly
3. Check backend logs for OAuth errors
4. Verify redirect URIs match exactly in Google Cloud Console

