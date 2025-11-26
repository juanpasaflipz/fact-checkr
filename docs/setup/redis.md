# Redis Setup & Connection Guide

## Current Status

✅ **Redis is installed and running!**

**Connection Test:**
```bash
redis-cli ping
# Returns: PONG
```

---

## Local Redis (Current Setup)

### Status
- ✅ Redis server is running
- ✅ Connection: `redis://localhost:6379/0`
- ✅ Workers can connect

### Configuration

**Backend `.env`:**
```bash
REDIS_URL=redis://localhost:6379/0
```

**Default (if not set):**
- Host: `localhost`
- Port: `6379`
- Database: `0`

---

## Redis Management

### Start Redis (if not running)
```bash
# Using Homebrew service
brew services start redis

# Or manually
redis-server
```

### Stop Redis
```bash
brew services stop redis
```

### Check Status
```bash
# Test connection
redis-cli ping
# Should return: PONG

# Check if running
ps aux | grep redis-server

# Check info
redis-cli info server
```

### View Redis Data
```bash
# Connect to Redis CLI
redis-cli

# Inside Redis CLI:
KEYS *              # List all keys
GET <key>          # Get value
FLUSHALL           # Clear all data (careful!)
INFO               # Server information
EXIT               # Exit
```

---

## Production Redis Options

### Option 1: Redis Cloud (Recommended for Production)

**Benefits:**
- Managed service
- Free tier available
- Automatic backups
- High availability

**Setup:**
1. Sign up at [redis.com](https://redis.com/try-free/)
2. Create database
3. Copy connection string
4. Add to `.env`:
   ```bash
   REDIS_URL=redis://:password@host:port
   ```

**Free Tier:**
- 30MB storage
- No credit card required
- Perfect for development/small production

### Option 2: Self-Hosted (Docker)

```bash
# Run Redis in Docker
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# Connection string
REDIS_URL=redis://localhost:6379/0
```

### Option 3: Railway / Render Redis

**Railway:**
1. Add Redis service
2. Copy connection string
3. Add to environment variables

**Render:**
1. Create Redis instance
2. Copy internal URL
3. Add to environment variables

---

## Testing Redis Connection

### From Python
```python
import redis
r = redis.from_url("redis://localhost:6379/0")
print(r.ping())  # Should print: True
```

### From Command Line
```bash
# Test connection
redis-cli ping

# Test with specific database
redis-cli -n 0 ping

# Test with password (if set)
redis-cli -a password ping
```

### From Celery
```bash
cd backend
source venv/bin/activate
celery -A app.worker inspect ping
# Should show worker response
```

---

## Troubleshooting

### "Connection refused"
```bash
# Check if Redis is running
ps aux | grep redis-server

# Start Redis
brew services start redis
# Or: redis-server
```

### "Redis is not accessible"
```bash
# Check Redis URL in .env
cd backend
cat .env | grep REDIS_URL

# Test connection
redis-cli ping

# Check port
lsof -i :6379
```

### "Can't connect to Redis"
1. **Verify Redis is running:**
   ```bash
   redis-cli ping
   ```

2. **Check firewall/network:**
   ```bash
   # Local should work, remote needs network access
   ```

3. **Verify connection string:**
   ```bash
   # Format: redis://[password@]host:port/db
   # Example: redis://localhost:6379/0
   # Example: redis://:password@host:6379/0
   ```

### Redis Memory Issues
```bash
# Check memory usage
redis-cli info memory

# Clear all data (careful!)
redis-cli FLUSHALL

# Set max memory (in redis.conf)
maxmemory 256mb
maxmemory-policy allkeys-lru
```

---

## Redis Configuration for Production

### Security
```bash
# Set password in redis.conf
requirepass your_secure_password

# Update connection string
REDIS_URL=redis://:your_secure_password@localhost:6379/0
```

### Persistence
```bash
# Enable AOF (Append Only File) - recommended
appendonly yes
appendfsync everysec

# Or RDB snapshots
save 900 1
save 300 10
save 60 10000
```

### Performance
```bash
# Connection pooling (already handled by Celery)
# Max clients
maxclients 10000

# Timeout
timeout 300
```

---

## Monitoring Redis

### Check Connection Count
```bash
redis-cli info clients
```

### Check Memory Usage
```bash
redis-cli info memory
```

### Check Keys
```bash
redis-cli DBSIZE        # Total keys
redis-cli KEYS "*"      # List all keys
redis-cli KEYS "celery*" # Celery keys
```

### Monitor Commands
```bash
redis-cli MONITOR
# Shows all commands in real-time
```

---

## Celery + Redis

### Verify Celery Can Connect
```bash
cd backend
source venv/bin/activate

# Check worker can ping Redis
celery -A app.worker inspect ping

# Check registered tasks
celery -A app.worker inspect registered

# Check active tasks
celery -A app.worker inspect active
```

### Clear Celery Queue
```bash
# Clear all Celery data
redis-cli FLUSHDB

# Or specific keys
redis-cli KEYS "celery*" | xargs redis-cli DEL
```

---

## Quick Reference

### Connection Strings
```bash
# Local (default)
REDIS_URL=redis://localhost:6379/0

# With password
REDIS_URL=redis://:password@localhost:6379/0

# Remote
REDIS_URL=redis://user:password@host:port/db

# Redis Cloud
REDIS_URL=redis://:password@host.redis.cloud:port
```

### Common Commands
```bash
# Start
brew services start redis

# Stop
brew services stop redis

# Restart
brew services restart redis

# Test
redis-cli ping

# Connect
redis-cli

# Info
redis-cli info
```

---

## Next Steps

1. ✅ **Redis is running** - No action needed for local development
2. ⏳ **For production:** Set up Redis Cloud or managed Redis
3. ⏳ **Update `.env`:** Add `REDIS_URL` if using custom configuration
4. ⏳ **Test workers:** Verify Celery can connect

---

**Current Status:** ✅ Redis is connected and working!

