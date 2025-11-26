# Backend & Frontend Connection Fix

## ✅ Current Status

**Backend:** ✅ Running on http://localhost:8000  
**Frontend:** ✅ Running on http://localhost:3000  
**CORS:** ✅ Configured  
**API Endpoint:** ✅ Working (tested `/claims`)

## What Was Fixed

1. ✅ Started backend server (was not running)
2. ✅ Created `backend_manager.sh` for easy management
3. ✅ Created `frontend/.env.local` with API URL
4. ✅ Fixed CORS configuration in backend `.env`
5. ✅ Verified API endpoints are responding

## Quick Start Commands

### Backend Management
```bash
cd backend

# Start backend
./backend_manager.sh start

# Check status
./backend_manager.sh status

# View logs
./backend_manager.sh logs

# Stop backend
./backend_manager.sh stop
```

### Frontend
The frontend should automatically pick up the `.env.local` file. If you're still seeing errors:

1. **Restart the frontend dev server:**
   ```bash
   cd frontend
   # Stop current server (Ctrl+C)
   npm run dev
   ```

2. **Hard refresh browser:**
   - Chrome/Edge: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
   - Firefox: `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)

3. **Clear browser cache** if issues persist

## Verification

### Test Backend
```bash
# Health check
curl http://localhost:8000/health

# Test claims endpoint
curl 'http://localhost:8000/claims?skip=0&limit=5'
```

### Test Frontend Connection
Open browser console and check:
- No CORS errors
- Network requests to `http://localhost:8000` succeed
- API responses are received

## Troubleshooting

### Error: "Network error - Backend may not be running"

**Check:**
1. Backend is running:
   ```bash
   cd backend && ./backend_manager.sh status
   ```

2. Backend is accessible:
   ```bash
   curl http://localhost:8000/health
   ```

3. Frontend `.env.local` exists:
   ```bash
   cd frontend && cat .env.local
   # Should show: NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. CORS is configured:
   ```bash
   cd backend && grep CORS_ORIGINS .env
   # Should show: CORS_ORIGINS=http://localhost:3000
   ```

### If Backend Won't Start

1. **Check port 8000:**
   ```bash
   lsof -i :8000
   # Kill any processes if needed
   lsof -ti :8000 | xargs kill -9
   ```

2. **Check logs:**
   ```bash
   cd backend
   tail -50 backend.log
   ```

3. **Restart backend:**
   ```bash
   ./backend_manager.sh restart
   ```

### If Frontend Still Can't Connect

1. **Verify environment variable:**
   ```bash
   cd frontend
   # .env.local should exist with:
   # NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

2. **Restart frontend:**
   - Stop the dev server
   - Delete `.next` folder: `rm -rf .next`
   - Restart: `npm run dev`

3. **Check browser console:**
   - Look for actual error messages
   - Check Network tab for failed requests
   - Verify request URL is `http://localhost:8000`

## Configuration Files

### Backend `.env`
```bash
CORS_ORIGINS=http://localhost:3000
DATABASE_URL=your_database_url
# ... other variables
```

### Frontend `.env.local`
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Next Steps

1. ✅ Backend is running
2. ✅ Frontend has `.env.local` configured
3. ⏳ **Restart frontend dev server** to pick up changes
4. ⏳ **Hard refresh browser** to clear cache
5. ⏳ Verify connection works

---

**If issues persist after restarting frontend and hard refreshing browser, check:**
- Browser console for specific error messages
- Network tab in browser dev tools
- Backend logs: `tail -f backend/backend.log`

