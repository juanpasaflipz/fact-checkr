# Quick Fix: Backend Not Responding

## Problem
Backend process exists but not responding to HTTP requests.

## Solution

### Step 1: Kill the stuck process
```bash
# Find the process
lsof -i:8000

# Kill it (replace PID with actual number)
kill -9 <PID>
```

### Step 2: Start the backend fresh
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### Step 3: Verify it's working
In a new terminal:
```bash
curl http://localhost:8000/health
```

Should return:
```json
{"status":"healthy","database":"connected",...}
```

### Step 4: Refresh your frontend
Go back to your browser and refresh the page. The "Failed to fetch" error should be gone.

## If Backend Still Won't Start

### Check for errors:
```bash
cd backend
source venv/bin/activate
python -c "from main import app; print('Import successful')"
```

### Check database connection:
```bash
cd backend
python test_db_connection.py
```

### Check environment variables:
```bash
cd backend
cat .env | grep -E "DATABASE_URL|CORS_ORIGINS"
```

## Expected Output When Starting

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

If you see errors, check the error messages and fix the issues (usually database connection or missing environment variables).

