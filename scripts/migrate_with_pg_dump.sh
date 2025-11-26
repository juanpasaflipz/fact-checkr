#!/bin/bash
# Alternative migration using pg_dump/psql (better for large datasets)

set -e

echo "🔄 Migrating data from Supabase to Neon using pg_dump"
echo "=" * 60

# Check for Supabase connection string
if [ -z "$SUPABASE_DATABASE_URL" ]; then
    echo "❌ Error: SUPABASE_DATABASE_URL not set"
    echo ""
    echo "Usage:"
    echo "  SUPABASE_DATABASE_URL='postgresql://...' ./migrate_with_pg_dump.sh"
    echo ""
    echo "Or add to .env:"
    echo "  SUPABASE_DATABASE_URL=postgresql://..."
    exit 1
fi

# Get Neon connection string from .env
source .env 2>/dev/null || true
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL (Neon) not found in .env"
    exit 1
fi

echo ""
echo "1. Exporting data from Supabase..."
BACKUP_FILE="supabase_backup_$(date +%Y%m%d_%H%M%S).sql"
pg_dump "$SUPABASE_DATABASE_URL" \
    --no-owner \
    --no-acl \
    --data-only \
    --inserts \
    > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "   ✅ Export successful: $BACKUP_FILE"
    echo "   📦 File size: $(du -h "$BACKUP_FILE" | cut -f1)"
else
    echo "   ❌ Export failed"
    exit 1
fi

echo ""
echo "2. Importing data to Neon..."
psql "$DATABASE_URL" < "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "   ✅ Import successful!"
else
    echo "   ❌ Import failed"
    echo "   💡 You may need to run migrations first: alembic upgrade head"
    exit 1
fi

echo ""
echo "3. Cleaning up..."
# Keep backup for safety, but offer to remove
echo "   📁 Backup saved as: $BACKUP_FILE"
echo "   💡 You can remove it after verifying the migration"

echo ""
echo "✅ Migration complete!"
echo ""
echo "Next steps:"
echo "1. Verify data: python check_data_counts.py"
echo "2. Test your application"
echo "3. Remove backup file if everything looks good"

