#!/bin/bash
set -e

PROJECT_ID="fact-check-mx-934bc"
REGION="us-central1"

echo "===================================================="
echo "🚀 Preparing to deploy Celery Worker & Beat services"
echo "===================================================="

# Configuration (Extracted from deploy_backend.sh and cloudbuild.yaml)
DB_PASSWORD="FactCheckr_Safe_2025_Secure"
DB_IP="10.239.24.51"
DB_NAME="factcheckr_db"
REDIS_URL="redis://10.239.24.51:6379"

# API Keys (From deploy_backend.sh)
OPENAI_API_KEY="${OPENAI_API_KEY}"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
TWITTER_API_KEY="${TWITTER_API_KEY}"
TWITTER_API_SECRET="${TWITTER_API_SECRET}"
TWITTER_ACCESS_TOKEN="${TWITTER_ACCESS_TOKEN}"
TWITTER_ACCESS_SECRET="${TWITTER_ACCESS_SECRET}"
TWITTER_BEARER_TOKEN="${TWITTER_BEARER_TOKEN}"
SERPER_API_KEY="${SERPER_API_KEY}"
STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY}"
STRIPE_PUBLISHABLE_KEY="${STRIPE_PUBLISHABLE_KEY}"
STRIPE_WEBHOOK_SECRET="${STRIPE_WEBHOOK_SECRET}"
STRIPE_PRO_MONTHLY_PRICE_ID="${STRIPE_PRO_MONTHLY_PRICE_ID}"
STRIPE_PRO_YEARLY_PRICE_ID="${STRIPE_PRO_YEARLY_PRICE_ID}"
STRIPE_TEAM_MONTHLY_PRICE_ID="${STRIPE_TEAM_MONTHLY_PRICE_ID}"
STRIPE_TEAM_YEARLY_PRICE_ID="${STRIPE_TEAM_YEARLY_PRICE_ID}"
JWT_SECRET_KEY="${JWT_SECRET_KEY}"
FIREBASE_CREDENTIALS="${FIREBASE_CREDENTIALS}"

# Encode password correctly using Python
echo "🔐 Encoding database password..."
# Using Cloud SQL Socket via Public IP (since Private IP is not enabled on DB instance)
# Redis is on Private IP (10.239.24.51) so we keep VPC Connector.
INSTANCE_CONNECTION_NAME="fact-check-mx-934bc:us-central1:factcheckr-db"
DATABASE_URL="postgresql://postgres:$DB_PASSWORD@/factcheckr_db?host=/cloudsql/$INSTANCE_CONNECTION_NAME"

# NOTE: For Cloud Run to connect to Cloud SQL via Private IP, we must ensure VPC connector is used.
VPC_CONNECTOR="factcheckr-conn"

# Construct Env Vars String (safe delimiter , now that password is clean)
ENV_VARS="DATABASE_URL=$DATABASE_URL"
ENV_VARS+=",REDIS_URL=$REDIS_URL"
ENV_VARS+=",OPENAI_API_KEY=$OPENAI_API_KEY"
ENV_VARS+=",ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY"
ENV_VARS+=",TWITTER_API_KEY=$TWITTER_API_KEY"
ENV_VARS+=",TWITTER_API_SECRET=$TWITTER_API_SECRET"
ENV_VARS+=",TWITTER_ACCESS_TOKEN=$TWITTER_ACCESS_TOKEN"
ENV_VARS+=",TWITTER_ACCESS_SECRET=$TWITTER_ACCESS_SECRET"
ENV_VARS+=",TWITTER_BEARER_TOKEN=$TWITTER_BEARER_TOKEN"
ENV_VARS+=",SERPER_API_KEY=$SERPER_API_KEY"
ENV_VARS+=",STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY"
ENV_VARS+=",STRIPE_PUBLISHABLE_KEY=$STRIPE_PUBLISHABLE_KEY"
ENV_VARS+=",STRIPE_WEBHOOK_SECRET=$STRIPE_WEBHOOK_SECRET"
ENV_VARS+=",STRIPE_PRO_MONTHLY_PRICE_ID=$STRIPE_PRO_MONTHLY_PRICE_ID"
ENV_VARS+=",STRIPE_PRO_YEARLY_PRICE_ID=$STRIPE_PRO_YEARLY_PRICE_ID"
ENV_VARS+=",STRIPE_TEAM_MONTHLY_PRICE_ID=$STRIPE_TEAM_MONTHLY_PRICE_ID"
ENV_VARS+=",STRIPE_TEAM_YEARLY_PRICE_ID=$STRIPE_TEAM_YEARLY_PRICE_ID"
ENV_VARS+=",JWT_SECRET_KEY=$JWT_SECRET_KEY"
ENV_VARS+=",FIREBASE_CREDENTIALS=$FIREBASE_CREDENTIALS"
ENV_VARS+=",SCRAPING_KEYWORD_PRIORITY=all"
ENV_VARS+=",USE_MULTI_AGENT_VERIFICATION=true"
ENV_VARS+=",CORS_ORIGINS=*"

echo "✅ Environment configuration prepared."

# 2. Build and Deploy Worker
echo "----------------------------------------------------"
echo "🔨 Building Worker Image..."
echo "----------------------------------------------------"
gcloud builds submit -q --config cloudbuild-worker.yaml .

echo "----------------------------------------------------"
echo "🚀 Deploying Worker Service (factcheckr-worker)..."
echo "----------------------------------------------------"
gcloud run deploy factcheckr-worker -q \
    --image gcr.io/$PROJECT_ID/factcheckr-worker \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --min-instances 1 \
    --no-cpu-throttling \
    --vpc-connector $VPC_CONNECTOR \
    --add-cloudsql-instances $INSTANCE_CONNECTION_NAME \
    --set-env-vars "$ENV_VARS"

# 3. Build and Deploy Beat
echo "----------------------------------------------------"
echo "🔨 Building Beat Image (Skipped - reusing worker image)..."
echo "----------------------------------------------------"
# Optimization: Reuse worker image since code/dependencies are identical
# gcloud builds submit -q --config cloudbuild-beat.yaml .

echo "----------------------------------------------------"
echo "🚀 Deploying Beat Service (factcheckr-beat)..."
echo "----------------------------------------------------"
gcloud run deploy factcheckr-beat -q \
    --image gcr.io/$PROJECT_ID/factcheckr-worker \
    --command "scripts/start-beat.sh" \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --min-instances 1 \
    --no-cpu-throttling \
    --vpc-connector $VPC_CONNECTOR \
    --add-cloudsql-instances $INSTANCE_CONNECTION_NAME \
    --set-env-vars "$ENV_VARS"

echo "===================================================="
echo "✅ Deployment of background workers complete!"
echo "===================================================="
