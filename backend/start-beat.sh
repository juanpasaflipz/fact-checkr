#!/bin/bash
# Railway Celery Beat (scheduler) startup script

set -e  # Exit on error

echo "=========================================="
echo "Starting FactCheckr Celery Beat Scheduler..."
echo "=========================================="

# Verify Redis connection
echo "Testing Redis connection..."
python -c "
import os
import redis
r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
r.ping()
print('✅ Redis connection successful')
" || {
    echo "❌ Failed to connect to Redis"
    exit 1
}

# Test if worker module can be imported
echo "Testing worker import..."
python -c "from app.worker import celery_app; print('✅ Worker module imported successfully')" || {
    echo "❌ Failed to import worker module"
    exit 1
}

echo "Starting Celery beat scheduler..."

# Run Celery beat
exec celery -A app.worker.celery_app beat \
    --loglevel=info \
    --pidfile=/tmp/celerybeat.pid

