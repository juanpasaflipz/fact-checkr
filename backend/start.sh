#!/bin/sh
# Railway startup script
# Railway sets $PORT automatically

# Don't exit on error immediately - we want to see what's failing
set -u  # Treat unset vars as error

PORT=${PORT:-8000}

echo "=========================================="
echo "Starting FactCheckr API on port ${PORT}..."
echo "=========================================="

echo "Environment check:"
echo "PORT=${PORT}"
echo "DATABASE_URL=${DATABASE_URL:-NOT SET}"
echo ""

echo "Runtime info:"
python --version || true
pip --version || true
echo "Checking installed packages..."
pip show fastapi uvicorn gunicorn || true

# Test if main.py can be imported
echo ""
echo "Testing app import..."
if python -c "import main; print('✅ App module imported successfully')" 2>&1; then
    echo "✅ App import successful"
else
    echo "❌ Failed to import app module"
    echo "Attempting to start anyway..."
fi

echo ""
echo "Starting gunicorn on 0.0.0.0:${PORT}..."
echo "Health check endpoint: http://0.0.0.0:${PORT}/health"
echo ""

# Run gunicorn with error handling and verbose logging
# --worker-class: Use uvicorn workers for async support
exec gunicorn main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "0.0.0.0:${PORT}" \
  --timeout 120 \
  --keepalive 5 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --capture-output \
  --enable-stdio-inheritance

