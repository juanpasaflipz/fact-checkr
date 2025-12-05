# Google OAuth Quick Checklist

Use this checklist to quickly verify your Google OAuth setup.

## ✅ Google Cloud Console

- [ ] OAuth consent screen configured (External, app name, emails)
- [ ] OAuth 2.0 Client ID created (Web application)
- [ ] Redirect URI added: `http://localhost:8000/api/auth/google/callback`
- [ ] Redirect URI added: `https://your-backend-domain.com/api/auth/google/callback`
- [ ] Client ID copied (looks like: `123456789-abc.apps.googleusercontent.com`)
- [ ] Client Secret copied (looks like: `GOCSPX-abc123...`)
- [ ] Test users added (if in testing mode) OR app published

## ✅ Backend Environment Variables (Local)

Add to `backend/.env`:
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
FRONTEND_URL=http://localhost:3000
```

- [ ] `GOOGLE_CLIENT_ID` set
- [ ] `GOOGLE_CLIENT_SECRET` set
- [ ] `GOOGLE_REDIRECT_URI` matches Google Cloud Console exactly
- [ ] `FRONTEND_URL` set to `http://localhost:3000`
- [ ] Backend restarted after adding variables

## ✅ Backend Environment Variables (Production - Railway)

Add to Railway environment variables:
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-client-secret
GOOGLE_REDIRECT_URI=https://your-backend-domain.com/api/auth/google/callback
FRONTEND_URL=https://www.factcheck.mx
CORS_ORIGINS=https://factcheck.mx,https://www.factcheck.mx,http://localhost:3000
```

- [ ] `GOOGLE_CLIENT_ID` set in Railway
- [ ] `GOOGLE_CLIENT_SECRET` set in Railway
- [ ] `GOOGLE_REDIRECT_URI` matches Google Cloud Console exactly
- [ ] `FRONTEND_URL` set to `https://www.factcheck.mx`
- [ ] `CORS_ORIGINS` includes frontend domains
- [ ] Backend redeployed after adding variables

## ✅ Frontend Environment Variables (Production - Vercel)

Add to Vercel environment variables:
```bash
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
```

- [ ] `NEXT_PUBLIC_API_URL` set to production backend URL
- [ ] Frontend redeployed after adding variables

## ✅ Testing

### Localhost
- [ ] Backend running: `curl http://localhost:8000/health`
- [ ] Frontend running: `http://localhost:3000`
- [ ] Click "Continuar con Google" on signin page
- [ ] Redirected to Google login
- [ ] After login, redirected back and logged in

### Production
- [ ] Visit `https://www.factcheck.mx/signin`
- [ ] Click "Continuar con Google"
- [ ] Redirected to Google login
- [ ] After login, redirected back and logged in

## 🔍 Common Issues

### "redirect_uri_mismatch"
- [ ] Check `GOOGLE_REDIRECT_URI` matches Google Cloud Console exactly
- [ ] No trailing slashes
- [ ] No extra spaces

### "invalid_client"
- [ ] Client ID and Secret copied correctly
- [ ] No extra spaces or quotes
- [ ] From correct OAuth client

### "oauth_not_configured"
- [ ] Environment variables set in backend
- [ ] Backend restarted after adding variables

### CORS errors
- [ ] `CORS_ORIGINS` includes frontend URL
- [ ] Backend CORS middleware configured

## 📝 Quick Commands

### Check Backend Environment Variables
```bash
cd backend
cat .env | grep GOOGLE
```

### Test Backend OAuth Endpoint
```bash
curl -I http://localhost:8000/api/auth/google/login
# Should redirect to Google
```

### Check Backend Health
```bash
curl http://localhost:8000/health
```

---

**Full Guide**: See `GOOGLE_AUTH_FIX_GUIDE.md` for detailed instructions.

