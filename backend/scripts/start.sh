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
try:
    print('Testing main.py import...')
    import main
    print('✅ main.py imported successfully')
    print(f'✅ FastAPI app: {main.app}')
except Exception as e:
    print(f'❌ Failed to import main.py: {e}')
    traceback.print_exc()
    sys.exit(1)
"; then
    error_exit "Failed to import main.py - cannot start server"
fi

echo ""
echo "Starting Gunicorn..."
echo ""

# Start Gunicorn (foreground process for Railway)
echo "=========================================="
echo "Starting Gunicorn server..."
echo "Binding to: 0.0.0.0:${PORT}"
echo "=========================================="

# Use exec to replace shell process (important for Railway)
# This ensures Railway can properly monitor the process
exec gunicorn main:app \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    --preload
