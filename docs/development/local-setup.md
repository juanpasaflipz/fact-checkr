# Local Development Setup

Guide for running FactCheckr MX locally.

## Prerequisites

1. **PostgreSQL** - Database must be running
2. **Redis** - Required for Celery workers (message broker)
3. **Environment Variables** - Ensure `.env` files are configured

---

## Quick Start (All Services)

### Option 1: Start Everything Manually

Open **3 separate terminal windows/tabs**:

#### Terminal 1: Backend API
```bash
cd /Users/juan/fact-checkr/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2: Frontend
```bash
cd /Users/juan/fact-checkr/frontend
pnpm dev
# or if using npm: npm run dev
# or if using yarn: yarn dev
```

#### Terminal 3: Background Workers (Celery)
```bash
cd /Users/juan/fact-checkr/backend
source venv/bin/activate
./start_workers.sh
# OR manually:
# celery -A app.worker worker --beat --loglevel=info
```

---

## Detailed Setup

### Step 1: Start Backend API

```bash
# Navigate to backend directory
cd /Users/juan/fact-checkr/backend

# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify Backend:**
- Open browser: http://localhost:8000
- Should see: `{"message": "Fact Checkr API is running (Database Backed)"}`
- Health check: http://localhost:8000/health

---

### Step 2: Start Frontend

```bash
# Navigate to frontend directory
cd /Users/juan/fact-checkr/frontend

# Install dependencies (if not already done)
pnpm install
# OR: npm install
# OR: yarn install

# Start Next.js development server
pnpm dev
# OR: npm run dev
# OR: yarn dev
```

**Expected Output:**
```
▲ Next.js 16.x.x
- Local:        http://localhost:3000
- Ready in X.XXs
```

**Verify Frontend:**
- Open browser: http://localhost:3000
- Should see the FactCheckr dashboard

---

### Step 3: Start Background Workers (Optional but Recommended)

Background workers handle:
- Automatic scraping every hour
- Async fact-checking of claims
- Processing queued tasks

```bash
# Navigate to backend directory
cd /Users/juan/fact-checkr/backend

# Activate virtual environment
source venv/bin/activate

# Start workers using the script
./start_workers.sh

# OR start manually:
celery -A app.worker worker --beat --loglevel=info
```

**Expected Output:**
```
celery@hostname v5.x.x (singularity)

[config]
.> app:         factcheckr_worker:0x...
.> transport:   redis://localhost:6379/0
.> results:     redis://localhost:6379/0
.> concurrency: 2 (prefork)

[tasks]
  . app.tasks.fact_check.process_source
  . app.tasks.scraper.scrape_all_sources

[beat] beat: Starting...
```

**Verify Workers:**
- Check Redis is running: `redis-cli ping` (should return `PONG`)
- Workers will automatically start scraping every hour

---

## Verify Everything is Running

### Check Backend
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "message": "API and database are operational"
}
```

### Check Frontend
- Open http://localhost:3000 in browser
- Dashboard should load with stats cards

### Check Workers
- Look for Celery logs showing task execution
- Check Redis: `redis-cli keys "*"` (should show task keys)

---

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
# OR use different port:
uvicorn main:app --reload --port 8001
```

**Database connection error:**
- Verify PostgreSQL is running: `pg_isready`
- Check `DATABASE_URL` in `.env` file
- Ensure database exists: `psql -l | grep factcheckr`

**Module not found errors:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Issues

**Port 3000 already in use:**
```bash
# Find and kill process
lsof -ti:3000 | xargs kill -9
# OR use different port:
pnpm dev --port 3001
```

**API connection errors:**
- Verify backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local`
- Default: `http://localhost:8000`

**Build errors:**
```bash
cd frontend
rm -rf .next node_modules
pnpm install
pnpm dev
```

### Worker Issues

**Redis not running:**
```bash
# Start Redis (macOS with Homebrew)
brew services start redis

# OR start manually
redis-server
```

**Worker not starting:**
- Check Redis connection: `redis-cli ping`
- Verify `REDIS_URL` in `.env`
- Check Celery logs for errors

**No tasks executing:**
- Verify beat scheduler is running (should see `[beat]` in logs)
- Check task schedule in `backend/app/worker.py`

---

## Service URLs

Once everything is running:

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Stats Endpoint**: http://localhost:8000/stats

---

## Quick Verification Script

Run this to check all services:

```bash
# Check backend
curl -s http://localhost:8000/health | grep -q "healthy" && echo "✓ Backend OK" || echo "✗ Backend DOWN"

# Check frontend
curl -s http://localhost:3000 | grep -q "html" && echo "✓ Frontend OK" || echo "✗ Frontend DOWN"

# Check Redis
redis-cli ping | grep -q "PONG" && echo "✓ Redis OK" || echo "✗ Redis DOWN"

# Check workers
ps aux | grep -q "[c]elery.*worker" && echo "✓ Workers OK" || echo "✗ Workers DOWN"
```

---

## Using Docker Compose (Alternative)

For a simpler setup, use Docker Compose:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

See [Deployment Guide](../deployment/production.md) for Docker setup details.

