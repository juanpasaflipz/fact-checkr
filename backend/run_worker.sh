#!/bin/bash
# Run Celery worker with beat (scheduler)
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
./venv/bin/celery -A app.worker worker --beat --loglevel=info
