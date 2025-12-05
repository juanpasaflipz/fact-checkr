#!/bin/sh
# Railway Celery Beat (scheduler) startup script

set -e  # Exit on error

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    . venv/bin/activate
fi

# Use python3 if python is not available
PYTHON_CMD="python"
if ! command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python3"
fi

echo "=========================================="
echo "Starting FactCheckr Celery Beat Scheduler..."
echo "=========================================="

# Verify Redis connection
echo "Testing Redis connection..."
$PYTHON_CMD -c "
import os
import redis
r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
r.ping()
print('[OK] Redis connection successful')
" || {
    echo "[ERROR] Failed to connect to Redis"
    exit 1
}

# Test if worker module can be imported
echo "Testing worker import..."
$PYTHON_CMD -c "from app.worker import celery_app; print('[OK] Worker module imported successfully')" || {
    echo "[ERROR] Failed to import worker module"
    exit 1
}

echo "Starting Celery beat scheduler..."

# Run Celery beat
exec celery -A app.worker.celery_app beat \
    --loglevel=info \
    --pidfile=/tmp/celerybeat.pid
