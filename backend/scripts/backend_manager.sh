#!/bin/bash
# Backend server manager script
# Provides easy start/stop/status/health check for FastAPI backend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
BACKEND_LOG="$SCRIPT_DIR/backend.log"
PIDFILE="$SCRIPT_DIR/logs/backend.pid"
PORT=8000
HOST=127.0.0.1

# Create logs directory
mkdir -p logs

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
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

# Check if port is in use
is_port_in_use() {
    lsof -i :$PORT > /dev/null 2>&1
}

# Start backend
start_backend() {
    if is_running "$PIDFILE"; then
        warn "Backend already running (PID: $(cat $PIDFILE))"
        return 0
    fi
    
    if is_port_in_use; then
        error "Port $PORT is already in use"
        info "Try: lsof -i :$PORT"
        return 1
    fi
    
    log "Starting FastAPI backend server..."
    source venv/bin/activate
    
    # Start backend in background
    nohup uvicorn main:app \
        --reload \
        --host $HOST \
        --port $PORT \
        > "$BACKEND_LOG" 2>&1 &
    
    local backend_pid=$!
    echo $backend_pid > "$PIDFILE"
    
    # Wait a moment and check if it's still running
    sleep 3
    
    if is_running "$PIDFILE"; then
        # Check if health endpoint responds
        if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
            log "Backend started successfully (PID: $backend_pid)"
            log "API available at: http://localhost:$PORT"
            log "API docs at: http://localhost:$PORT/docs"
            return 0
        else
            warn "Backend process started but health check failed"
            warn "Check logs: tail -f $BACKEND_LOG"
            return 1
        fi
    else
        error "Backend failed to start"
        error "Check logs: tail -20 $BACKEND_LOG"
        return 1
    fi
}

# Stop backend
stop_backend() {
    if [ ! -f "$PIDFILE" ]; then
        # Try to find by port
        local pid=$(lsof -ti :$PORT 2>/dev/null || true)
        if [ -n "$pid" ]; then
            warn "Found backend process on port $PORT (PID: $pid)"
            log "Stopping backend (PID: $pid)..."
            kill -TERM "$pid" 2>/dev/null || true
            
            # Wait for graceful shutdown
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                warn "Force killing backend..."
                kill -KILL "$pid" 2>/dev/null || true
            fi
            log "Backend stopped"
            return 0
        else
            warn "Backend not running (no PID file or process on port $PORT)"
            return 0
        fi
    fi
    
    local pid=$(cat "$PIDFILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        log "Stopping backend (PID: $pid)..."
        kill -TERM "$pid" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local count=0
        while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if ps -p "$pid" > /dev/null 2>&1; then
            warn "Force killing backend..."
            kill -KILL "$pid" 2>/dev/null || true
        fi
        
        rm -f "$PIDFILE"
        log "Backend stopped"
    else
        warn "Backend not running (process not found)"
        rm -f "$PIDFILE"
    fi
}

# Health check
health_check() {
    if ! is_running "$PIDFILE"; then
        error "Backend is not running"
        return 1
    fi
    
    local response=$(curl -s http://localhost:$PORT/health 2>/dev/null || echo "")
    if [ -n "$response" ]; then
        log "Health check passed"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        return 0
    else
        error "Health check failed - backend not responding"
        return 1
    fi
}

# Status
status() {
    echo "=== Backend Server Status ==="
    if is_running "$PIDFILE"; then
        echo -e "Status: ${GREEN}RUNNING${NC} (PID: $(cat $PIDFILE))"
        echo -e "URL: http://localhost:$PORT"
        echo -e "Docs: http://localhost:$PORT/docs"
        
        # Check health
        if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
            echo -e "Health: ${GREEN}HEALTHY${NC}"
        else
            echo -e "Health: ${YELLOW}NOT RESPONDING${NC}"
        fi
    else
        echo -e "Status: ${RED}STOPPED${NC}"
    fi
    
    if is_port_in_use; then
        echo -e "Port $PORT: ${GREEN}IN USE${NC}"
    else
        echo -e "Port $PORT: ${RED}AVAILABLE${NC}"
    fi
}

# Main command handler
case "${1:-}" in
    start)
        start_backend
        ;;
    stop)
        stop_backend
        ;;
    restart)
        stop_backend
        sleep 2
        start_backend
        ;;
    status)
        status
        ;;
    health)
        health_check
        ;;
    logs)
        tail -f "$BACKEND_LOG"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|health|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the backend server"
        echo "  stop    - Stop the backend server"
        echo "  restart - Restart the backend server"
        echo "  status  - Show backend status"
        echo "  health  - Check backend health endpoint"
        echo "  logs    - Tail backend logs"
        exit 1
        ;;
esac

