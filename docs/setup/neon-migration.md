# Neon Migration Guide - Step by Step

## Prerequisites
- Current Supabase database connection string
- Neon account (we'll create this)
- Backup of existing data (we'll do this)

## Step 1: Create Neon Account

1. Go to https://neon.tech
2. Click "Sign Up" (you can use GitHub, Google, or email)
3. Complete the signup process

## Step 2: Create a New Project in Neon

1. Once logged in, click "Create Project"
2. Fill in:
   - **Project name**: `fact-checkr` (or your preferred name)
   - **Region**: Choose closest to you (e.g., `US East (Ohio)` for US)
   - **PostgreSQL version**: 15 or 16 (recommended: 16)
3. Click "Create Project"
4. Wait for the project to be created (~30 seconds)

## Step 3: Get Connection String

1. In your Neon project dashboard, you'll see a connection string
2. It looks like: `postgresql://user:password@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require`
3. Click "Copy" to copy the connection string
4. **Save this somewhere safe** - you'll need it in the next step

## Step 4: Backup Current Supabase Data (If You Have Data)

If you have existing data in Supabase that you want to keep:

```bash
# Install pg_dump if not already installed (usually comes with PostgreSQL)
# macOS: brew install postgresql
# Or use Docker: docker run --rm -it postgres:15 pg_dump --version

# Export data from Supabase
pg_dump "your-supabase-connection-string" > supabase_backup.sql

# This will create a backup file with all your data
```

## Step 5: Update Environment Variable

1. Open `backend/.env` file
2. Find the `DATABASE_URL` line
3. Replace it with your Neon connection string:

```bash
DATABASE_URL=postgresql://user:password@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**Important:** Make sure to:
- Keep the `?sslmode=require` parameter (Neon requires SSL)
- Don't add any extra spaces
- Keep the connection string on one line

## Step 6: Run Database Migrations

Neon database is empty, so we need to create the tables:

```bash
cd backend
source venv/bin/activate

# Run Alembic migrations to create tables
alembic upgrade head

# If you don't have migrations set up, we can create them
```

## Step 7: Import Data (If You Have Backup)

If you backed up data from Supabase:

```bash
# Import data to Neon
psql "your-neon-connection-string" < supabase_backup.sql
```

## Step 8: Test Connection

```bash
cd backend
source venv/bin/activate
python -c "from app.database.connection import engine; from sqlalchemy import text; with engine.connect() as conn: result = conn.execute(text('SELECT 1')); print('✓ Neon connection successful!')"
```

## Step 9: Restart Services

```bash
# Restart backend
# (Stop current backend, then restart)

# Restart workers
# (Stop current workers, then restart)
```

## Step 10: Verify Everything Works

1. Check backend health: `curl http://localhost:8000/health`
2. Check stats endpoint: `curl http://localhost:8000/stats`
3. Check frontend loads data correctly

## Troubleshooting

### Connection Timeout
- Make sure `?sslmode=require` is in the connection string
- Check firewall settings
- Verify the connection string is correct

### Migration Errors
- Make sure Alembic is installed: `pip install alembic`
- Check database permissions
- Verify connection string format

### Import Errors
- Make sure psql is installed
- Check backup file format
- Verify table structure matches

## Neon-Specific Optimizations

After migration, you can optimize for Neon:

1. **Connection Pooling**: Neon handles this automatically
2. **Auto-scaling**: Neon scales automatically
3. **Branching**: You can create database branches for testing

## Next Steps

After successful migration:
1. Update any documentation with new connection string
2. Remove old Supabase connection string from `.env`
3. Test all features thoroughly
4. Monitor connection stability

## Need Help?

If you encounter any issues during migration, check:
- Neon documentation: https://neon.tech/docs
- Connection issues: Check connection string format
- Migration issues: Check Alembic setup

