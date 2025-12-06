# Google OAuth HAR Analysis - Issues Found and Fixed

## Issues Identified from HAR File

### 1. ❌ Invalid State Error

**Problem**: The OAuth callback receives a valid `code` and `state` from Google, but the backend returns `invalid_state` error.

**Root Cause**: 
- OAuth states were stored in an in-memory dictionary (`oauth_states = {}`)
- In production with multiple workers/instances, the state might be created on one instance but validated on another
- If the backend restarts, all in-memory states are lost
- States expire after 10 minutes, but the validation wasn't working correctly

**Evidence from HAR**:
```
Request: GET /api/auth/google/callback?state=WGhsubTopkUbihHKD-9-lu23eFirWukJ_gdumu4BNAk&code=4/0Ab32j935Bms5_...
Response: 307 Redirect to https://wwww.factcheck.com/signin?error=invalid_state
```

### 2. ❌ Wrong FRONTEND_URL Configuration

**Problem**: The redirect URL shows `https://wwww.factcheck.com` (4 w's) instead of the correct domain.

**Root Cause**: 
- `FRONTEND_URL` environment variable in Railway is misconfigured
- Should be `https://www.factcheck.mx` or `https://factcheck.mx`

**Evidence from HAR**:
```
Location: https://wwww.factcheck.com/signin?error=invalid_state
```

## Fixes Applied

### 1. ✅ Redis-Based State Storage

**Changed**: OAuth state storage now uses Redis instead of in-memory dictionary.

**Benefits**:
- States persist across backend restarts
- Works with multiple worker instances
- Automatic expiration (10 minutes)
- More reliable for production

**Implementation**:
- Uses existing `REDIS_URL` environment variable
- Falls back to in-memory storage if Redis unavailable
- States stored with key: `oauth_state:{state}` with 10-minute TTL

### 2. ✅ Enhanced State Validation

**Changed**: Improved state validation with better error logging.

**Features**:
- Checks Redis first, then in-memory fallback
- Better logging to debug state issues
- Logs available states count for debugging
- One-time use: state is deleted immediately after validation

### 3. ✅ FRONTEND_URL Validation

**Changed**: Added validation to catch common typos in `FRONTEND_URL`.

**Checks**:
- Validates URL format (must start with http:// or https://)
- Detects common typos like "wwww" (4 w's)
- Warns if using .com instead of .mx domain
- Logs errors on startup

### 4. ✅ Enhanced Error Logging

**Changed**: Improved logging throughout the OAuth callback handler.

**New Logging**:
- Logs state storage method (Redis vs memory)
- Logs state lookup results
- Logs available states count
- Better error messages for debugging

## Required Actions

### 1. Fix FRONTEND_URL in Railway

**In Railway Environment Variables**, update:

```bash
# WRONG (current):
FRONTEND_URL=https://wwww.factcheck.com

# CORRECT:
FRONTEND_URL=https://www.factcheck.mx
```

Or if you prefer without www:
```bash
FRONTEND_URL=https://factcheck.mx
```

**Important**: Make sure there are no typos. The validation will now catch this on startup.

### 2. Verify Redis is Available

The code will automatically use Redis if available. Verify:

1. **Check Railway Environment Variables**:
   ```bash
   REDIS_URL=redis://your-redis-host:6379/0
   ```

2. **Check Backend Logs** on startup:
   - Should see: `✅ Using Redis for OAuth state storage`
   - If you see: `⚠️ Redis not available`, check your `REDIS_URL`

### 3. Redeploy Backend

After fixing `FRONTEND_URL`:
1. Update the environment variable in Railway
2. Redeploy the backend
3. Check startup logs for validation messages

## Testing

### 1. Verify Configuration

After redeploy, check backend logs for:
```
✅ Google OAuth configured
   Client ID: 1094246951103-f6aq...
   Redirect URI: https://backend-production-72ea.up.railway.app/api/auth/google/callback
   Frontend URL: https://www.factcheck.mx
✅ Using Redis for OAuth state storage
```

**If you see errors**:
- `❌ FRONTEND_URL appears to have a typo` → Fix the environment variable
- `⚠️ Redis not available` → Check `REDIS_URL` configuration

### 2. Test OAuth Flow

1. Visit `https://www.factcheck.mx/signin`
2. Click "Continuar con Google"
3. Complete Google authentication
4. Should redirect back to `https://www.factcheck.mx/signin?token=...&success=true`

### 3. Check Backend Logs

During OAuth flow, you should see:
```
Google OAuth callback hit
Query params: code=present, state=present
OAuth state found in Redis: WGhsubTopk...
Exchanging authorization code for tokens...
Successfully exchanged code for access token
JWT token created for user X
Redirecting to frontend: https://www.factcheck.mx/signin
```

## Expected Behavior After Fix

1. ✅ State validation works across instances
2. ✅ States persist after backend restarts
3. ✅ Redirect goes to correct frontend URL
4. ✅ Better error messages if something fails
5. ✅ Automatic detection of configuration issues

## Troubleshooting

### Still Getting "invalid_state" Error?

1. **Check Redis connection**:
   - Verify `REDIS_URL` is correct
   - Check if Redis is accessible from backend
   - Look for Redis connection errors in logs

2. **Check state expiration**:
   - States expire after 10 minutes
   - If you wait too long between clicking "Sign in" and completing Google auth, state will expire
   - Try the flow again quickly

3. **Check logs**:
   - Look for "OAuth state found in Redis" or "OAuth state found in memory"
   - Check "Available states in Redis" count
   - If count is 0, states might be expiring too quickly

### Still Redirecting to Wrong URL?

1. **Verify FRONTEND_URL**:
   ```bash
   # In Railway, check environment variable
   FRONTEND_URL=https://www.factcheck.mx
   ```

2. **Check startup logs**:
   - Should see validation message if URL is wrong
   - Look for warnings about URL format

3. **Redeploy after fixing**:
   - Environment variable changes require redeploy
   - Check logs after redeploy to confirm

## Summary

The main issues were:
1. **In-memory state storage** → Fixed with Redis
2. **Wrong FRONTEND_URL** → Needs manual fix in Railway

After fixing `FRONTEND_URL` and redeploying, OAuth should work correctly with:
- Persistent state storage (Redis)
- Correct redirect URLs
- Better error handling and logging

