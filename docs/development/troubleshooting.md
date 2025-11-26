# Troubleshooting "Failed to fetch" Error

## Problem
Getting `TypeError: Failed to fetch` when trying to load claims from the API.

## Common Causes & Solutions

### 1. Backend Server Not Running

**Check:**
```bash
# Check if backend is running
lsof -i:8000

# Or check process
ps aux | grep uvicorn
```

**Solution:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

The backend should start on `http://localhost:8000`

### 2. Missing Environment Variables

**Check:**
```bash
cd frontend
ls -la .env.local
```

**Solution:**
Create `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Important:** Restart the Next.js dev server after creating/updating `.env.local`:
```bash
# Stop the server (Ctrl+C) and restart
npm run dev
```

### 3. CORS Configuration Issue

**Check backend `.env`:**
```bash
cd backend
cat .env | grep CORS_ORIGINS
```

**Solution:**
Ensure `backend/.env` has:
```bash
CORS_ORIGINS=http://localhost:3000
```

If using a different frontend port, add it:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

**Restart backend** after changing CORS settings.

### 4. Backend Not Responding

**Test backend directly:**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","database":"connected",...}
```

**If curl fails:**
- Backend may have crashed
- Check backend logs: `tail -f backend/backend.log`
- Check for database connection errors
- Verify DATABASE_URL in `backend/.env`

### 5. Port Conflicts

**Check if port 8000 is in use by another process:**
```bash
lsof -i:8000
```

**Solution:**
- Kill the process using port 8000, OR
- Change backend port in `uvicorn main:app --port 8001`
- Update `NEXT_PUBLIC_API_URL=http://localhost:8001` in frontend

### 6. Network/Firewall Issues

**Check:**
- Firewall blocking localhost connections
- VPN interfering with localhost
- Antivirus blocking connections

**Solution:**
- Temporarily disable firewall/antivirus
- Try `127.0.0.1` instead of `localhost`:
  ```bash
  NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
  ```

## Quick Diagnostic Steps

1. **Verify backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check frontend environment:**
   ```bash
   cd frontend
   cat .env.local
   ```

3. **Check backend CORS:**
   ```bash
   cd backend
   cat .env | grep CORS
   ```

4. **Check browser console:**
   - Open DevTools (F12)
   - Check Network tab for failed requests
   - Look for CORS errors (red requests)

5. **Restart both servers:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   source venv/bin/activate
   uvicorn main:app --reload

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

## Expected Behavior

When everything is working:
- Backend: `http://localhost:8000/health` returns JSON
- Frontend: Claims load without errors
- Browser console: No network errors
- Network tab: Requests to `/claims` return 200 OK

## Still Not Working?

1. **Check backend logs:**
   ```bash
   tail -f backend/backend.log
   ```

2. **Check frontend console:**
   - Open browser DevTools
   - Look for detailed error messages

3. **Verify database connection:**
   ```bash
   cd backend
   python test_db_connection.py
   ```

4. **Test API directly:**
   ```bash
   curl http://localhost:8000/claims?skip=0&limit=5
   ```

## Error Message Reference

- **"Failed to fetch"**: Backend not running or unreachable
- **CORS error**: Backend CORS not configured for frontend origin
- **404 Not Found**: Wrong API URL or endpoint
- **500 Internal Server Error**: Backend error (check logs)
- **Database connection error**: DATABASE_URL incorrect or database down

