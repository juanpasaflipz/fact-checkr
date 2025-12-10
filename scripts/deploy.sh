#!/bin/bash
# Comprehensive Deployment Script for FactCheckr
# Automates full deployment: migrations, backend (Railway), frontend (Vercel)
# Usage: ./scripts/deploy.sh [--skip-migrations] [--skip-backend] [--skip-frontend] [--verify-only]

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Flags
SKIP_MIGRATIONS=false
SKIP_BACKEND=false
SKIP_FRONTEND=false
VERIFY_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-migrations)
            SKIP_MIGRATIONS=true
            shift
            ;;
        --skip-backend)
            SKIP_BACKEND=true
            shift
            ;;
        --skip-frontend)
            SKIP_FRONTEND=true
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-migrations] [--skip-backend] [--skip-frontend] [--verify-only]"
            exit 1
            ;;
    esac
done

# Helper functions
log() {
    echo -e "${GREEN}[✓]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

info() {
    echo -e "${BLUE}[i]${NC} $1"
}

section() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

step() {
    echo -e "${MAGENTA}[→]${NC} $1"
}

# Banner
banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║         FactCheckr MX - Deployment Automation            ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
    section "Checking Prerequisites"
    
    local missing=0
    
    # Git
    if ! command -v git &> /dev/null; then
        error "Git is not installed"
        missing=1
    else
        log "Git found: $(git --version | cut -d' ' -f3)"
    fi
    
    # Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
        missing=1
    else
        log "Python 3 found: $(python3 --version)"
    fi
    
    # Node.js (for frontend)
    if ! command -v node &> /dev/null; then
        warn "Node.js is not installed (required for frontend deployment)"
        if [ "$SKIP_FRONTEND" = false ]; then
            missing=1
        fi
    else
        log "Node.js found: $(node --version)"
    fi
    
    # Railway CLI
    if ! command -v railway &> /dev/null; then
        warn "Railway CLI not found"
        if [ "$SKIP_BACKEND" = false ]; then
            info "  Install: npm i -g @railway/cli"
            info "  Or deploy manually via Railway dashboard"
        fi
    else
        log "Railway CLI found: $(railway --version 2>/dev/null || echo 'installed')"
    fi
    
    # Vercel CLI
    if ! command -v vercel &> /dev/null; then
        warn "Vercel CLI not found"
        if [ "$SKIP_FRONTEND" = false ]; then
            info "  Install: npm i -g vercel"
            info "  Or deploy manually via Vercel dashboard"
        fi
    else
        log "Vercel CLI found: $(vercel --version 2>/dev/null || echo 'installed')"
    fi
    
    # Alembic (for migrations)
    if ! command -v alembic &> /dev/null; then
        warn "Alembic not found (required for migrations)"
        if [ "$SKIP_MIGRATIONS" = false ]; then
            info "  Install: pip install alembic"
        fi
    else
        log "Alembic found: $(alembic --version | head -n1)"
    fi
    
    if [ $missing -eq 1 ]; then
        error "Missing required tools. Please install them first."
        exit 1
    fi
}

# Check git status
check_git_status() {
    section "Checking Git Status"
    
    # Check if we're in a git repo
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        error "Not in a git repository"
        exit 1
    fi
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        warn "You have uncommitted changes"
        info "Current changes:"
        git status --short
        echo ""
        read -p "Continue with deployment? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Deployment cancelled"
            exit 0
        fi
    else
        log "Working directory is clean"
    fi
    
    # Show current branch
    CURRENT_BRANCH=$(git branch --show-current)
    info "Current branch: $CURRENT_BRANCH"
    
    if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
        warn "Not on main/master branch. Deploying from: $CURRENT_BRANCH"
    fi
    
    # Check if ahead of remote
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
    if [ -n "$REMOTE" ]; then
        if [ "$LOCAL" != "$REMOTE" ]; then
            warn "Local branch is ahead/behind remote"
            info "Consider pushing changes first: git push"
        else
            log "Local branch is up to date with remote"
        fi
    else
        warn "No remote tracking branch found"
    fi
}

# Verify Railway connection
check_railway() {
    if [ "$SKIP_BACKEND" = true ]; then
        return 0
    fi
    
    section "Checking Railway Connection"
    
    if ! command -v railway &> /dev/null; then
        warn "Railway CLI not available - skipping Railway checks"
        return 0
    fi
    
    if railway whoami &> /dev/null; then
        log "Logged in to Railway"
        RAILWAY_USER=$(railway whoami 2>/dev/null || echo "unknown")
        info "  User: $RAILWAY_USER"
        
        # Check if linked to project
        if railway status &> /dev/null; then
            log "Railway project is linked"
        else
            warn "Railway project not linked"
            info "  Run: railway link"
        fi
    else
        warn "Not logged in to Railway"
        info "  Run: railway login"
    fi
}

# Verify Vercel connection
check_vercel() {
    if [ "$SKIP_FRONTEND" = true ]; then
        return 0
    fi
    
    section "Checking Vercel Connection"
    
    if ! command -v vercel &> /dev/null; then
        warn "Vercel CLI not available - skipping Vercel checks"
        return 0
    fi
    
    if vercel whoami &> /dev/null; then
        log "Logged in to Vercel"
        VERCEL_USER=$(vercel whoami 2>/dev/null || echo "unknown")
        info "  User: $VERCEL_USER"
    else
        warn "Not logged in to Vercel"
        info "  Run: vercel login"
    fi
}

# Run database migrations
run_migrations() {
    if [ "$SKIP_MIGRATIONS" = true ]; then
        warn "Skipping database migrations"
        return 0
    fi
    
    section "Running Database Migrations"
    
    if [ "$VERIFY_ONLY" = true ]; then
        info "Verify-only mode: checking migration status"
        ./scripts/deploy-production.sh verify
        return 0
    fi
    
    # Check if Railway CLI is available
    if command -v railway &> /dev/null && railway whoami &> /dev/null; then
        step "Running migrations via Railway..."
        if (cd backend && railway run --service backend python -c "import sys; from alembic.config import main; sys.exit(main())" upgrade head); then
            log "Migrations completed successfully on Railway"
        else
            error "Migration failed on Railway"
            info "Trying alternative method..."
            if railway run --service backend alembic upgrade head 2>/dev/null; then
                log "Migrations completed (alternative method)"
            else
                error "Migration failed. Please run manually:"
                info "  (cd backend && railway run --service backend python -c 'import sys; from alembic.config import main; sys.exit(main())' upgrade head)"
                exit 1
            fi
        fi
    else
        warn "Railway CLI not available - cannot run migrations automatically"
        info "Please run migrations manually:"
        info "  ./scripts/deploy-production.sh railway"
        read -p "Have you run migrations manually? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Migrations must be run before deployment"
            exit 1
        fi
    fi
}

# Deploy backend to Railway
deploy_backend() {
    if [ "$SKIP_BACKEND" = true ]; then
        warn "Skipping backend deployment"
        return 0
    fi
    
    section "Deploying Backend to Railway"
    
    if [ "$VERIFY_ONLY" = true ]; then
        info "Verify-only mode: checking backend status"
        if command -v railway &> /dev/null; then
            railway status
        fi
        return 0
    fi
    
    if ! command -v railway &> /dev/null; then
        warn "Railway CLI not available"
        info "Deploy manually via Railway dashboard or GitHub auto-deploy"
        info "  URL: https://railway.app"
        return 0
    fi
    
    if ! railway whoami &> /dev/null; then
        error "Not logged in to Railway"
        info "Run: railway login"
        exit 1
    fi
    
    step "Triggering Railway deployment..."
    
    # Check if we should push to trigger auto-deploy
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
    
    if [ -z "$REMOTE" ] || [ "$LOCAL" != "$REMOTE" ]; then
        warn "Local changes not pushed to remote"
        info "Railway auto-deploy requires code to be pushed to GitHub"
        read -p "Push to GitHub now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            step "Pushing to GitHub..."
            git push origin $(git branch --show-current)
            log "Code pushed to GitHub"
            info "Railway will auto-deploy in a few moments"
            info "Monitor deployment: railway logs --service backend"
        else
            info "Skipping push. Deploy manually in Railway dashboard"
        fi
    else
        log "Code is up to date on remote"
        info "If auto-deploy is enabled, Railway will deploy automatically"
        info "Or trigger manually in Railway dashboard"
    fi
    
    # Verify services are configured
    info "Verifying Railway services..."
    if [ -f "railway.json" ]; then
        log "Backend service configured (railway.json)"
    else
        warn "railway.json not found"
    fi
}

# Deploy frontend to Vercel
deploy_frontend() {
    if [ "$SKIP_FRONTEND" = true ]; then
        warn "Skipping frontend deployment"
        return 0
    fi
    
    section "Deploying Frontend to Vercel"
    
    if [ "$VERIFY_ONLY" = true ]; then
        info "Verify-only mode: checking frontend status"
        if command -v vercel &> /dev/null; then
            cd frontend
            vercel ls 2>/dev/null || warn "No Vercel deployments found"
            cd ..
        fi
        return 0
    fi
    
    cd frontend
    
    # Check if .env.local exists and has required variables
    if [ -f ".env.local" ]; then
        if grep -q "NEXT_PUBLIC_API_URL" .env.local; then
            log "Frontend environment variables found"
        else
            warn "NEXT_PUBLIC_API_URL not found in .env.local"
        fi
    else
        warn ".env.local not found"
        info "Make sure environment variables are set in Vercel dashboard"
    fi
    
    # Build test
    step "Testing frontend build..."
    if npm run build > /dev/null 2>&1; then
        log "Frontend build test passed"
    else
        error "Frontend build failed"
        info "Run 'npm run build' in frontend/ to see errors"
        cd ..
        exit 1
    fi
    
    if ! command -v vercel &> /dev/null; then
        warn "Vercel CLI not available"
        info "Deploy manually via Vercel dashboard or GitHub auto-deploy"
        info "  URL: https://vercel.com"
        cd ..
        return 0
    fi
    
    if ! vercel whoami &> /dev/null; then
        error "Not logged in to Vercel"
        info "Run: vercel login"
        cd ..
        exit 1
    fi
    
    # Check if project is linked
    if [ ! -f ".vercel/project.json" ]; then
        warn "Vercel project not linked"
        read -p "Link Vercel project now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            vercel link
        else
            info "Skipping Vercel link. Deploy manually"
            cd ..
            return 0
        fi
    fi
    
    step "Deploying to Vercel..."
    
    # Check if we should push to trigger auto-deploy
    cd ..
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
    cd frontend
    
    if [ -z "$REMOTE" ] || [ "$LOCAL" != "$REMOTE" ]; then
        warn "Local changes not pushed to remote"
        info "Vercel auto-deploy requires code to be pushed to GitHub"
        read -p "Deploy to Vercel now anyway? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            vercel --prod
            log "Frontend deployed to Vercel"
        else
            info "Skipping Vercel deployment. Push to GitHub for auto-deploy"
        fi
    else
        log "Code is up to date on remote"
        read -p "Deploy to Vercel production now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            vercel --prod
            log "Frontend deployed to Vercel"
        else
            info "Vercel will auto-deploy if configured"
        fi
    fi
    
    cd ..
}

# Verify deployment
verify_deployment() {
    section "Verifying Deployment"
    
    # Backend health check
    if [ "$SKIP_BACKEND" = false ]; then
        step "Checking backend health..."
        BACKEND_URL="https://backend-production-72ea.up.railway.app"
        if curl -s -f "${BACKEND_URL}/health" > /dev/null; then
            log "Backend health check passed"
            info "  URL: ${BACKEND_URL}/health"
        else
            warn "Backend health check failed"
            info "  URL: ${BACKEND_URL}/health"
        fi
    fi
    
    # Frontend check (if we know the URL)
    if [ "$SKIP_FRONTEND" = false ]; then
        step "Frontend deployment check..."
        info "Check Vercel dashboard for frontend URL"
        info "  URL: https://vercel.com"
    fi
    
    # Database migrations verification
    if [ "$SKIP_MIGRATIONS" = false ]; then
        step "Verifying database migrations..."
        if command -v railway &> /dev/null && railway whoami &> /dev/null; then
            ./scripts/deploy-production.sh verify
        else
            warn "Cannot verify migrations (Railway CLI not available)"
        fi
    fi
}

# Main execution
main() {
    banner
    
    # Check if verify-only mode
    if [ "$VERIFY_ONLY" = true ]; then
        info "Running in VERIFY-ONLY mode"
        echo ""
    fi
    
    # Prerequisites
    check_prerequisites
    
    # Git status
    check_git_status
    
    # Platform checks
    check_railway
    check_vercel
    
    # Deployment steps
    if [ "$VERIFY_ONLY" = false ]; then
        run_migrations
        deploy_backend
        deploy_frontend
    fi
    
    # Verification
    verify_deployment
    
    # Summary
    section "Deployment Summary"
    
    if [ "$VERIFY_ONLY" = true ]; then
        log "Verification complete"
    else
        log "Deployment process completed"
    fi
    
    echo ""
    info "Next steps:"
    if [ "$SKIP_BACKEND" = false ]; then
        info "  • Monitor backend: railway logs --service backend"
        info "  • Check backend health: curl https://backend-production-72ea.up.railway.app/health"
    fi
    if [ "$SKIP_FRONTEND" = false ]; then
        info "  • Check Vercel dashboard: https://vercel.com"
    fi
    if [ "$SKIP_MIGRATIONS" = false ]; then
        info "  • Verify migrations: ./scripts/deploy-production.sh verify"
    fi
    info "  • Test features: Google OAuth, Stripe checkout, new features"
    echo ""
}

# Run main
main
