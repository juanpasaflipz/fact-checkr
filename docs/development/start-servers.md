# Starting Both Servers

## Quick Start Commands

### Option 1: Manual (Recommended for Development)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 2: Background Script

Create a `start-all.sh` script:
```bash
#!/bin/bash

# Start backend
cd backend
source venv/bin/activate
uvicorn main:app --reload &
BACKEND_PID=$!

# Start frontend
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "Or run: kill $BACKEND_PID $FRONTEND_PID"

wait
```

Make it executable:
```bash
chmod +x start-all.sh
./start-all.sh
```

## Verify Servers Are Running

### Check Backend:
```bash
curl http://localhost:8000/health
```

Should return:
```json
{"status":"healthy","database":"connected","message":"API and database are operational"}
```

### Check Frontend:
Open browser: http://localhost:3000

Or check with curl:
```bash
curl http://localhost:3000
```

### Check Ports:
```bash
lsof -i:8000  # Backend
lsof -i:3000  # Frontend
```

## URLs

- **Backend API**: http://localhost:8000
- **Backend Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

## Stopping Servers

### If running in separate terminals:
- Press `Ctrl+C` in each terminal

### If running in background:
```bash
# Find PIDs
lsof -i:8000
lsof -i:3000

# Kill processes
kill -9 <PID>
```

Or kill all:
```bash
pkill -f "uvicorn main:app"
pkill -f "next dev"
```

## Troubleshooting

### Backend won't start:
1. Check if port 8000 is in use: `lsof -i:8000`
2. Verify `.env` file exists: `ls backend/.env`
3. Check database connection: `cd backend && python test_db_connection.py`

### Frontend won't start:
1. Check if port 3000 is in use: `lsof -i:3000`
2. Install dependencies: `cd frontend && npm install`
3. Check `.env.local`: `ls frontend/.env.local`

### Connection errors:
- Verify `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`
- Check CORS settings in `backend/.env`: `CORS_ORIGINS=http://localhost:3000`
- Restart both servers after changing environment variables

