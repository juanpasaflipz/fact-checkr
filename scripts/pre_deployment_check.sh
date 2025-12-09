#!/bin/bash
# Pre-deployment verification script

set -e

echo "=========================================="
echo "PRE-DEPLOYMENT VERIFICATION"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# Check 1: .env files are in .gitignore
echo "1. Checking .env files are ignored..."
if git check-ignore backend/.env frontend/.env.local .env > /dev/null 2>&1; then
    echo "   ✅ .env files are properly ignored"
else
    echo "   ⚠️  WARNING: Some .env files may not be ignored"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 2: No hardcoded secrets in code
echo ""
echo "2. Checking for hardcoded secrets..."
if grep -r "sk_live_\|sk_test_\|pk_live_\|pk_test_" backend/ --exclude-dir=venv --exclude-dir=__pycache__ --exclude-dir=.git 2>/dev/null | grep -v "example\|test\|mock" | grep -v ".pyc" | grep -v ".md" > /dev/null; then
    echo "   ❌ ERROR: Found potential hardcoded secrets!"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ No hardcoded secrets found"
fi

# Check 3: Dockerfiles exist
echo ""
echo "3. Checking Dockerfiles..."
if [ -f "backend/Dockerfile" ] && [ -f "backend/Dockerfile.worker" ] && [ -f "frontend/Dockerfile" ]; then
    echo "   ✅ All Dockerfiles present"
else
    echo "   ❌ ERROR: Missing Dockerfiles"
    ERRORS=$((ERRORS + 1))
fi

# Check 4: docker-compose.yml exists
echo ""
echo "4. Checking docker-compose.yml..."
if [ -f "docker-compose.yml" ]; then
    echo "   ✅ docker-compose.yml present"
else
    echo "   ❌ ERROR: docker-compose.yml missing"
    ERRORS=$((ERRORS + 1))
fi

# Check 5: env.example exists
echo ""
echo "5. Checking env.example..."
if [ -f "env.example" ]; then
    echo "   ✅ env.example present"
else
    echo "   ⚠️  WARNING: env.example missing"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 6: Railway config exists
echo ""
echo "6. Checking Railway configuration..."
if [ -f "railway.toml" ]; then
    echo "   ✅ railway.toml present"
else
    echo "   ⚠️  WARNING: railway.toml missing (optional for Railway deployment)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 7: Database migrations are up to date
echo ""
echo "7. Checking database migrations..."
cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
    if python scripts/verify_setup.py 2>&1 | grep -q "Database is up to date"; then
        echo "   ✅ Database migrations are up to date"
    else
        echo "   ⚠️  WARNING: Database migrations may not be up to date"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "   ⚠️  WARNING: Cannot verify migrations (venv not found)"
    WARNINGS=$((WARNINGS + 1))
fi
cd ..

# Check 8: No uncommitted critical files
echo ""
echo "8. Checking git status..."
if git status --porcelain | grep -E "\.env$|\.env\.local$|secrets" > /dev/null; then
    echo "   ❌ ERROR: .env or secrets files are staged/uncommitted!"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ No sensitive files in git staging"
fi

# Summary
echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "✅ Ready for deployment!"
    exit 0
else
    echo "❌ Please fix errors before deploying"
    exit 1
fi
