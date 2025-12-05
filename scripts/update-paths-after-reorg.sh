#!/bin/bash
# Update File Paths After Reorganization
# This script updates references to moved files

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
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

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

info "Updating file paths after reorganization..."

# Update Dockerfiles
info "Updating Dockerfiles..."

# backend/Dockerfile
if [ -f "backend/Dockerfile" ]; then
    sed -i.bak 's|COPY start\.sh|COPY scripts/start.sh|g' backend/Dockerfile
    sed -i.bak 's|COPY backend/start\.sh|COPY backend/scripts/start.sh|g' backend/Dockerfile
    rm -f backend/Dockerfile.bak
    log "Updated backend/Dockerfile"
fi

# backend/Dockerfile.beat
if [ -f "backend/Dockerfile.beat" ]; then
    sed -i.bak 's|COPY backend/start-beat\.sh|COPY backend/scripts/start-beat.sh|g' backend/Dockerfile.beat
    sed -i.bak 's|COPY start-beat\.sh|COPY scripts/start-beat.sh|g' backend/Dockerfile.beat
    rm -f backend/Dockerfile.beat.bak
    log "Updated backend/Dockerfile.beat"
fi

# backend/Dockerfile.worker
if [ -f "backend/Dockerfile.worker" ]; then
    sed -i.bak 's|COPY backend/start-worker\.sh|COPY backend/scripts/start-worker.sh|g' backend/Dockerfile.worker
    sed -i.bak 's|COPY start-worker\.sh|COPY scripts/start-worker.sh|g' backend/Dockerfile.worker
    rm -f backend/Dockerfile.worker.bak
    log "Updated backend/Dockerfile.worker"
fi

# Update railway.json if it references scripts
if [ -f "railway.json" ]; then
    if grep -q "start.sh" railway.json; then
        sed -i.bak 's|start\.sh|scripts/start.sh|g' railway.json
        rm -f railway.json.bak
        log "Updated railway.json"
    fi
fi

# Update backend/scripts/*.sh files that reference each other
info "Updating script references..."

for script in backend/scripts/*.sh; do
    if [ -f "$script" ]; then
        # Update references to other scripts
        sed -i.bak 's|\./start-beat\.sh|./scripts/start-beat.sh|g' "$script"
        sed -i.bak 's|\./start-worker\.sh|./scripts/start-worker.sh|g' "$script"
        sed -i.bak 's|\./start\.sh|./scripts/start.sh|g' "$script"
        sed -i.bak 's|start-beat\.sh|scripts/start-beat.sh|g' "$script"
        sed -i.bak 's|start-worker\.sh|scripts/start-worker.sh|g' "$script"
        rm -f "${script}.bak"
    fi
done

log "Updated script references"

# Update scripts/deploy.sh if it references backend scripts
if [ -f "scripts/deploy.sh" ]; then
    sed -i.bak 's|backend/start\.sh|backend/scripts/start.sh|g' scripts/deploy.sh
    sed -i.bak 's|backend/start-beat\.sh|backend/scripts/start-beat.sh|g' scripts/deploy.sh
    sed -i.bak 's|backend/start-worker\.sh|backend/scripts/start-worker.sh|g' scripts/deploy.sh
    rm -f scripts/deploy.sh.bak
    log "Updated scripts/deploy.sh"
fi

# Update scripts/deploy-production.sh
if [ -f "scripts/deploy-production.sh" ]; then
    sed -i.bak 's|backend/start-beat\.sh|backend/scripts/start-beat.sh|g' scripts/deploy-production.sh
    sed -i.bak 's|backend/start-worker\.sh|backend/scripts/start-worker.sh|g' scripts/deploy-production.sh
    rm -f scripts/deploy-production.sh.bak
    log "Updated scripts/deploy-production.sh"
fi

# Update scripts/start-dev.sh
if [ -f "scripts/start-dev.sh" ]; then
    sed -i.bak 's|backend/start\.sh|backend/scripts/start.sh|g' scripts/start-dev.sh
    rm -f scripts/start-dev.sh.bak
    log "Updated scripts/start-dev.sh"
fi

log "Path updates complete!"
info "Review the changes with: git diff"
info "Test the updated files before committing"

