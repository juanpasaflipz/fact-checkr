# Database Setup Guide

Guide for setting up PostgreSQL database (Neon recommended for production).

## Quick Start with Neon

1. **Create Project** at [neon.tech](https://neon.tech)
2. **Copy Connection String**
   - Use **pooled endpoint** for serverless deployments
   - Format: `postgresql://user:pass@host-pooler.neon.tech/db?sslmode=require`
3. **Run Migrations**
   ```bash
   cd backend
   source venv/bin/activate
   alembic upgrade head
   ```
4. **Enable Connection Pooling** in Neon dashboard

## Local PostgreSQL Setup

### Install PostgreSQL

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE factcheckr;
CREATE USER factcheckr_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE factcheckr TO factcheckr_user;
\q
```

### Connection String

```bash
DATABASE_URL=postgresql://factcheckr_user:your_secure_password@localhost/factcheckr
```

## Run Migrations

```bash
cd backend
source venv/bin/activate

# Upgrade to latest migration
alembic upgrade head

# Create new migration (when schema changes)
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1
```

## Seed Initial Data

```bash
# Seed topics
python seed_topics.py

# Seed mock data (development only)
python seed_mock_data.py
```

## Connection Pooling

For serverless deployments (Railway, Vercel, Fly.io), use Neon's pooled endpoint:

```
postgresql://user:pass@host-pooler.neon.tech/db?sslmode=require
```

This prevents connection limit issues with serverless functions.

## Backup and Restore

### Backup
```bash
pg_dump $DATABASE_URL > backup.sql
```

### Restore
```bash
psql $DATABASE_URL < backup.sql
```

## Troubleshooting

### Connection Timeout
- Check Neon is not suspended (free tier auto-suspends)
- Verify using pooled endpoint for serverless
- Increase `pool_timeout` in connection.py

### Migration Errors
- Ensure database exists
- Check user has proper permissions
- Verify DATABASE_URL format

### Connection Limit
- Use pooled endpoint for serverless
- Reduce connection pool size
- Check for connection leaks

