#!/bin/bash

# Configuration
PROJECT_ID="fact-check-mx-934bc"
DB_PASSWORD="FactCheckr_Safe_2025_Secure" # User must replace this again since I don't store it

# Create a temporary JSON file for Firebase Admin Credentials if needed, 
# but for now we are using Client SDK on frontend and Admin SDK on backend.
# The backend needs SERVICE ACCOUNT credentials. 
# We typically mount this as a secret, but for now we can try passing as base664 or just rely on Default Application Credentials (ADC) on Cloud Run!
# Cloud Run automatically has access to GCP resources if IAM is set up.
# For Firebase Admin SDK to work without a key file, we just need to give the Cloud Run Service Account "Firebase Admin" role.

echo "🚀 Deploying to Cloud Run..."

# Encode password to handle special characters like @, :, /
DB_PASSWORD_ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$DB_PASSWORD'''))")

gcloud builds submit --config cloudbuild.yaml \
    --project $PROJECT_ID \
    --substitutions _DB_PASSWORD="$DB_PASSWORD_ENCODED",_OPENAI_API_KEY="${OPENAI_API_KEY}",_ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}",_TWITTER_API_KEY="${TWITTER_API_KEY}",_TWITTER_API_SECRET="${TWITTER_API_SECRET}",_TWITTER_ACCESS_TOKEN="${TWITTER_ACCESS_TOKEN}",_TWITTER_ACCESS_SECRET="${TWITTER_ACCESS_SECRET}",_TWITTER_BEARER_TOKEN="${TWITTER_BEARER_TOKEN}",_SERPER_API_KEY="${SERPER_API_KEY}",_STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY}",_STRIPE_PUBLISHABLE_KEY="${STRIPE_PUBLISHABLE_KEY}",_STRIPE_WEBHOOK_SECRET="${STRIPE_WEBHOOK_SECRET}",_STRIPE_PRO_MONTHLY_PRICE_ID="${STRIPE_PRO_MONTHLY_PRICE_ID}",_STRIPE_PRO_YEARLY_PRICE_ID="${STRIPE_PRO_YEARLY_PRICE_ID}",_STRIPE_TEAM_MONTHLY_PRICE_ID="${STRIPE_TEAM_MONTHLY_PRICE_ID}",_STRIPE_TEAM_YEARLY_PRICE_ID="${STRIPE_TEAM_YEARLY_PRICE_ID}",_JWT_SECRET_KEY="${JWT_SECRET_KEY}",_FIREBASE_CREDENTIALS_JSON="{}" 
