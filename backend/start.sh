#!/bin/bash
# Railway startup script
# Railway sets $PORT automatically

set -e  # Exit on error

PORT=${PORT:-8000}

echo "Starting FactCheckr API on port ${PORT}..."

# Run gunicorn with error handling
exec gunicorn main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

