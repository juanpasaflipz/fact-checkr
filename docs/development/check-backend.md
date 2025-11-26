# Checking Backend Status

## Quick Check Commands

### 1. Check if backend is responding:
```bash
curl http://localhost:8000/health
```

Should return:
```json
{"status":"healthy","database":"connected","message":"API and database are operational"}
```

### 2. Check if process is running:
```bash
lsof -i:8000
```

Should show Python/uvicorn process.

### 3. Check process details:
```bash
ps aux | grep uvicorn | grep -v grep
```

### 4. Test API endpoint:
```bash
curl http://localhost:8000/claims?skip=0&limit=1
```

## If Backend is Not Responding

### Restart Backend:
```bash
# Kill existing process
pkill -f "uvicorn main:app"

# Start fresh
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### Check for Errors:
```bash
# Check backend logs
tail -f backend/backend.log

# Or if running in terminal, check for error messages
```

### Common Issues:

1. **Port already in use:**
   ```bash
   lsof -i:8000
   kill -9 <PID>
   ```

2. **Database connection error:**
   - Check `backend/.env` has correct `DATABASE_URL`
   - Test: `cd backend && python test_db_connection.py`

3. **Missing dependencies:**
   ```bash
   cd backend
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Import errors:**
   ```bash
   cd backend
   source venv/bin/activate
   python -c "from main import app; print('OK')"
   ```

## Frontend Connection Issues

If backend is running but frontend can't connect:

1. **Check CORS:**
   ```bash
   # In backend/.env
   CORS_ORIGINS=http://localhost:3000
   ```

2. **Check frontend API URL:**
   ```bash
   # In frontend/.env.local
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Restart frontend after changing .env.local:**
   ```bash
   # Stop and restart
   cd frontend
   npm run dev
   ```

