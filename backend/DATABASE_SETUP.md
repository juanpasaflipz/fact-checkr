# Database Setup Guide

## Prerequisites
You need PostgreSQL installed on your system.

### Install PostgreSQL on macOS
```bash
# Using Homebrew
brew install postgresql@16
brew services start postgresql@16
```

## Setup Steps

### 1. Create Database
```bash
# Connect to PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE factcheckr;
CREATE USER factcheckr_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE factcheckr TO factcheckr_user;

# Exit psql
\q
```

### 2. Update .env File
Add this line to your `.env` file:
```
DATABASE_URL=postgresql://factcheckr_user:your_secure_password@localhost/factcheckr
```

### 3. Run Migrations
```bash
# Create initial migration
./venv/bin/alembic revision --autogenerate -m "Initial schema"

# Apply migration
./venv/bin/alembic upgrade head
```

### 4. Verify Setup
```bash
# Connect to database
psql -d factcheckr -U factcheckr_user

# List tables
\dt

# You should see: sources, claims, topics, entities, claim_topics
```

## Quick Start (If PostgreSQL is already installed)
```bash
# 1. Create database
createdb factcheckr

# 2. Add to .env
echo "DATABASE_URL=postgresql://localhost/factcheckr" >> .env

# 3. Run migrations
./venv/bin/alembic revision --autogenerate -m "Initial schema"
./venv/bin/alembic upgrade head
```

## Troubleshooting

**Connection refused:**
- Make sure PostgreSQL is running: `brew services list`
- Start if needed: `brew services start postgresql@16`

**Permission denied:**
- Check your DATABASE_URL credentials
- Verify user has correct permissions

**Table already exists:**
- Drop and recreate: `dropdb factcheckr && createdb factcheckr`
- Then run migrations again
