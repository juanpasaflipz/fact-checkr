FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Make startup script executable
RUN chmod +x /app/scripts/start.sh

# Railway handles port mapping automatically - no EXPOSE needed
# Railway sets $PORT environment variable at runtime

# Railway sets PORT env var - uvicorn reads it automatically
# Run migrations first (non-blocking on failure), then start uvicorn
CMD sh -c "echo 'Running migrations...' && alembic upgrade head || echo 'Migration warning (continuing)' && echo 'Starting uvicorn...' && python -m uvicorn main:app --host 0.0.0.0 --port \${PORT:-8000}"

