#!/bin/bash
# Railway startup script
# Railway sets $PORT automatically

PORT=${PORT:-8000}

exec gunicorn main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

