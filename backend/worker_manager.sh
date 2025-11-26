#!/bin/bash
# Robust Celery worker manager with health checks and auto-restart
# This script provides better process management than basic nohup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
WORKER_LOG="$SCRIPT_DIR/logs/celery_worker.log"
BEAT_LOG="$SCRIPT_DIR/logs/celery_beat.log"
PIDFILE_WORKER="$SCRIPT_DIR/logs/celery_worker.pid"
PIDFILE_BEAT="$SCRIPT_DIR/logs/celery_beat.pid"
MAX_RESTARTS=10
RESTART_DELAY=5

# Create logs directory
mkdir -p logs

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check if process is running
is_running() {
    local pidfile=$1
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$pidfile"
            return 1
        fi
    fi
    return 1
}

# Start worker
start_worker() {
    if is_running "$PIDFILE_WORKER"; then
        warn "Worker already running (PID: $(cat $PIDFILE_WORKER))"
        return 0
    fi
    
    log "Starting Celery worker..."
    source venv/bin/activate
    
    # Start worker in background
    nohup celery -A app.worker worker \
        --loglevel=info \
        --concurrency=2 \
        --logfile="$WORKER_LOG" \
        --pidfile="$PIDFILE_WORKER" \
        > "$WORKER_LOG" 2>&1 &
    
    local worker_pid=$!
    echo $worker_pid > "$PIDFILE_WORKER"
    
    # Wait a moment and check if it's still running
    sleep 2
    if is_running "$PIDFILE_WORKER"; then
        log "Worker started successfully (PID: $worker_pid)"
        return 0
    else
        error "Worker failed to start"
        return 1
    fi
}

# Start beat
start_beat() {
    if is_running "$PIDFILE_BEAT"; then
        warn "Beat already running (PID: $(cat $PIDFILE_BEAT))"
        return 0
    fi
    
    log "Starting Celery beat..."
    source venv/bin/activate
    
    # Start beat in background with explicit schedule file
    nohup celery -A app.worker beat \
        --loglevel=info \
        --logfile="$BEAT_LOG" \
        --pidfile="$PIDFILE_BEAT" \
        --schedule="$SCRIPT_DIR/logs/celerybeat-schedule" \
        > "$BEAT_LOG" 2>&1 &
    
    local beat_pid=$!
    echo $beat_pid > "$PIDFILE_BEAT"
    
    # Wait a moment and check if it's still running
    sleep 2
    if is_running "$PIDFILE_BEAT"; then
        log "Beat started successfully (PID: $beat_pid)"
        return 0
    else
        error "Beat failed to start"
        return 1
    fi
}

# Stop worker
stop_worker() {
    if [ ! -f "$PIDFILE_WORKER" ]; then
        warn "Worker not running (no PID file)"
        return 0
    fi
    
    local pid=$(cat "$PIDFILE_WORKER")
    if ps -p "$pid" > /dev/null 2>&1; then
        log "Stopping worker (PID: $pid)..."
        kill -TERM "$pid" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local count=0
        while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 30 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if ps -p "$pid" > /dev/null 2>&1; then
            warn "Force killing worker..."
            kill -KILL "$pid" 2>/dev/null || true
        fi
        
        rm -f "$PIDFILE_WORKER"
        log "Worker stopped"
    else
        warn "Worker not running (process not found)"
        rm -f "$PIDFILE_WORKER"
    fi
}

# Stop beat
stop_beat() {
    if [ ! -f "$PIDFILE_BEAT" ]; then
        warn "Beat not running (no PID file)"
        return 0
    fi
    
    local pid=$(cat "$PIDFILE_BEAT")
    if ps -p "$pid" > /dev/null 2>&1; then
        log "Stopping beat (PID: $pid)..."
        kill -TERM "$pid" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local count=0
        while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 30 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if ps -p "$pid" > /dev/null 2>&1; then
            warn "Force killing beat..."
            kill -KILL "$pid" 2>/dev/null || true
        fi
        
        rm -f "$PIDFILE_BEAT"
        log "Beat stopped"
    else
        warn "Beat not running (process not found)"
        rm -f "$PIDFILE_BEAT"
    fi
}

# Health check
health_check() {
    local healthy=true
    
    if ! is_running "$PIDFILE_WORKER"; then
        error "Worker is not running"
        healthy=false
    fi
    
    if ! is_running "$PIDFILE_BEAT"; then
        error "Beat is not running"
        healthy=false
    fi
    
    # Check Redis connection
    if ! redis-cli ping > /dev/null 2>&1; then
        error "Redis is not accessible"
        healthy=false
    fi
    
    if [ "$healthy" = true ]; then
        log "Health check passed"
        return 0
    else
        error "Health check failed"
        return 1
    fi
}

# Status
status() {
    echo "=== Celery Worker Status ==="
    if is_running "$PIDFILE_WORKER"; then
        echo -e "Worker: ${GREEN}RUNNING${NC} (PID: $(cat $PIDFILE_WORKER))"
    else
        echo -e "Worker: ${RED}STOPPED${NC}"
    fi
    
    if is_running "$PIDFILE_BEAT"; then
        echo -e "Beat: ${GREEN}RUNNING${NC} (PID: $(cat $PIDFILE_BEAT))"
    else
        echo -e "Beat: ${RED}STOPPED${NC}"
    fi
    
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "Redis: ${GREEN}CONNECTED${NC}"
    else
        echo -e "Redis: ${RED}DISCONNECTED${NC}"
    fi
}

# Main command handler
case "${1:-}" in
    start)
        start_worker
        start_beat
        sleep 2
        health_check
        ;;
    stop)
        stop_beat
        stop_worker
        ;;
    restart)
        stop_beat
        stop_worker
        sleep 2
        start_worker
        start_beat
        sleep 2
        health_check
        ;;
    status)
        status
        ;;
    health)
        health_check
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|health}"
        exit 1
        ;;
esac

