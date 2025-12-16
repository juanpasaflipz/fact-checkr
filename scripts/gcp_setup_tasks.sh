#!/bin/bash
# scripts/gcp_setup_tasks.sh

# Exit on error
set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"fact-check-mx-934bc"}
LOCATION=${LOCATION:-"us-central1"}
QUEUE_NAME=${QUEUE_NAME:-"factcheckr-tasks"}
SERVICE_ACCOUNT_NAME="factcheckr-sa"

echo "Setting up Google Cloud Tasks for project: $PROJECT_ID"

# 1. Enable APIs
echo "Enabling Cloud Tasks API..."
gcloud services enable cloudtasks.googleapis.com cloudrun.googleapis.com --project $PROJECT_ID

# 2. Create Service Account for OIDC capability
if ! gcloud iam service-accounts describe ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com --project $PROJECT_ID &>/dev/null; then
  echo "Creating Service Account: $SERVICE_ACCOUNT_NAME..."
  gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name "FactCheckr Cloud Run Invoker" \
    --project $PROJECT_ID
else
  echo "Service Account $SERVICE_ACCOUNT_NAME already exists."
fi

# 3. Grant Cloud Run Invoker role to Service Account
echo "Granting Cloud Run Invoker role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member "serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/run.invoker"

# 4. Create Cloud Tasks Queue
if ! gcloud tasks queues describe $QUEUE_NAME --location $LOCATION --project $PROJECT_ID &>/dev/null; then
  echo "Creating Cloud Tasks Queue: $QUEUE_NAME..."
  gcloud tasks queues create $QUEUE_NAME \
    --location $LOCATION \
    --project $PROJECT_ID
else
  echo "Queue $QUEUE_NAME already exists."
fi

echo "✅ Setup complete!"
echo "Service Account Email: ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
echo "Queue: projects/$PROJECT_ID/locations/$LOCATION/queues/$QUEUE_NAME"
