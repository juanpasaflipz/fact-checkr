#!/bin/sh
# Railway startup script - Clean version
# Railway automatically sets $PORT at runtime

set -x  # Show commands as they execute
# Don't use set -e - we handle errors explicitly with error_exit()

# Function to log errors and exit
error_exit() {
    echo "ERROR: $1" >&2
    exit 1
}

# Immediate output for Railway logs
echo "=========================================="
echo "🚀 Starting FactCheckr Backend"
echo "Time: $(date)"
echo "=========================================="

# Unbuffer Python output
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Get port (Railway sets this automatically)
PORT=${PORT:-8000}
echo "Listening on port: ${PORT}"
echo "PORT environment variable: ${PORT}"

# Ensure we're in /app (where Dockerfile sets WORKDIR)
cd /app || {
    echo "ERROR: Failed to cd to /app"
    exit 1
}
echo "Working directory: $(pwd)"
echo "Contents of /app:"
ls -la /app | head -20

# Verify main.py exists
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found in /app!"
    echo "Full directory listing:"
    ls -la /app
    exit 1
fi
echo "✅ main.py found"

# Run migrations in background (non-blocking) so app can start quickly
if command -v alembic >/dev/null 2>&1; then
    echo "Running database migrations in background..."
    (alembic upgrade head || echo "⚠️ Migration warning (continuing)...") &
    MIGRATION_PID=$!
    echo "Migration process started (PID: $MIGRATION_PID)"
else
    echo "⚠️ Alembic not found, skipping migrations"
fi

echo ""
echo "Testing Python import..."
echo ""

# Test if main.py can be imported (catch errors early)
echo "Testing Python import of main.py..."
if ! python -c "
import sys
import traceback
import os
# Set minimal env for testing
os.environ.setdefault('DATABASE_URL', 'postgresql://localhost/test')
try:
    print('Testing main.py import...')
    import main
    print('✅ main.py imported successfully')
    print(f'✅ FastAPI app: {main.app}')
    # Test that health endpoint exists
    routes = [route.path for route in main.app.routes]
    if '/health' in routes:
        print('✅ /health endpoint registered')
    else:
        print(f'⚠️ /health not found in routes: {routes}')
except Exception as e:
    print(f'❌ Failed to import main.py: {e}')
    traceback.print_exc()
    sys.exit(1)
"; then
    error_exit "Failed to import main.py - cannot start server"
fi

echo ""
echo "✅ All startup checks passed"
echo ""

echo ""
echo "Starting Gunicorn..."
echo ""

# Start Gunicorn (foreground process for Railway)
echo "=========================================="
echo "Starting Gunicorn server..."
echo "Binding to: 0.0.0.0:${PORT}"
echo "=========================================="

# Try uvicorn first (simpler, better for Railway), fallback to gunicorn
if command -v uvicorn >/dev/null 2>&1; then
    echo "✅ Using uvicorn (found at: $(which uvicorn))"
    echo "✅ Starting server on 0.0.0.0:${PORT}"
    echo "✅ Server will be available at http://0.0.0.0:${PORT}/health"
    # Use uvicorn directly - simpler and works better with Railway
    # Don't use --no-access-log so we can see requests in logs
    # Try uvloop if available, otherwise use default
    if python -c "import uvloop" 2>/dev/null; then
        echo "✅ Using uvloop for better performance"
        exec uvicorn main:app \
            --host 0.0.0.0 \
            --port "${PORT}" \
            --log-level info \
            --timeout-keep-alive 5 \
            --loop uvloop
    else
        echo "⚠️ uvloop not available, using default event loop"
        exec uvicorn main:app \
            --host 0.0.0.0 \
            --port "${PORT}" \
            --log-level info \
            --timeout-keep-alive 5
    fi
elif command -v gunicorn >/dev/null 2>&1; then
    echo "✅ Using gunicorn (found at: $(which gunicorn))"
    echo "✅ Starting server on 0.0.0.0:${PORT}"
    # Fallback to gunicorn if uvicorn not available
    exec gunicorn main:app \
        --workers 1 \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind "0.0.0.0:${PORT}" \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        --capture-output \
        --graceful-timeout 30 \
        --keep-alive 5
else
    error_exit "Neither uvicorn nor gunicorn found - cannot start server"
fi
