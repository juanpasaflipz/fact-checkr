#!/bin/bash
# Production Deployment Script
# Usage: ./deploy.sh [backend|frontend|all|docker]

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[DEPLOY]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

check_env() {
    log "Checking environment variables..."
    
    local missing=0
    
    # Backend required
    if [ -z "$DATABASE_URL" ]; then
        error "DATABASE_URL is not set"
        missing=1
    fi
    
    if [ -z "$JWT_SECRET_KEY" ]; then
        error "JWT_SECRET_KEY is not set"
        missing=1
    fi
    
    # Frontend required
    if [ -z "$NEXT_PUBLIC_API_URL" ]; then
        warn "NEXT_PUBLIC_API_URL is not set (will use default)"
    fi
    
    if [ $missing -eq 1 ]; then
        error "Missing required environment variables. Aborting."
        exit 1
    fi
    
    log "Environment check passed"
}

deploy_backend() {
    log "Deploying backend..."
    
    cd backend
    
    # Run database migrations
    info "Running database migrations..."
    source venv/bin/activate
    alembic upgrade head
    
    # Check if using Docker
    if [ "$1" = "docker" ]; then
        info "Building Docker image..."
        docker build -t factcheckr-backend:latest .
        log "Backend Docker image built"
    else
        info "Backend ready for deployment"
        info "Use: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"
    fi
    
    cd ..
}

deploy_frontend() {
    log "Deploying frontend..."
    
    cd frontend
    
    # Install dependencies
    info "Installing dependencies..."
    npm ci
    
    # Build
    info "Building Next.js application..."
    npm run build
    
    # Check if using Docker
    if [ "$1" = "docker" ]; then
        info "Building Docker image..."
        docker build -t factcheckr-frontend:latest .
        log "Frontend Docker image built"
    else
        info "Frontend ready for deployment"
        info "Use: npm start"
    fi
    
    cd ..
}

deploy_docker() {
    log "Deploying with Docker Compose..."
    
    check_env
    
    # Build and start services
    info "Building Docker images..."
    docker-compose build
    
    info "Starting services..."
    docker-compose up -d
    
    log "Services started. Checking health..."
    sleep 5
    
    # Health checks
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "✅ Backend is healthy"
    else
        warn "⚠️  Backend health check failed"
    fi
    
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log "✅ Frontend is accessible"
    else
        warn "⚠️  Frontend health check failed"
    fi
    
    info "View logs: docker-compose logs -f"
    info "Stop services: docker-compose down"
}

deploy_all() {
    log "Deploying all services..."
    
    check_env
    
    deploy_backend
    deploy_frontend
    
    log "✅ Deployment complete"
    info "Next steps:"
    info "1. Start backend: cd backend && gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker"
    info "2. Start workers: cd backend && ./worker_manager.sh start"
    info "3. Start frontend: cd frontend && npm start"
}

# Main
case "${1:-all}" in
    backend)
        check_env
        deploy_backend
        ;;
    frontend)
        deploy_frontend
        ;;
    docker)
        deploy_docker
        ;;
    all)
        deploy_all
        ;;
    *)
        echo "Usage: $0 [backend|frontend|all|docker]"
        echo ""
        echo "Commands:"
        echo "  backend  - Deploy backend only"
        echo "  frontend - Deploy frontend only"
        echo "  all      - Deploy both (default)"
        echo "  docker   - Deploy using Docker Compose"
        exit 1
        ;;
esac

