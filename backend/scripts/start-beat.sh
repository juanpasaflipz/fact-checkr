#!/bin/sh
# Railway Celery Beat (scheduler) startup script

set -e  # Exit on error

echo "=========================================="
echo "Starting FactCheckr Celery Beat Scheduler..."
echo "=========================================="

# Set Python path to include current directory
export PYTHONPATH=/app:$PYTHONPATH

# Verify Python and dependencies
echo "Checking Python version..."
python --version

echo "Checking installed packages..."
python -c "import celery; print(f'Celery version: {celery.__version__}')" || {
    echo "[ERROR] Celery not installed"
    exit 1
}

# Verify Redis connection
echo "Testing Redis connection..."
python -c "
import os
import sys
try:
    import redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    display = redis_url.split('@')[-1] if '@' in redis_url else redis_url
    print(f'Connecting to Redis: {display}')
    r = redis.from_url(redis_url)
    r.ping()
    print('[OK] Redis connection successful')
except Exception as e:
    print(f'[ERROR] Failed to connect to Redis: {e}')
    sys.exit(1)
" || {
    echo "[ERROR] Redis connection test failed"
    exit 1
}

# Test if worker module can be imported
echo "Testing worker import..."
python -c "
import sys
import traceback
try:
    from app.worker import celery_app
    print('[OK] Worker module imported successfully')
    print(f'[OK] Celery app name: {celery_app.main}')
except Exception as e:
    print(f'[ERROR] Failed to import worker module: {e}')
    traceback.print_exc()
    sys.exit(1)
" || {
    echo "[ERROR] Worker module import failed"
    exit 1
}

echo "Starting Celery beat scheduler..."

# Run Celery beat
exec celery -A app.worker:celery_app beat \
    --loglevel=info \
    --pidfile=/tmp/celerybeat.pid
