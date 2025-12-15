#!/bin/bash

# Source the .env file if it exists
if [ -f .env ]; then
  # Use grep to filter out comments and empty lines, then export
  export $(grep -v '^#' .env | xargs)
fi

# Set default values for missing keys to avoid build errors
# NOTE: These should be replaced with real values in production or via .env
export _DB_PASSWORD=${DB_PASSWORD:-"factcheckr_db_password"}
export _STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY:-"sk_test_placeholder"}
export _STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY:-"pk_test_placeholder"}
export _STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET:-"whsec_placeholder"}
export _STRIPE_PRO_MONTHLY_PRICE_ID=${STRIPE_PRO_MONTHLY_PRICE_ID:-"price_placeholder"}
export _STRIPE_PRO_YEARLY_PRICE_ID=${STRIPE_PRO_YEARLY_PRICE_ID:-"price_placeholder"}
export _STRIPE_TEAM_MONTHLY_PRICE_ID=${STRIPE_TEAM_MONTHLY_PRICE_ID:-"price_placeholder"}
export _STRIPE_TEAM_YEARLY_PRICE_ID=${STRIPE_TEAM_YEARLY_PRICE_ID:-"price_placeholder"}
export _FIREBASE_CREDENTIALS_JSON=${FIREBASE_CREDENTIALS:-"{}"}

# Construct the substitutions string
SUBSTITUTIONS="_DB_PASSWORD=${_DB_PASSWORD},\
_OPENAI_API_KEY=${OPENAI_API_KEY},\
_ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},\
_TWITTER_API_KEY=${TWITTER_API_KEY},\
_TWITTER_API_SECRET=${TWITTER_API_SECRET},\
_TWITTER_ACCESS_TOKEN=${TWITTER_ACCESS_TOKEN},\
_TWITTER_ACCESS_SECRET=${TWITTER_ACCESS_SECRET},\
_TWITTER_BEARER_TOKEN=${TWITTER_BEARER_TOKEN},\
_SERPER_API_KEY=${SERPER_API_KEY},\
_STRIPE_SECRET_KEY=${_STRIPE_SECRET_KEY},\
_STRIPE_PUBLISHABLE_KEY=${_STRIPE_PUBLISHABLE_KEY},\
_STRIPE_WEBHOOK_SECRET=${_STRIPE_WEBHOOK_SECRET},\
_STRIPE_PRO_MONTHLY_PRICE_ID=${_STRIPE_PRO_MONTHLY_PRICE_ID},\
_STRIPE_PRO_YEARLY_PRICE_ID=${_STRIPE_PRO_YEARLY_PRICE_ID},\
_STRIPE_TEAM_MONTHLY_PRICE_ID=${_STRIPE_TEAM_MONTHLY_PRICE_ID},\
_STRIPE_TEAM_YEARLY_PRICE_ID=${_STRIPE_TEAM_YEARLY_PRICE_ID},\
_FIREBASE_CREDENTIALS_JSON=${_FIREBASE_CREDENTIALS_JSON},\
_JWT_SECRET_KEY=${JWT_SECRET_KEY}"

echo "Submitting build with substitutions..."

gcloud builds submit --config cloudbuild.yaml --substitutions="${SUBSTITUTIONS}" .
