# Repository Reorganization Guide

This document explains the new repository structure after reorganization.

## New Directory Structure

```
fact-checkr/
├── backend/
│   ├── app/                    # Application code (unchanged)
│   ├── alembic/                # Database migrations (unchanged)
│   ├── scripts/                 # ✨ NEW: All backend scripts
│   │   ├── start.sh
│   │   ├── start-beat.sh
│   │   ├── start-worker.sh
│   │   ├── start_workers.sh
│   │   ├── run_worker.sh
│   │   ├── backend_manager.sh
│   │   └── worker_manager.sh
│   ├── config/                  # ✨ NEW: Configuration files
│   │   ├── railway.json
│   │   ├── railway-beat.json
│   │   ├── railway-worker.json
│   │   └── supervisor_celery.conf
│   ├── tests/                   # ✨ NEW: Test files
│   │   ├── check_db.py
│   │   └── test_startup.py
│   ├── logs/                    # Log files (unchanged)
│   ├── main.py                  # Main entry point (unchanged)
│   └── requirements.txt         # Dependencies (unchanged)
│
├── frontend/                     # Frontend code (unchanged)
│
├── scripts/                     # ✨ REORGANIZED: All utility scripts
│   ├── deploy-production.sh
│   ├── deploy.sh
│   ├── start-dev.sh
│   ├── migrate_*.sh
│   ├── seed_*.py
│   └── test/
│
├── docs/
│   ├── deployment/              # All deployment docs
│   ├── setup/                   # Setup and environment docs
│   ├── development/             # Development guides
│   ├── integrations/           # Third-party integrations
│   ├── features/               # ✨ NEW: Feature documentation
│   │   ├── PREMIUM_FEATURES_IMPLEMENTATION.md
│   │   ├── PREDICTION_MARKET_ENHANCEMENTS.md
│   │   ├── VERIFICATION_PROCESS_ANALYSIS.md
│   │   └── DATA_COLLECTION_*.md
│   ├── guides/                  # ✨ NEW: How-to guides
│   │   ├── STRIPE_SETUP_GUIDE.md
│   │   ├── TWITTER_BASIC_UPGRADE.md
│   │   └── SCRAPING_*.md
│   └── archive/                # Archived docs
│
├── docker-compose.yml           # Docker setup (unchanged)
├── railway.json                 # Root Railway config (unchanged)
├── vercel.json                  # Vercel config (unchanged)
└── README.md                    # Main README (unchanged)
```

## Files That Need Path Updates

After running the reorganization script, you'll need to update references in:

### 1. Dockerfiles

**`backend/Dockerfile`** - Update script paths:
```dockerfile
# OLD:
COPY backend/start.sh /app/start.sh

# NEW:
COPY backend/scripts/start.sh /app/start.sh
```

**`backend/Dockerfile.beat`** - Update script paths:
```dockerfile
# OLD:
COPY backend/start-beat.sh /app/start-beat.sh

# NEW:
COPY backend/scripts/start-beat.sh /app/start-beat.sh
```

**`backend/Dockerfile.worker`** - Update script paths:
```dockerfile
# OLD:
COPY backend/start-worker.sh /app/start-worker.sh

# NEW:
COPY backend/scripts/start-worker.sh /app/start-worker.sh
```

### 2. Railway Configuration

**`railway.json`** - May need to update if it references backend scripts:
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "sh /app/scripts/start.sh"  // Updated path
  }
}
```

### 3. Scripts That Reference Other Scripts

Check these scripts for hardcoded paths:
- `scripts/deploy.sh`
- `scripts/deploy-production.sh`
- `scripts/start-dev.sh`
- Any scripts in `backend/scripts/` that call each other

### 4. Documentation References

Update any documentation that references old paths:
- README.md
- Deployment guides
- Setup guides

## Backward Compatibility

The reorganization script creates symlinks for commonly used files:
- `backend/start.sh` → `backend/scripts/start.sh`

This allows existing references to continue working, but you should update them eventually.

## Running the Reorganization

```bash
# 1. Review what will be moved
./scripts/reorganize-repo.sh

# 2. After running, update file references
# (See "Files That Need Path Updates" above)

# 3. Test that everything works
cd backend
./scripts/start.sh  # Should work with new path

# 4. Commit changes
git add .
git commit -m "Reorganize repository structure"
```

## Benefits of New Structure

1. **Clearer Organization**: Scripts, configs, and tests are in dedicated folders
2. **Easier Navigation**: Related files are grouped together
3. **Better Maintainability**: Less clutter in root directories
4. **Scalability**: Easy to add new scripts/configs without cluttering

## Migration Checklist

- [ ] Run reorganization script
- [ ] Update Dockerfile paths
- [ ] Update Railway config paths
- [ ] Update script references
- [ ] Update documentation references
- [ ] Test all scripts work
- [ ] Test Docker builds
- [ ] Test Railway deployment
- [ ] Commit changes

## Questions?

If you encounter issues after reorganization:
1. Check the symlinks (they provide backward compatibility)
2. Review this guide for path updates
3. Check git status to see what moved
4. Test each component individually

