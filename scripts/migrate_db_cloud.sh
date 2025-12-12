#!/bin/bash
set -e

# Configuration
PROJECT_ID="fact-check-mx-934bc"
INSTANCE_NAME="factcheckr-db"
DATABASE_NAME="factcheckr_db"
REGION="us-central1"
BUCKET_NAME="factcheckr-migration-$(date +%s)"
DUMP_FILE="migration_dump.sql"

echo "🚀 Starting FactCheckr Database Migration"
echo "Target: Project $PROJECT_ID | Instance $INSTANCE_NAME"

# 1. Get Source Database URL
if [ -z "$SOURCE_DB_URL" ]; then
    echo -n "Enter Railway Database URL (postgresql://...): "
    read -s SOURCE_DB_URL
    echo ""
fi

if [ -z "$SOURCE_DB_URL" ]; then
    echo "❌ Error: Source Database URL is required."
    exit 1
fi

# 2. Dump Database
echo "📦 Dumping data from Railway..."
# --no-owner --no-acl: Crucial for Cloud SQL compatibility
# Using quote around variable to handle special chars
pg_dump "${SOURCE_DB_URL}" \
    --no-owner \
    --no-acl \
    --format=p \
    --file="$DUMP_FILE"

echo "✅ Dump successful: $(ls -lh $DUMP_FILE | awk '{print $5}')"

# 3. Create Temporary GCS Bucket
echo "☁️  Creating temporary GCS bucket gs://$BUCKET_NAME..."
gcloud storage buckets create gs://$BUCKET_NAME --project=$PROJECT_ID --location=$REGION

# 4. Upload Dump to GCS
echo "⬆️  Uploading dump to GCS..."
gcloud storage cp $DUMP_FILE gs://$BUCKET_NAME/$DUMP_FILE

# 5. Grant Cloud SQL Service Account Permissions
echo "🔑 configuring IAM permissions..."
# Get Cloud SQL Service Account Email
SQL_SA_EMAIL=$(gcloud sql instances describe $INSTANCE_NAME --project=$PROJECT_ID --format="value(serviceAccountEmailAddress)")
echo "   SA Email: $SQL_SA_EMAIL"

# Grant objectAdmin (read/write) to the bucket
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
    --member="serviceAccount:$SQL_SA_EMAIL" \
    --role="roles/storage.objectViewer"

# 6. Import to Cloud SQL
echo "🔄 Importing data into Cloud SQL (factcheckr_db)..."
gcloud sql import sql $INSTANCE_NAME gs://$BUCKET_NAME/$DUMP_FILE \
    --database=$DATABASE_NAME \
    --project=$PROJECT_ID \
    -q

# 7. Cleanup
echo "🧹 Cleaning up..."
gcloud storage rm -r gs://$BUCKET_NAME
rm $DUMP_FILE

echo "✅ MIGRATION COMPLETE!"
echo "The database $DATABASE_NAME on $INSTANCE_NAME has been updated."
