# Neon Migration - Quick Start Guide

## 🎯 Quick Steps (5 minutes)

### 1. Create Neon Account & Database

1. Go to https://neon.tech and sign up (free)
2. Click "Create Project"
3. Name it `fact-checkr`
4. Choose a region close to you
5. Click "Create Project"

### 2. Get Connection String

1. In your Neon project dashboard, find the connection string
2. It looks like: `postgresql://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`
3. Click "Copy" to copy it

### 3. Update Your .env File

```bash
cd backend
# Edit .env file and replace DATABASE_URL with your Neon connection string
# Make sure to include ?sslmode=require at the end
```

Or use this command (replace with your actual connection string):
```bash
# Backup old .env first
cp .env .env.backup

# Update DATABASE_URL (replace YOUR_NEON_CONNECTION_STRING)
sed -i '' 's|DATABASE_URL=.*|DATABASE_URL=YOUR_NEON_CONNECTION_STRING|' .env
```

### 4. Test Connection

```bash
cd backend
source venv/bin/activate
python test_neon_connection.py
```

You should see: `✅ All tests passed!`

### 5. Run Migrations

```bash
# This will create all your tables in Neon
alembic upgrade head
```

### 6. Restart Services

```bash
# Restart backend (stop current, then start new)
# Restart workers (stop current, then start new)
```

### 7. Verify Everything Works

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test stats endpoint
curl http://localhost:8000/stats
```

## 🚀 Automated Migration (Recommended)

Use the helper script:

```bash
cd backend
./migrate_to_neon.sh
```

This script will:
- ✅ Check your .env file
- ✅ Test the connection
- ✅ Run migrations automatically
- ✅ Verify the schema

## 📋 Manual Steps (If Needed)

### Backup Supabase Data (Optional)

If you have important data in Supabase:

```bash
# Export from Supabase
pg_dump "your-supabase-connection-string" > supabase_backup.sql

# Import to Neon (after migration)
psql "your-neon-connection-string" < supabase_backup.sql
```

### Create Tables Manually (If migrations fail)

```bash
cd backend
source venv/bin/activate
python3 << 'EOF'
from app.database.connection import engine
from app.database.models import Base
Base.metadata.create_all(engine)
print("✓ Tables created!")
EOF
```

## ✅ Verification Checklist

- [ ] Neon account created
- [ ] Project created in Neon
- [ ] Connection string copied
- [ ] DATABASE_URL updated in .env
- [ ] Connection test passed
- [ ] Migrations run successfully
- [ ] Backend restarted
- [ ] Workers restarted
- [ ] Health endpoint works
- [ ] Frontend loads data

## 🆘 Troubleshooting

### Connection Timeout

- Make sure `?sslmode=require` is in connection string
- Check Neon project is active (not paused)
- Verify connection string format

### Migration Errors

- Check Alembic is installed: `pip install alembic`
- Verify DATABASE_URL is correct
- Try: `alembic current` to see current version

### Import Errors

- Make sure you're in `backend/` directory
- Activate venv: `source venv/bin/activate`
- Check all dependencies: `pip install -r requirements.txt`

## 📞 Need Help?

1. Run the test script: `python test_neon_connection.py`
2. Check the detailed guide: `NEON_MIGRATION_GUIDE.md`
3. Neon docs: https://neon.tech/docs

## 🎉 After Migration

Once everything works:
1. ✅ Remove old Supabase connection string
2. ✅ Update any documentation
3. ✅ Monitor connection stability
4. ✅ Enjoy better reliability!

---

**Estimated Time:** 5-10 minutes
**Difficulty:** Easy
**Code Changes Required:** None (just .env update)

