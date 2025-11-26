#!/bin/bash
# Railway startup script
# Railway sets $PORT automatically

set -e  # Exit on error

PORT=${PORT:-8000}

echo "=========================================="
echo "Starting FactCheckr API on port ${PORT}..."
echo "=========================================="

# Test if main.py can be imported
echo "Testing app import..."
python -c "import main; print('✅ App module imported successfully')" || {
    echo "❌ Failed to import app module"
    exit 1
}

echo "Starting gunicorn..."

# Run gunicorn with error handling
exec gunicorn main:app \
    -w 2 \
    -k uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload

