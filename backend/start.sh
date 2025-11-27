#!/bin/sh
# Railway startup script
# Railway sets $PORT automatically

PORT=${PORT:-8000}

# Force output to be unbuffered so we see logs immediately
export PYTHONUNBUFFERED=1

echo "=========================================="
echo "Starting FactCheckr API on port ${PORT}..."
echo "=========================================="
echo ""

# Environment check
echo "Environment check:"
echo "PORT=${PORT}"
if [ -n "${DATABASE_URL:-}" ]; then
    echo "DATABASE_URL is set (length: ${#DATABASE_URL})"
else
    echo "DATABASE_URL is NOT SET"
fi
echo ""

# Runtime info
echo "Runtime info:"
python --version 2>&1 || echo "Python check failed"
echo "Working directory: $(pwd)"
echo "Files in current dir:"
ls -la | head -20 || echo "ls failed"
echo ""

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found!"
    echo "Current directory contents:"
    ls -la
    exit 1
fi

# Test if main.py can be imported
echo "Testing app import..."
python -c "import main; print('✅ App module imported successfully')" 2>&1
IMPORT_STATUS=$?
if [ $IMPORT_STATUS -eq 0 ]; then
    echo "✅ App import successful"
else
    echo "❌ Failed to import app module (exit code: $IMPORT_STATUS)"
    echo "Attempting to start anyway..."
fi
echo ""

# Check if alembic is available (non-fatal)
if command -v alembic >/dev/null 2>&1; then
    echo "Running database migrations..."
    alembic upgrade head 2>&1 || echo "⚠️ Migrations failed - continuing with startup..."
else
    echo "⚠️ Alembic not found in PATH - skipping migrations"
fi
echo ""

echo "Starting gunicorn on 0.0.0.0:${PORT}..."
echo "Health check endpoint will be at: http://0.0.0.0:${PORT}/health"
echo ""

# Run gunicorn with error handling and verbose logging
# Use single worker initially for easier debugging
# Note: --preload removed as it can cause issues with uvicorn workers
exec gunicorn main:app \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "0.0.0.0:${PORT}" \
  --timeout 120 \
  --keepalive 5 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --capture-output \
  --enable-stdio-inheritance

