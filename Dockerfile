FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code from backend directory
COPY backend/ .

# Create logs directory
RUN mkdir -p logs

# Make startup script executable
RUN chmod +x /app/start.sh

# Railway handles port mapping automatically - no EXPOSE needed
# Railway sets $PORT environment variable at runtime

# Default: run with startup script
# The script handles migrations, logging, and gunicorn startup
CMD ["sh", "/app/start.sh"]

