#!/bin/bash
# Start Celery worker with beat scheduler for continuous data fetching

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start Celery worker with beat
echo "Starting Celery worker with beat scheduler..."
celery -A app.worker worker --beat --loglevel=info --concurrency=2

