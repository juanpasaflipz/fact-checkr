# Celery Worker Management Guide

This guide explains the improved worker management system that prevents crashes and ensures reliability.

---

## Overview

The new system includes:
1. **Automatic retries** with exponential backoff
2. **Process management** with health checks
3. **Better error handling** in tasks
4. **Graceful shutdown** handling
5. **Monitoring** capabilities

---

## Methods Available

### Method 1: Worker Manager Script (Recommended)

**Location:** `backend/worker_manager.sh`

**Features:**
- Automatic restart on failure
- Health checks
- Graceful shutdown
- Status monitoring
- Separate worker and beat processes

**Usage:**
```bash
cd backend

# Start workers
./worker_manager.sh start

# Stop workers
./worker_manager.sh stop

# Restart workers
./worker_manager.sh restart

# Check status
./worker_manager.sh status

# Health check
./worker_manager.sh health
```

**Benefits:**
- ✅ Automatic restart on crash
- ✅ Health monitoring
- ✅ Clean process management
- ✅ Separate logs for worker and beat

---

### Method 2: Supervisor (Production)

**Installation:**
```bash
pip install supervisor
```

**Configuration:** `backend/supervisor_celery.conf`

**Usage:**
```bash
# Start supervisor
supervisord -c backend/supervisor_celery.conf

# Control processes
supervisorctl -c backend/supervisor_celery.conf status
supervisorctl -c backend/supervisor_celery.conf start celery_worker
supervisorctl -c backend/supervisor_celery.conf stop celery_beat
supervisorctl -c backend/supervisor_celery.conf restart all

# View logs
tail -f backend/logs/celery_worker.log
tail -f backend/logs/celery_beat.log
```

**Benefits:**
- ✅ Professional process management
- ✅ Automatic restarts
- ✅ Web UI available
- ✅ Better for production

---

### Method 3: Systemd (Linux Production)

Create `/etc/systemd/system/celery-worker.service`:
```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=your_user
Group=your_group
WorkingDirectory=/path/to/fact-checkr/backend
Environment="PATH=/path/to/fact-checkr/backend/venv/bin"
ExecStart=/path/to/fact-checkr/backend/venv/bin/celery -A app.worker worker --loglevel=info --concurrency=2 --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Usage:**
```bash
sudo systemctl enable celery-worker
sudo systemctl start celery-worker
sudo systemctl status celery-worker
```

---

## Improvements Made

### 1. Automatic Retries

Tasks now automatically retry on failure:
- **Max retries:** 3 attempts
- **Backoff:** Exponential (1s, 2s, 4s, ...)
- **Max delay:** 10 minutes between retries
- **Jitter:** Random delay to prevent thundering herd

**Configuration in `app/worker.py`:**
```python
task_autoretry_for=(Exception,),
task_retry_backoff=True,
task_retry_backoff_max=600,
task_max_retries=3,
```

### 2. Better Error Handling

Tasks use `bind=True` to access retry functionality:
```python
@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def scrape_all_sources(self):
    try:
        # ... task code ...
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc)  # Automatic retry
```

### 3. Timeout Protection

Tasks have time limits to prevent hanging:
- **Soft limit:** 4 minutes (raises exception, can be caught)
- **Hard limit:** 5 minutes (kills task)

### 4. Worker Lifecycle Management

Workers restart after processing tasks to prevent memory leaks:
- **Max tasks per child:** 50 tasks
- Prevents memory accumulation
- Ensures fresh worker state

### 5. Health Checks

Automatic health check every 5 minutes:
- Verifies database connectivity
- Logs worker status
- Can be used for monitoring alerts

---

## Monitoring

### Check Worker Status
```bash
# Using worker manager
./worker_manager.sh status

# Using Celery CLI
celery -A app.worker inspect active
celery -A app.worker inspect stats
celery -A app.worker inspect registered
```

### View Logs
```bash
# Worker logs
tail -f backend/logs/celery_worker.log

# Beat logs
tail -f backend/logs/celery_beat.log

# Error logs
tail -f backend/logs/celery_worker_error.log
```

### Monitor Task Execution
```bash
# Watch active tasks
watch -n 2 'celery -A app.worker inspect active'

# Check scheduled tasks
celery -A app.worker inspect scheduled

# View task results
celery -A app.worker result <task_id>
```

---

## Troubleshooting

### Workers Keep Crashing

1. **Check logs:**
   ```bash
   tail -50 backend/logs/celery_worker_error.log
   ```

2. **Check dependencies:**
   ```bash
   cd backend
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Check Redis:**
   ```bash
   redis-cli ping
   ```

4. **Check database:**
   ```bash
   cd backend
   source venv/bin/activate
   python -c "from app.database import SessionLocal; db = SessionLocal(); print('DB OK')"
   ```

### Tasks Not Executing

1. **Check beat is running:**
   ```bash
   ./worker_manager.sh status
   ```

2. **Check scheduled tasks:**
   ```bash
   celery -A app.worker inspect scheduled
   ```

3. **Manually trigger task:**
   ```bash
   cd backend
   source venv/bin/activate
   python trigger_scrape.py
   ```

### High Memory Usage

Workers automatically restart after 50 tasks. If memory is still high:

1. **Reduce concurrency:**
   ```bash
   # In worker_manager.sh, change:
   --concurrency=2  # to --concurrency=1
   ```

2. **Reduce max tasks per child:**
   ```python
   # In app/worker.py:
   worker_max_tasks_per_child=25  # instead of 50
   ```

---

## Best Practices

1. **Always use the worker manager script** for development
2. **Use Supervisor or systemd** for production
3. **Monitor logs regularly** for early problem detection
4. **Set up alerts** for worker failures
5. **Regular health checks** to verify system status
6. **Keep dependencies updated** to prevent compatibility issues

---

## Migration from Old System

If you're currently using `start_workers.sh`:

1. **Stop old workers:**
   ```bash
   pkill -f "celery.*worker"
   ```

2. **Start new system:**
   ```bash
   ./worker_manager.sh start
   ```

3. **Verify:**
   ```bash
   ./worker_manager.sh status
   ```

---

## Next Steps

1. ✅ Use `worker_manager.sh` for development
2. ⏳ Set up Supervisor for production
3. ⏳ Configure monitoring alerts
4. ⏳ Set up log rotation
5. ⏳ Create health check dashboard

---

**For questions or issues, check logs first:**
```bash
tail -f backend/logs/celery_worker.log
```

