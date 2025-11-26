FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
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

# Expose port (Railway will map to $PORT dynamically)
EXPOSE 8000

# Health check (Railway handles this externally)
# HEALTHCHECK removed - Railway uses its own health check

# Run with gunicorn for production
# Railway sets $PORT automatically - use it in the bind address
CMD sh -c 'gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --timeout 120 --access-logfile - --error-logfile -'

