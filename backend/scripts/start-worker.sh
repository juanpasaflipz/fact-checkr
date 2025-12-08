#!/bin/sh
# Railway Celery Worker startup script

set -e  # Exit on error

echo "=========================================="
echo "Starting FactCheckr Celery Worker..."
echo "=========================================="

# Set Python path to include project root (works locally and in container)
APP_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${APP_ROOT}:${PYTHONPATH}"
cd "$APP_ROOT"

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
python - <<'PY' || {
import os
import sys

try:
    import redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    display = redis_url.split("@")[-1] if "@" in redis_url else redis_url
    print(f'Connecting to Redis: {display}')
    r = redis.from_url(redis_url)
    r.ping()
    print('[OK] Redis connection successful')
except Exception as e:
    print(f'[ERROR] Failed to connect to Redis: {e}')
    sys.exit(1)
PY
    echo "[ERROR] Redis connection test failed"
    exit 1
}

# Test database connection (if DATABASE_URL is set)
if [ -n "$DATABASE_URL" ]; then
    echo "Testing database connection..."
    python - <<'PY' || {
import os
import sys

try:
    from app.database.connection import get_engine
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute('SELECT 1')
        print('[OK] Database connection successful')
except Exception as e:
    print(f'[WARNING] Database connection test failed: {e}')
    print('Worker will continue but database operations may fail')
PY
    echo "[WARNING] Database connection test failed - worker will continue"
}
fi

# Test if worker module can be imported
echo "Testing worker import..."
python - <<'PY' || {
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
PY
    echo "[ERROR] Worker module import failed"
    exit 1
}

echo "Starting Celery worker..."

# Run Celery worker
exec celery -A app.worker.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=50 \
    --time-limit=900 \
    --soft-time-limit=840
