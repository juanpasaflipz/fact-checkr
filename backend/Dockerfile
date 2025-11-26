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

# Make startup script executable
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Railway handles port mapping automatically - no EXPOSE needed
# Railway sets $PORT environment variable at runtime

# Run with startup script
CMD ["/app/start.sh"]

