#!/bin/bash
# Production Deployment Script for Railway
# Automates database migrations and deployment verification
# Usage: ./scripts/deploy-production.sh [railway|local|verify]

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

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
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

check_requirements() {
    section "Checking Requirements"
    
    local missing=0
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
        missing=1
    else
        log "Python 3 found: $(python3 --version)"
    fi
    
    # Check Alembic
    if ! command -v alembic &> /dev/null; then
        error "Alembic is not installed. Run: pip install alembic"
        missing=1
    else
        log "Alembic found: $(alembic --version | head -n1)"
    fi
    
    # Check Railway CLI (optional)
    if command -v railway &> /dev/null; then
        log "Railway CLI found: $(railway --version 2>/dev/null || echo 'installed')"
    else
        warn "Railway CLI not found (optional, for Railway deployments)"
    fi
    
    if [ $missing -eq 1 ]; then
        error "Missing required tools. Please install them first."
        exit 1
    fi
}

check_env_vars() {
    section "Checking Environment Variables"
    
    local missing=0
    local warnings=0
    
    # Required variables
    if [ -z "$DATABASE_URL" ]; then
        error "DATABASE_URL is not set"
        missing=1
    else
        log "DATABASE_URL is set"
        # Mask password in output
        DB_MASKED=$(echo "$DATABASE_URL" | sed 's/:[^@]*@/:***@/')
        info "  → $DB_MASKED"
    fi
    
    if [ -z "$REDIS_URL" ]; then
        warn "REDIS_URL is not set (required for Celery)"
        warnings=1
    else
        log "REDIS_URL is set"
    fi
    
    if [ -z "$JWT_SECRET_KEY" ]; then
        error "JWT_SECRET_KEY is not set"
        missing=1
    else
        log "JWT_SECRET_KEY is set"
    fi
    
    # Optional but recommended
    if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
        warn "No AI API keys set (ANTHROPIC_API_KEY or OPENAI_API_KEY)"
        warnings=1
    else
        log "AI API key(s) configured"
    fi
    
    if [ -z "$STRIPE_SECRET_KEY" ]; then
        warn "STRIPE_SECRET_KEY not set (subscriptions won't work)"
        warnings=1
    else
        log "Stripe configured"
    fi
    
    if [ $missing -eq 1 ]; then
        error "Missing required environment variables. Aborting."
        echo ""
        info "Set environment variables:"
        info "  export DATABASE_URL='postgresql://...'"
        info "  export JWT_SECRET_KEY='your-secret-key'"
        exit 1
    fi
    
    if [ $warnings -eq 1 ]; then
        warn "Some optional variables are missing (deployment may have limited functionality)"
    fi
}

test_db_connection() {
    section "Testing Database Connection"
    
    if [ -z "$DATABASE_URL" ]; then
        error "DATABASE_URL not set, skipping connection test"
        return 1
    fi
    
    info "Testing connection to database..."
    
    python3 << EOF
import os
import sys
from sqlalchemy import create_engine, text

try:
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    
    engine = create_engine(db_url, connect_args={"connect_timeout": 10})
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✓ Connected to PostgreSQL: {version[:50]}...")
        sys.exit(0)
except Exception as e:
    print(f"✗ Connection failed: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        log "Database connection successful"
        return 0
    else
        error "Database connection failed"
        return 1
    fi
}

test_redis_connection() {
    section "Testing Redis Connection"
    
    if [ -z "$REDIS_URL" ]; then
        warn "REDIS_URL not set, skipping Redis test"
        return 0
    fi
    
    info "Testing connection to Redis..."
    
    python3 << EOF
import os
import sys
import redis

try:
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    r = redis.from_url(redis_url)
    r.ping()
    print("✓ Connected to Redis")
    sys.exit(0)
except Exception as e:
    print(f"✗ Redis connection failed: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        log "Redis connection successful"
        return 0
    else
        warn "Redis connection failed (Celery won't work without it)"
        return 1
    fi
}

run_migrations() {
    section "Running Database Migrations"
    
    cd backend
    
    # Activate venv if it exists
    if [ -d "venv" ]; then
        info "Activating virtual environment..."
        source venv/bin/activate
    fi
    
    # Check if we're in the right directory
    if [ ! -f "alembic.ini" ]; then
        error "alembic.ini not found. Are you in the backend directory?"
        exit 1
    fi
    
    # Get current migration
    info "Checking current database state..."
    CURRENT=$(alembic current 2>&1 | grep -oP '(?<=\(head\)|\(head, )\w+' || echo "none")
    info "Current migration: ${CURRENT:-none}"
    
    # Run migrations
    info "Running migrations to head..."
    if alembic upgrade head; then
        log "Migrations completed successfully"
        
        # Verify new tables exist
        info "Verifying new tables..."
        python3 << EOF
import os
import sys
from sqlalchemy import create_engine, inspect

try:
    db_url = os.getenv('DATABASE_URL')
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = [
        'market_proposals',
        'user_market_stats',
        'market_notifications',
        'referral_bonuses'
    ]
    
    missing = []
    for table in required_tables:
        if table in tables:
            print(f"✓ Table '{table}' exists")
        else:
            print(f"✗ Table '{table}' missing")
            missing.append(table)
    
    if missing:
        print(f"\n⚠️  Missing tables: {', '.join(missing)}")
        sys.exit(1)
    else:
        print("\n✓ All premium feature tables verified")
        sys.exit(0)
except Exception as e:
    print(f"✗ Verification failed: {e}")
    sys.exit(1)
EOF
        
        if [ $? -eq 0 ]; then
            log "All premium feature tables verified"
        else
            warn "Some tables may be missing (this is OK if migrations are still running)"
        fi
    else
        error "Migration failed"
        exit 1
    fi
    
    cd ..
}

verify_services() {
    section "Verifying Service Configuration"
    
    info "Checking Railway configuration files..."
    
    local services_ok=0
    
    # Check main backend
    if [ -f "railway.json" ]; then
        log "Main backend service configured (railway.json)"
        services_ok=$((services_ok + 1))
    else
        warn "railway.json not found"
    fi
    
    # Check Celery Beat
    if [ -f "backend/railway-beat.json" ] && [ -f "backend/Dockerfile.beat" ]; then
        log "Celery Beat service configured"
        services_ok=$((services_ok + 1))
    else
        warn "Celery Beat configuration missing"
    fi
    
    # Check Celery Worker
    if [ -f "backend/railway-worker.json" ] && [ -f "backend/Dockerfile.worker" ]; then
        log "Celery Worker service configured"
        services_ok=$((services_ok + 1))
    else
        warn "Celery Worker configuration missing"
    fi
    
    if [ $services_ok -eq 3 ]; then
        log "All 3 services are configured"
    else
        warn "Some services may not be configured ($services_ok/3 found)"
    fi
}

deploy_railway() {
    section "Deploying to Railway"
    
    if ! command -v railway &> /dev/null; then
        error "Railway CLI not found"
        info "Install it: npm i -g @railway/cli"
        info "Or deploy manually via Railway dashboard"
        exit 1
    fi
    
    info "Checking Railway login..."
    if railway whoami &> /dev/null; then
        log "Logged in to Railway"
    else
        error "Not logged in to Railway"
        info "Run: railway login"
        exit 1
    fi
    
    info "Running migrations on Railway..."
    info "Note: Running from backend directory where alembic.ini is located"
    
    # Railway run needs to be executed from the backend directory
    # Use --command to change directory and run alembic
    if railway run --service backend sh -c "cd backend && alembic upgrade head"; then
        log "Migrations completed on Railway"
    else
        error "Failed to run migrations on Railway"
        info "Trying alternative method..."
        # Alternative: if Railway service root is already backend
        if railway run --service backend alembic upgrade head 2>/dev/null; then
            log "Migrations completed on Railway (alternative method)"
        else
            error "Migration failed. You may need to run migrations manually:"
            info "  railway run --service backend sh -c 'cd backend && alembic upgrade head'"
            exit 1
        fi
    fi
    
    info "Deployment steps:"
    info "1. Push code to GitHub (if using auto-deploy)"
    info "2. Or manually trigger deployment in Railway dashboard"
    info "3. Verify all 3 services are running:"
    info "   - Backend (API)"
    info "   - Celery Beat (Scheduler)"
    info "   - Celery Worker (Task Executor)"
}

deploy_local() {
    section "Local Deployment Preparation"
    
    check_requirements
    check_env_vars
    test_db_connection
    test_redis_connection
    run_migrations
    verify_services
    
    section "Deployment Complete"
    log "Local deployment preparation complete!"
    echo ""
    info "Next steps:"
    info "1. Start backend: cd backend && gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker"
    info "2. Start Celery Beat: cd backend && ./start-beat.sh"
    info "3. Start Celery Worker: cd backend && ./start-worker.sh"
}

verify_deployment() {
    section "Verifying Deployment"
    
    # Check if we should use Railway's environment
    if command -v railway &> /dev/null && railway whoami &> /dev/null; then
        info "Using Railway's environment for verification"
        verify_railway_deployment
    else
        # Fall back to local environment
        check_env_vars
        
        if [ -z "$DATABASE_URL" ]; then
            error "Cannot verify without DATABASE_URL"
            error "Either set local DATABASE_URL or ensure Railway CLI is configured"
            exit 1
        fi
        
        verify_local_deployment
    fi
}

verify_railway_deployment() {
    info "Verifying deployment on Railway..."
    info "Using Railway's environment variables with local Python"
    
    # Get Railway environment variables and use them locally
    # Railway run exports env vars, so we can use them in our Python script
    cd backend
    
    # Activate venv if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Run verification using Railway's environment variables
    railway run --service backend python3 << 'PYEOF'
import os
import sys
from sqlalchemy import create_engine, inspect, text

try:
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print('✗ DATABASE_URL not found in Railway environment')
        sys.exit(1)
    
    print(f'✓ Connected to Railway database')
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f'Found {len(tables)} tables in database')
    print('')
    
    # Check premium feature tables
    premium_tables = {
        'market_proposals': 'Market proposals',
        'user_market_stats': 'User market statistics',
        'market_notifications': 'Market notifications',
        'referral_bonuses': 'Referral bonuses'
    }
    
    all_ok = True
    for table, desc in premium_tables.items():
        if table in tables:
            print(f'✓ {desc} ({table})')
        else:
            print(f'✗ {desc} ({table}) - MISSING')
            all_ok = False
    
    # Check users table for new columns
    if 'users' in tables:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('referred_by_user_id', 'referral_code')
            """))
            columns = [row[0] for row in result]
            
            if 'referred_by_user_id' in columns:
                print('✓ Users.referred_by_user_id column')
            else:
                print('✗ Users.referred_by_user_id column - MISSING')
                all_ok = False
                
            if 'referral_code' in columns:
                print('✓ Users.referral_code column')
            else:
                print('✗ Users.referral_code column - MISSING')
                all_ok = False
    
    print('')
    if all_ok:
        print('✓ All premium features are deployed!')
        sys.exit(0)
    else:
        print('✗ Some features are missing. Run migrations first.')
        sys.exit(1)
        
except Exception as e:
    print(f'✗ Verification failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF
    
    local exit_code=$?
    cd ..
    
    if [ $exit_code -eq 0 ]; then
        log "Deployment verification successful on Railway!"
    else
        error "Deployment verification failed on Railway"
        exit 1
    fi
}

verify_local_deployment() {
    
    info "Checking database tables..."
    python3 << EOF
import os
import sys
from sqlalchemy import create_engine, inspect, text

try:
    db_url = os.getenv('DATABASE_URL')
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"Found {len(tables)} tables in database")
    print("")
    
    # Check premium feature tables
    premium_tables = {
        'market_proposals': 'Market proposals',
        'user_market_stats': 'User market statistics',
        'market_notifications': 'Market notifications',
        'referral_bonuses': 'Referral bonuses'
    }
    
    all_ok = True
    for table, desc in premium_tables.items():
        if table in tables:
            print(f"✓ {desc} ({table})")
        else:
            print(f"✗ {desc} ({table}) - MISSING")
            all_ok = False
    
    # Check users table for new columns
    if 'users' in tables:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('referred_by_user_id', 'referral_code')
            """))
            columns = [row[0] for row in result]
            
            if 'referred_by_user_id' in columns:
                print("✓ Users.referred_by_user_id column")
            else:
                print("✗ Users.referred_by_user_id column - MISSING")
                all_ok = False
                
            if 'referral_code' in columns:
                print("✓ Users.referral_code column")
            else:
                print("✗ Users.referral_code column - MISSING")
                all_ok = False
    
    print("")
    if all_ok:
        print("✓ All premium features are deployed!")
        sys.exit(0)
    else:
        print("✗ Some features are missing. Run migrations first.")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Verification failed: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        log "Deployment verification successful!"
    else
        error "Deployment verification failed"
        exit 1
    fi
}

# Main
case "${1:-local}" in
    railway)
        check_requirements
        # Skip local env check for Railway - it uses Railway's environment automatically
        info "Skipping local environment check - Railway CLI uses Railway's environment variables"
        deploy_railway
        ;;
    local)
        deploy_local
        ;;
    verify)
        verify_deployment
        ;;
    *)
        echo "Usage: $0 [railway|local|verify]"
        echo ""
        echo "Commands:"
        echo "  railway  - Deploy to Railway (runs migrations via Railway CLI)"
        echo "  local    - Prepare for local deployment (default)"
        echo "  verify   - Verify deployment status"
        echo ""
        echo "Examples:"
        echo "  $0 local              # Prepare local deployment"
        echo "  $0 railway             # Deploy to Railway"
        echo "  $0 verify              # Verify current deployment"
        exit 1
        ;;
esac

