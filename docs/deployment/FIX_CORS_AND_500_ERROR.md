# Fix CORS and 500 Error Issues

## Issues Identified

1. **CORS Error**: Requests from `https://www.factcheck.mx` are being blocked
2. **500 Internal Server Error**: `/claims` endpoint is returning 500 errors

## Solution

### 1. Fix CORS Configuration

The backend CORS configuration includes `https://www.factcheck.mx` in the default origins, but if `CORS_ORIGINS` environment variable is set in Railway, it might be overriding the defaults.

**Action Required in Railway:**

1. Go to Railway Dashboard → Backend Service → Variables
2. Check if `CORS_ORIGINS` is set
3. If it exists, update it to include:
   ```
   http://localhost:3000,http://localhost:3001,https://factcheck.mx,https://www.factcheck.mx,https://fact-checkr-production.up.railway.app,https://fact-checkr.vercel.app,https://fact-checkr-juanpasa.vercel.app
   ```
4. If it doesn't exist, the defaults should work, but you can explicitly set it to be safe
5. **Redeploy** the backend service after updating

### 2. Fix 500 Error on `/claims` Endpoint

The 500 error suggests a database or code issue. Check Railway logs:

**Action Required:**

1. Go to Railway Dashboard → Backend Service → Logs
2. Look for error messages around the time of the 500 errors
3. Common causes:
   - Database connection issues
   - Missing database columns (if migrations weren't run)
   - Code errors in the claims endpoint

**Quick Fix Steps:**

1. **Check Database Connection:**
   ```bash
   # Test database connection
   curl https://backend-production-72ea.up.railway.app/health/detailed
   ```

2. **Check Railway Logs:**
   - Look for Python tracebacks
   - Look for database connection errors
   - Look for import errors

3. **Verify Database Migrations:**
   - Ensure all migrations have been run
   - Check if new columns exist (like `evidence_details`)

### 3. Temporary Workaround

If you need to quickly fix CORS, you can update the Railway environment variable:

**Railway Dashboard → Backend Service → Variables:**

Add or update:
```
CORS_ORIGINS=https://www.factcheck.mx,https://factcheck.mx,http://localhost:3000,https://fact-checkr-production.up.railway.app
```

Then redeploy.

### 4. Verify Fix

After making changes:

1. **Test CORS:**
   ```bash
   curl -H "Origin: https://www.factcheck.mx" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: Content-Type" \
        -X OPTIONS \
        https://backend-production-72ea.up.railway.app/claims
   ```
   Should return CORS headers.

2. **Test Claims Endpoint:**
   ```bash
   curl https://backend-production-72ea.up.railway.app/claims?skip=0&limit=5
   ```
   Should return 200 with JSON data, not 500.

3. **Test from Frontend:**
   - Open browser console on https://www.factcheck.mx
   - Check Network tab
   - Verify requests succeed without CORS errors

## Root Cause Analysis

### CORS Issue
- The code includes `https://www.factcheck.mx` in default origins
- But if `CORS_ORIGINS` env var is set, it overrides defaults
- Solution: Ensure `CORS_ORIGINS` includes the production domain

### 500 Error
- Likely a database query issue or missing migration
- Need to check Railway logs for specific error
- Could be related to recent schema changes (evidence_details column)

## Next Steps

1. ✅ Check Railway logs for specific 500 error
2. ✅ Update CORS_ORIGINS in Railway
3. ✅ Verify database migrations are applied
4. ✅ Test endpoints after fix
5. ✅ Monitor for recurring issues

