#!/bin/bash
# Start Celery worker with beat scheduler for continuous data fetching

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$APP_ROOT"

# Activate virtual environment
source venv/bin/activate

# Set environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start Celery worker with beat
echo "Starting Celery worker with beat scheduler..."
celery -A app.worker:celery_app worker --beat --loglevel=info --concurrency=2

