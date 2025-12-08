#!/bin/bash

# Deployment script for new market categories feature
# This script helps verify deployment readiness

set -e

echo "🚀 New Market Categories Deployment Checklist"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "backend/main.py" ] || [ ! -f "frontend/package.json" ]; then
    echo -e "${RED}❌ Error: Must run from project root${NC}"
    exit 1
fi

echo "📋 Pre-Deployment Checks"
echo "----------------------"

# Check git status
echo -n "Checking git status... "
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Uncommitted changes${NC}"
    echo "   Run: git status"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Clean${NC}"
fi

# Check if on main branch
echo -n "Checking branch... "
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}⚠️  Not on main branch (currently: $CURRENT_BRANCH)${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ On main branch${NC}"
fi

# Check backend files
echo -n "Checking backend files... "
if grep -q "sports.*financial-markets.*weather.*social-incidents" backend/app/routers/auth.py 2>/dev/null; then
    echo -e "${GREEN}✅ Backend updated${NC}"
else
    echo -e "${RED}❌ Backend may not have new categories${NC}"
    exit 1
fi

# Check frontend files
echo -n "Checking frontend files... "
if grep -q "sports.*financial-markets.*weather.*social-incidents" frontend/src/app/markets/page.tsx 2>/dev/null; then
    echo -e "${GREEN}✅ Frontend updated${NC}"
else
    echo -e "${RED}❌ Frontend may not have new categories${NC}"
    exit 1
fi

# Check test script exists
echo -n "Checking test script... "
if [ -f "scripts/test_new_categories.py" ]; then
    echo -e "${GREEN}✅ Test script exists${NC}"
else
    echo -e "${YELLOW}⚠️  Test script not found${NC}"
fi

echo ""
echo "📦 Deployment Steps"
echo "------------------"
echo ""
echo "1. Commit and push changes:"
echo "   git add ."
echo "   git commit -m 'feat: Add new market categories'"
echo "   git push origin main"
echo ""
echo "2. Backend (Railway) will auto-deploy"
echo "   - Check Railway dashboard"
echo "   - Verify health check: curl https://fact-checkr-production.up.railway.app/health"
echo ""
echo "3. Frontend (Vercel) will auto-deploy"
echo "   - Check Vercel dashboard"
echo "   - Verify build completes"
echo ""
echo "4. Post-deployment verification:"
echo "   - Visit /markets page"
echo "   - Verify new category tabs appear"
echo "   - Test filtering by each category"
echo ""
echo "📚 Full deployment guide: docs/deployment/NEW_CATEGORIES_DEPLOYMENT.md"
echo ""

read -p "Ready to deploy? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Deployment Checklist:"
    echo "  [ ] git add ."
    echo "  [ ] git commit -m 'feat: Add new market categories'"
    echo "  [ ] git push origin main"
    echo "  [ ] Monitor Railway deployment"
    echo "  [ ] Monitor Vercel deployment"
    echo "  [ ] Run post-deployment tests"
    echo ""
    echo "Good luck! 🎉"
else
    echo "Deployment cancelled."
    exit 0
fi

