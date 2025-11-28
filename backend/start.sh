#!/bin/sh
# Railway startup script - Clean version
# Railway automatically sets $PORT at runtime

set -e  # Exit on any error
set -x  # Show commands as they execute

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

# Ensure we're in /app (where Dockerfile sets WORKDIR)
cd /app
echo "Working directory: $(pwd)"

# Verify main.py exists
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found in /app!"
    ls -la /app
    exit 1
fi

# Run migrations if alembic is available (non-blocking)
if command -v alembic >/dev/null 2>&1; then
    echo "Running database migrations..."
    alembic upgrade head || echo "⚠️ Migration warning (continuing)..."
else
    echo "Alembic not found, skipping migrations"
fi

echo ""
echo "Starting Gunicorn..."
echo ""

# Start Gunicorn
# Railway will route traffic to this port automatically
exec gunicorn main:app \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
