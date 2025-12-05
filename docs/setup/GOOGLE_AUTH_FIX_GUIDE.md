# Google OAuth Setup & Fix Guide

Complete step-by-step guide to make Google authentication functional for both localhost and production (https://www.factcheck.mx).

## Quick Checklist

- [ ] Google Cloud Console OAuth client created
- [ ] Redirect URIs added to Google Cloud Console
- [ ] Backend environment variables configured
- [ ] Frontend environment variables configured (if needed)
- [ ] CORS configured correctly
- [ ] Tested on localhost
- [ ] Tested on production

---

## Part 1: Google Cloud Console Setup

### Step 1: Create/Select Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project or create a new one
3. Make sure billing is enabled (required for OAuth)

### Step 2: Configure OAuth Consent Screen

1. Navigate to **APIs & Services > OAuth consent screen**
2. Choose **External** (unless you have Google Workspace)
3. Fill in required fields:
   - **App name**: `FactCheckr MX`
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. Click **Save and Continue**
5. **Scopes** (Step 2): Click **Save and Continue** (default scopes are fine)
6. **Test users** (Step 3): 
   - If in testing mode, add your email as a test user
   - Or publish the app for production use
7. Click **Save and Continue**

### Step 3: Create OAuth 2.0 Client ID

1. Navigate to **APIs & Services > Credentials**
2. Click **+ CREATE CREDENTIALS > OAuth client ID**
3. Select **Web application** as application type
4. **Name**: `FactCheckr MX` (or any name)
5. **Authorized redirect URIs**: Add BOTH of these:
   ```
   http://localhost:8000/api/auth/google/callback
   https://backend-production-72ea.up.railway.app/api/auth/google/callback
   ```
   > **Note**: Replace `backend-production-72ea.up.railway.app` with your actual backend domain if different
6. Click **Create**
7. **IMPORTANT**: Copy both values:
   - **Client ID** (looks like: `123456789-abc123def456.apps.googleusercontent.com`)
   - **Client Secret** (looks like: `GOCSPX-abc123def456xyz789`)

---

## Part 2: Backend Configuration

### Step 1: Add Environment Variables

Add these to your `backend/.env` file:

#### For Local Development:
```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id-from-google-cloud.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-client-secret-from-google-cloud
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# Frontend URL (for redirects after OAuth)
FRONTEND_URL=http://localhost:3000

# CORS Origins (should include frontend URL)
CORS_ORIGINS=http://localhost:3000,https://factcheck.mx,https://www.factcheck.mx
```

#### For Production (Railway/Backend Hosting):
```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id-from-google-cloud.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-client-secret-from-google-cloud
GOOGLE_REDIRECT_URI=https://backend-production-72ea.up.railway.app/api/auth/google/callback

# Frontend URL (for redirects after OAuth)
FRONTEND_URL=https://www.factcheck.mx

# CORS Origins (should include frontend URL)
CORS_ORIGINS=https://factcheck.mx,https://www.factcheck.mx,http://localhost:3000
```

> **Important**: 
> - Replace `backend-production-72ea.up.railway.app` with your actual backend domain
> - The `GOOGLE_REDIRECT_URI` must match EXACTLY what you entered in Google Cloud Console
> - No trailing slashes, no extra spaces

### Step 2: Verify Backend Routes

The backend routes should already be set up at:
- `/api/auth/google/login` - Initiates OAuth flow
- `/api/auth/google/callback` - Handles OAuth callback

These are already implemented in `backend/app/routers/auth.py`.

### Step 3: Restart Backend

After adding environment variables:
```bash
cd backend
# Stop the server (Ctrl+C if running)
# Then restart
uvicorn main:app --reload
# Or use your startup script
```

---

## Part 3: Frontend Configuration

### Step 1: Verify API URL Configuration

Check `frontend/.env.local` (or Vercel environment variables):

#### For Local Development:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### For Production (Vercel):
```bash
NEXT_PUBLIC_API_URL=https://backend-production-72ea.up.railway.app
```

> **Note**: The frontend automatically detects the backend URL, but setting `NEXT_PUBLIC_API_URL` explicitly is recommended.

### Step 2: Verify Frontend Code

The frontend code is already set up correctly:
- `frontend/src/lib/auth.ts` - Contains `googleLogin()` function
- `frontend/src/app/signin/page.tsx` - Handles OAuth callback

No changes needed unless you want to customize the flow.

---

## Part 4: Testing

### Test on Localhost

1. **Start Backend**:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
   Verify it's running: `curl http://localhost:8000/health`

2. **Start Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test OAuth Flow**:
   - Navigate to `http://localhost:3000/signin`
   - Click "Continuar con Google"
   - You should be redirected to Google login
   - After login, you should be redirected back to `/signin?token=...&success=true`
   - You should be automatically logged in and redirected to `/subscription`

### Test on Production

1. **Verify Environment Variables**:
   - Check Railway backend environment variables
   - Check Vercel frontend environment variables

2. **Test OAuth Flow**:
   - Navigate to `https://www.factcheck.mx/signin`
   - Click "Continuar con Google"
   - You should be redirected to Google login
   - After login, you should be redirected back and logged in

---

## Part 5: Troubleshooting

### Error: "redirect_uri_mismatch"

**Problem**: The redirect URI doesn't match what's in Google Cloud Console.

**Solution**:
1. Check `GOOGLE_REDIRECT_URI` in `backend/.env`
2. Verify it matches EXACTLY in Google Cloud Console (APIs & Services > Credentials > Your OAuth Client)
3. Make sure there are no trailing slashes or extra spaces
4. Restart backend after making changes

**Common mistakes**:
- `http://localhost:8000/api/auth/google/callback/` (trailing slash) ❌
- `http://localhost:8000/api/auth/google/callback` ✅
- Extra spaces in the URI ❌

### Error: "invalid_client"

**Problem**: Client ID or Client Secret is incorrect.

**Solution**:
1. Double-check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `backend/.env`
2. Make sure you copied the full values (no truncation)
3. Verify they're from the correct OAuth client in Google Cloud Console
4. Make sure there are no extra spaces or quotes around the values

### Error: "access_denied"

**Problem**: User cancelled the OAuth flow or app is in testing mode without test users.

**Solution**:
1. If in testing mode, add your email as a test user in OAuth consent screen
2. Or publish your app (for production use)

### Error: "oauth_not_configured"

**Problem**: Backend environment variables are missing or empty.

**Solution**:
1. Check that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in `backend/.env`
2. Restart backend after adding variables
3. Verify variables are loaded: Check backend logs on startup

### Error: OAuth works but user isn't logged in

**Problem**: Frontend isn't handling the callback correctly.

**Solution**:
1. Check browser console for errors
2. Verify `handleOAuthCallback()` is being called in `signin/page.tsx`
3. Check that token is being stored in localStorage
4. Verify `FRONTEND_URL` in backend matches your frontend domain

### CORS Errors

**Problem**: Browser blocks requests due to CORS policy.

**Solution**:
1. Verify `CORS_ORIGINS` in backend includes your frontend URL
2. Check backend logs to see which origins are allowed
3. For production, make sure both `https://factcheck.mx` and `https://www.factcheck.mx` are in `CORS_ORIGINS`

---

## Part 6: Production Deployment Checklist

### Railway (Backend)

- [ ] `GOOGLE_CLIENT_ID` is set
- [ ] `GOOGLE_CLIENT_SECRET` is set
- [ ] `GOOGLE_REDIRECT_URI` is set to production backend URL
- [ ] `FRONTEND_URL` is set to `https://www.factcheck.mx`
- [ ] `CORS_ORIGINS` includes `https://factcheck.mx` and `https://www.factcheck.mx`
- [ ] Backend is restarted after adding variables

### Vercel (Frontend)

- [ ] `NEXT_PUBLIC_API_URL` is set to production backend URL
- [ ] Frontend is redeployed after adding variables

### Google Cloud Console

- [ ] Production redirect URI is added: `https://your-backend-domain.com/api/auth/google/callback`
- [ ] OAuth consent screen is published (or test users are added)
- [ ] Client ID and Secret are from the correct OAuth client

---

## Quick Reference

### Redirect URI Format
```
{backend-url}/api/auth/google/callback
```

### Local Development
```
http://localhost:8000/api/auth/google/callback
```

### Production
```
https://backend-production-72ea.up.railway.app/api/auth/google/callback
```

### Required Environment Variables

**Backend:**
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `FRONTEND_URL`
- `CORS_ORIGINS` (optional, has defaults)

**Frontend:**
- `NEXT_PUBLIC_API_URL` (optional, auto-detected)

---

## Still Having Issues?

1. **Check Backend Logs**: Look for OAuth-related errors
2. **Check Browser Console**: Look for JavaScript errors
3. **Verify Network Tab**: Check if OAuth requests are being made
4. **Test Backend Directly**: 
   ```bash
   curl http://localhost:8000/api/auth/google/login
   # Should redirect to Google
   ```
5. **Verify Google Cloud Console**: Double-check all settings match this guide

---

## Security Notes

- **Never commit** `.env` files with real credentials
- Use different OAuth clients for development and production if possible
- Keep your Client Secret secure
- Regularly rotate credentials if compromised
- The OAuth state parameter provides CSRF protection (already implemented)

