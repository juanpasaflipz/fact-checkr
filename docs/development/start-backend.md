# Starting the Backend Server

## Quick Start

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

The server will start on `http://localhost:8000`

## Verify It's Running

```bash
curl http://localhost:8000/health
```

Should return:
```json
{"status":"healthy","database":"connected","message":"API and database are operational"}
```

## Common Issues

### Port Already in Use
If port 8000 is already in use:
```bash
# Find what's using port 8000
lsof -i:8000

# Kill the process (replace PID with actual process ID)
kill -9 <PID>

# Or use a different port
uvicorn main:app --reload --port 8001
```

### Database Connection Error
Make sure your `backend/.env` file has the correct `DATABASE_URL`:
```bash
cat backend/.env | grep DATABASE_URL
```

### Missing Dependencies
If you get import errors:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

## Running in Background (Optional)

If you want to run the backend in the background:
```bash
cd backend
source venv/bin/activate
nohup uvicorn main:app --reload > backend.log 2>&1 &
```

To stop it:
```bash
pkill -f "uvicorn main:app"
```

## Development vs Production

**Development** (with auto-reload):
```bash
uvicorn main:app --reload
```

**Production** (no reload, multiple workers):
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

