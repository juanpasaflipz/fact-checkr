# Google OAuth Production Fix Guide

This guide addresses common Google OAuth issues in production based on the architecture analysis.

## Architecture Overview

**Your setup uses Option A: Backend handles OAuth**

This is the correct architecture for your application. The flow is:

1. Frontend (factcheck.mx) → calls `https://backend-production-72ea.up.railway.app/api/auth/google/login`
2. Backend redirects to Google with `redirect_uri=https://backend-production-72ea.up.railway.app/api/auth/google/callback`
3. Google sends user back to backend callback
4. Backend exchanges code for tokens, creates session/JWT, and redirects to `https://factcheck.mx/signin?token=...&success=true`

**Important**: Google never talks directly to the frontend, only to the backend.

## Why Google Shows Backend URL

When you see "to continue to backend-production-72ea.up.railway.app" in Google's consent screen, **this is correct and expected**. Google is telling the user where they'll be redirected after authentication, which is your backend callback URL.

## Google Cloud Console Configuration

### Authorized Redirect URIs

In Google Cloud Console → OAuth 2.0 Client → Authorized redirect URIs, you should have:

**✅ CORRECT (Full paths):**
```
https://backend-production-72ea.up.railway.app/api/auth/google/callback
http://localhost:8000/api/auth/google/callback
```

**❌ INCORRECT (Bare domains - remove these):**
```
https://www.factcheck.mx
https://factcheck.mx
```

**Why?** Google only calls the exact redirect URI you send in the OAuth request. Bare domains are not valid callback paths.

### What to Keep

- ✅ Production backend callback: `https://backend-production-72ea.up.railway.app/api/auth/google/callback`
- ✅ Local development callback: `http://localhost:8000/api/auth/google/callback`
- ❌ Remove any bare domain entries (factcheck.mx, www.factcheck.mx)

## Environment Variables

### Backend (Railway)

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-client-secret
GOOGLE_REDIRECT_URI=https://backend-production-72ea.up.railway.app/api/auth/google/callback

# Frontend URL (where users are redirected after OAuth)
FRONTEND_URL=https://www.factcheck.mx

# CORS (must include frontend domain)
CORS_ORIGINS=https://factcheck.mx,https://www.factcheck.mx,http://localhost:3000
```

**Critical**: `GOOGLE_REDIRECT_URI` must match **exactly** what's in Google Cloud Console (including protocol, domain, and full path).

### Frontend (Vercel)

```bash
NEXT_PUBLIC_API_URL=https://backend-production-72ea.up.railway.app
```

## Common Errors and Solutions

### 1. "redirect_uri_mismatch"

**Cause**: The redirect URI in your code doesn't match what's in Google Cloud Console.

**Fix**:
1. Check `GOOGLE_REDIRECT_URI` in Railway environment variables
2. Verify it matches exactly (character-by-character) in Google Cloud Console
3. No trailing slashes
4. Correct protocol (https for production, http for localhost)
5. Full path including `/api/auth/google/callback`

**Debug**: Check backend logs - the callback handler now logs the configured redirect URI.

### 2. "invalid_client"

**Cause**: Client ID or Secret is incorrect or missing.

**Fix**:
1. Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in Railway
2. Copy from Google Cloud Console (no extra spaces or quotes)
3. Ensure you're using the correct OAuth client (Web application type)
4. Redeploy backend after setting environment variables

### 3. "OAuth error in callback" (console.error)

**Cause**: Error during token exchange or user creation.

**Debug Steps**:
1. Check backend logs - enhanced logging now shows:
   - Query parameters received
   - Redirect URI being used
   - Token exchange response
   - Detailed error messages

2. Common issues:
   - Missing environment variables
   - Database connection errors
   - Invalid token exchange (check redirect_uri matches)

**Enhanced Logging**: The callback handler now logs:
- Full request URL
- All query parameters
- Configured redirect URI
- Token exchange details
- Google API error responses

## Testing the Flow

### 1. Verify Environment Variables

```bash
# Check backend logs on startup
# Should see: "✅ Loaded JWT_SECRET_KEY from environment"
# And no warnings about missing Google OAuth config
```

### 2. Test OAuth Initiation

```bash
# Visit in browser:
https://backend-production-72ea.up.railway.app/api/auth/google/login

# Should redirect to Google login page
```

### 3. Test Callback

After Google redirects back, check backend logs for:
- "Google OAuth callback hit"
- "Query params: code=present, state=present"
- "Configured redirect_uri: ..."
- Token exchange success/failure

### 4. Check Frontend Redirect

After successful OAuth, user should be redirected to:
```
https://www.factcheck.mx/signin?token=...&success=true
```

Frontend should extract token and store it.

## Debugging Checklist

When OAuth fails, check:

- [ ] `GOOGLE_CLIENT_ID` set in Railway
- [ ] `GOOGLE_CLIENT_SECRET` set in Railway
- [ ] `GOOGLE_REDIRECT_URI` matches Google Cloud Console exactly
- [ ] `FRONTEND_URL` set to `https://www.factcheck.mx`
- [ ] Backend redeployed after setting environment variables
- [ ] Google Cloud Console has correct redirect URI
- [ ] No bare domains in Google Cloud Console redirect URIs
- [ ] Backend logs show callback being hit
- [ ] Backend logs show token exchange attempt
- [ ] Check for specific error messages in logs

## Architecture Decision

**Current**: Backend handles OAuth (Option A) ✅

**Alternative**: Frontend handles OAuth (Option B) - Not recommended for your setup

If you wanted to switch to Option B (not recommended):
- Frontend would need to handle OAuth directly
- Callback would be `https://factcheck.mx/api/auth/callback/google`
- Backend would only receive authenticated API calls
- Requires significant refactoring

**Recommendation**: Keep Option A (current setup). It's simpler, more secure, and already working.

## Summary

1. ✅ Backend handling OAuth is correct
2. ✅ Google showing backend URL is normal
3. ✅ Callback should be backend URL, not frontend
4. ✅ Remove bare domains from Google Cloud Console
5. ✅ Ensure `GOOGLE_REDIRECT_URI` matches exactly
6. ✅ Enhanced logging now helps debug issues

## Next Steps

1. Verify environment variables in Railway
2. Clean up Google Cloud Console redirect URIs
3. Test OAuth flow end-to-end
4. Check backend logs for detailed error messages
5. If errors persist, share backend logs for further debugging

