#!/bin/bash
# Repository Reorganization Script
# This script reorganizes the repository structure for better maintainability

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

info() {
    echo -e "${BLUE}[i]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1" >&2
}

section() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Get the repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

section "Repository Reorganization"

info "Repository root: $REPO_ROOT"
info "This script will reorganize files and folders"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    error "Aborted by user"
    exit 1
fi

# 1. Create new directory structure
section "Creating Directory Structure"

mkdir -p backend/scripts
mkdir -p backend/config
mkdir -p backend/tests
mkdir -p docs/features
mkdir -p docs/guides
mkdir -p .temp

log "Directory structure created"

# 2. Move backend scripts
section "Organizing Backend Scripts"

# Move startup scripts to backend/scripts
if [ -f "backend/start-beat.sh" ]; then
    mv backend/start-beat.sh backend/scripts/
    log "Moved start-beat.sh → backend/scripts/"
fi

if [ -f "backend/start-worker.sh" ]; then
    mv backend/start-worker.sh backend/scripts/
    log "Moved start-worker.sh → backend/scripts/"
fi

if [ -f "backend/start.sh" ]; then
    mv backend/start.sh backend/scripts/
    log "Moved start.sh → backend/scripts/"
fi

if [ -f "backend/start_workers.sh" ]; then
    mv backend/start_workers.sh backend/scripts/start_local.sh
    log "Moved start_workers.sh → backend/scripts/start_local.sh"
fi

if [ -f "backend/run_worker.sh" ]; then
    mv backend/run_worker.sh backend/scripts/
    log "Moved run_worker.sh → backend/scripts/"
fi

if [ -f "backend/backend_manager.sh" ]; then
    mv backend/backend_manager.sh backend/scripts/
    log "Moved backend_manager.sh → backend/scripts/"
fi

if [ -f "backend/worker_manager.sh" ]; then
    mv backend/worker_manager.sh backend/scripts/
    log "Moved worker_manager.sh → backend/scripts/"
fi

# Move test files to backend/tests
if [ -f "backend/check_db.py" ]; then
    mv backend/check_db.py backend/tests/
    log "Moved check_db.py → backend/tests/"
fi

if [ -f "backend/test_startup.py" ]; then
    mv backend/test_startup.py backend/tests/
    log "Moved test_startup.py → backend/tests/"
fi

# Move supervisor config to backend/config
if [ -f "backend/supervisor_celery.conf" ]; then
    mv backend/supervisor_celery.conf backend/config/
    log "Moved supervisor_celery.conf → backend/config/"
fi

# 3. Move Railway configs to backend/config
section "Organizing Configuration Files"

if [ -f "backend/railway.json" ]; then
    mv backend/railway.json backend/config/
    log "Moved railway.json → backend/config/"
fi

if [ -f "backend/railway-beat.json" ]; then
    mv backend/railway-beat.json backend/config/
    log "Moved railway-beat.json → backend/config/"
fi

if [ -f "backend/railway-worker.json" ]; then
    mv backend/railway-worker.json backend/config/
    log "Moved railway-worker.json → backend/config/"
fi

# 4. Organize root-level files
section "Organizing Root-Level Files"

# Move deployment files to scripts
if [ -f "deploy.sh" ]; then
    mv deploy.sh scripts/
    log "Moved deploy.sh → scripts/"
fi

if [ -f "start-dev.sh" ]; then
    mv start-dev.sh scripts/
    log "Moved start-dev.sh → scripts/"
fi

# Move deployment status to docs
if [ -f "DEPLOYMENT_STATUS.md" ]; then
    mv DEPLOYMENT_STATUS.md docs/deployment/
    log "Moved DEPLOYMENT_STATUS.md → docs/deployment/"
fi

# 5. Organize documentation
section "Organizing Documentation"

# Move feature docs to docs/features
if [ -f "docs/PREMIUM_FEATURES_IMPLEMENTATION.md" ]; then
    mv docs/PREMIUM_FEATURES_IMPLEMENTATION.md docs/features/
    log "Moved PREMIUM_FEATURES_IMPLEMENTATION.md → docs/features/"
fi

if [ -f "docs/PREDICTION_MARKET_ENHANCEMENTS.md" ]; then
    mv docs/PREDICTION_MARKET_ENHANCEMENTS.md docs/features/
    log "Moved PREDICTION_MARKET_ENHANCEMENTS.md → docs/features/"
fi

if [ -f "docs/VERIFICATION_PROCESS_ANALYSIS.md" ]; then
    mv docs/VERIFICATION_PROCESS_ANALYSIS.md docs/features/
    log "Moved VERIFICATION_PROCESS_ANALYSIS.md → docs/features/"
fi

if [ -f "docs/VERIFICATION_IMPLEMENTATION_SUMMARY.md" ]; then
    mv docs/VERIFICATION_IMPLEMENTATION_SUMMARY.md docs/features/
    log "Moved VERIFICATION_IMPLEMENTATION_SUMMARY.md → docs/features/"
fi

if [ -f "docs/VERIFICATION_ENHANCEMENT_GUIDE.md" ]; then
    mv docs/VERIFICATION_ENHANCEMENT_GUIDE.md docs/features/
    log "Moved VERIFICATION_ENHANCEMENT_GUIDE.md → docs/features/"
fi

if [ -f "docs/DATA_COLLECTION_ANALYSIS.md" ]; then
    mv docs/DATA_COLLECTION_ANALYSIS.md docs/features/
    log "Moved DATA_COLLECTION_ANALYSIS.md → docs/features/"
fi

if [ -f "docs/DATA_COLLECTION_IMPLEMENTATION.md" ]; then
    mv docs/DATA_COLLECTION_IMPLEMENTATION.md docs/features/
    log "Moved DATA_COLLECTION_IMPLEMENTATION.md → docs/features/"
fi

if [ -f "docs/DATA_COLLECTION_QUICK_REFERENCE.md" ]; then
    mv docs/DATA_COLLECTION_QUICK_REFERENCE.md docs/features/
    log "Moved DATA_COLLECTION_QUICK_REFERENCE.md → docs/features/"
fi

# Move guide docs to docs/guides
if [ -f "docs/STRIPE_SETUP_GUIDE.md" ]; then
    mv docs/STRIPE_SETUP_GUIDE.md docs/guides/
    log "Moved STRIPE_SETUP_GUIDE.md → docs/guides/"
fi

if [ -f "docs/STRIPE_QUICK_CHECKLIST.md" ]; then
    mv docs/STRIPE_QUICK_CHECKLIST.md docs/guides/
    log "Moved STRIPE_QUICK_CHECKLIST.md → docs/guides/"
fi

if [ -f "docs/TWITTER_BASIC_UPGRADE.md" ]; then
    mv docs/TWITTER_BASIC_UPGRADE.md docs/guides/
    log "Moved TWITTER_BASIC_UPGRADE.md → docs/guides/"
fi

if [ -f "docs/TWITTER_SCRAPING_SCHEDULE.md" ]; then
    mv docs/TWITTER_SCRAPING_SCHEDULE.md docs/guides/
    log "Moved TWITTER_SCRAPING_SCHEDULE.md → docs/guides/"
fi

if [ -f "docs/SCRAPING_CRITERIA.md" ]; then
    mv docs/SCRAPING_CRITERIA.md docs/guides/
    log "Moved SCRAPING_CRITERIA.md → docs/guides/"
fi

if [ -f "docs/SCRAPING_KEYWORDS_QUICK_REFERENCE.md" ]; then
    mv docs/SCRAPING_KEYWORDS_QUICK_REFERENCE.md docs/guides/
    log "Moved SCRAPING_KEYWORDS_QUICK_REFERENCE.md → docs/guides/"
fi

# Move deployment docs
if [ -f "docs/RAILWAY_DEPLOYMENT.md" ]; then
    mv docs/RAILWAY_DEPLOYMENT.md docs/deployment/
    log "Moved RAILWAY_DEPLOYMENT.md → docs/deployment/"
fi

if [ -f "docs/VERCEL_DEPLOYMENT.md" ]; then
    mv docs/VERCEL_DEPLOYMENT.md docs/deployment/
    log "Moved VERCEL_DEPLOYMENT.md → docs/deployment/"
fi

if [ -f "docs/DEPLOYMENT_CHECKLIST.md" ]; then
    # Check if duplicate exists
    if [ ! -f "docs/deployment/DEPLOYMENT_CHECKLIST.md" ]; then
        mv docs/DEPLOYMENT_CHECKLIST.md docs/deployment/
        log "Moved DEPLOYMENT_CHECKLIST.md → docs/deployment/"
    else
        rm docs/DEPLOYMENT_CHECKLIST.md
        warn "Removed duplicate DEPLOYMENT_CHECKLIST.md"
    fi
fi

# Move cleanup summary to archive
if [ -f "docs/CLEANUP_SUMMARY.md" ]; then
    mv docs/CLEANUP_SUMMARY.md docs/archive/
    log "Moved CLEANUP_SUMMARY.md → docs/archive/"
fi

# 6. Move ENV_SETUP files to docs
section "Organizing Environment Documentation"

if [ -f "backend/ENV_SETUP.md" ]; then
    mv backend/ENV_SETUP.md docs/setup/
    log "Moved backend/ENV_SETUP.md → docs/setup/"
fi

if [ -f "frontend/ENV_SETUP.md" ]; then
    mv frontend/ENV_SETUP.md docs/setup/
    log "Moved frontend/ENV_SETUP.md → docs/setup/"
fi

if [ -f "frontend/ENV_PRODUCTION.md" ]; then
    mv frontend/ENV_PRODUCTION.md docs/setup/
    log "Moved frontend/ENV_PRODUCTION.md → docs/setup/"
fi

# 7. Remove old/duplicate files
section "Cleaning Up Duplicates"

# Remove old checklist
if [ -f "docs/deployment/checklist-old.md" ]; then
    rm docs/deployment/checklist-old.md
    log "Removed old checklist-old.md"
fi

# Remove old stripe setup
if [ -f "docs/integrations/stripe-setup-old.md" ]; then
    rm docs/integrations/stripe-setup-old.md
    log "Removed old stripe-setup-old.md"
fi

# 8. Update references in key files
section "Updating File References"

# Update backend scripts to reference new locations
info "Note: You may need to update script paths in:"
info "  - Dockerfiles"
info "  - Railway configs"
info "  - Other scripts that reference moved files"

# 9. Create symlinks for backward compatibility (optional)
section "Creating Backward Compatibility"

# Create symlinks for commonly referenced files
if [ -f "backend/scripts/start.sh" ]; then
    ln -sf scripts/start.sh backend/start.sh 2>/dev/null || true
    log "Created symlink: backend/start.sh → backend/scripts/start.sh"
fi

# 10. Summary
section "Reorganization Complete"

log "Repository reorganization completed!"
echo ""
info "Summary of changes:"
info "  ✓ Backend scripts moved to backend/scripts/"
info "  ✓ Test files moved to backend/tests/"
info "  ✓ Config files moved to backend/config/"
info "  ✓ Documentation organized into features/ and guides/"
info "  ✓ Duplicate files removed"
info "  ✓ Environment docs consolidated"
echo ""
warn "Next steps:"
warn "  1. Review moved files"
warn "  2. Update any hardcoded paths in scripts/configs"
warn "  3. Update Dockerfiles if they reference moved files"
warn "  4. Test that everything still works"
warn "  5. Commit changes to git"

