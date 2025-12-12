#!/bin/bash

# Configuration
PROJECT_ID="fact-check-mx-934bc"
REGION="us-central1"
DB_INSTANCE_NAME="factcheckr-db"
DB_PASSWORD="87Km.*dtA@GHjkgi" # CHANGE THIS!
REDIS_INSTANCE_NAME="factcheckr-redis"
VPC_CONNECTOR_NAME="factcheckr-conn"
NETWORK="default"

echo "🚀 Starting GCP Setup for Project: $PROJECT_ID"
echo "Region: $REGION"

# 1. Set Project
gcloud config set project $PROJECT_ID

# 2. Enable APIs
echo "Enable APIs..."
gcloud services enable \
    compute.googleapis.com \
    sqladmin.googleapis.com \
    run.googleapis.com \
    redis.googleapis.com \
    servicenetworking.googleapis.com \
    secretmanager.googleapis.com

# 3. Create VPC Connector (required for Cloud Run to talk to SQL/Redis internal IPs)
echo "Creating VPC Connector (this may take a few minutes)..."
# Check if exists first to avoid error
if ! gcloud compute networks vpc-access connectors describe $VPC_CONNECTOR_NAME --region=$REGION > /dev/null 2>&1; then
    gcloud compute networks vpc-access connectors create $VPC_CONNECTOR_NAME \
        --region=$REGION \
        --range=10.8.0.0/28 \
        --network=$NETWORK
else
    echo "VPC Connector $VPC_CONNECTOR_NAME already exists."
fi

# 4. Create Cloud SQL Instance (PostgreSQL)
echo "Creating Cloud SQL Instance (this may take 10-15 minutes)..."
if ! gcloud sql instances describe $DB_INSTANCE_NAME > /dev/null 2>&1; then
    gcloud sql instances create $DB_INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --activation-policy=ALWAYS
        
    gcloud sql users set-password postgres \
        --instance=$DB_INSTANCE_NAME \
        --password=$DB_PASSWORD

    # Create Database
    gcloud sql databases create factcheckr_db --instance=$DB_INSTANCE_NAME
else
    echo "Cloud SQL Instance $DB_INSTANCE_NAME already exists."
fi

# 5. Create Redis (Memorystore)
echo "Creating Redis Instance..."
if ! gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REGION > /dev/null 2>&1; then
    gcloud redis instances create $REDIS_INSTANCE_NAME \
        --size=1 \
        --region=$REGION \
        --tier=basic \
        --redis-version=redis_6_x
else
    echo "Redis Instance $REDIS_INSTANCE_NAME already exists."
fi

# Output Details
echo "✅ Setup Complete!"
echo "----------------------------------------"
echo "Cloud SQL Instance Connection Name:"
gcloud sql instances describe $DB_INSTANCE_NAME --format="value(connectionName)"
echo ""
echo "Redis Host:"
gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REGION --format="value(host)"
echo "----------------------------------------"
echo "⚠️  IMPORTANT: "
echo "1. Change the DB_PASSWORD in this script or manually in Console."
echo "2. Save the outputs above (Connection Name and Redis Host) for your .env file."
