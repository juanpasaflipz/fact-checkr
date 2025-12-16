#!/bin/bash
set -e

PROJECT_ID="fact-check-mx-934bc"
SERVICE_NAME="factcheckr-backend"
REGION="us-central1"

echo "Verifying deployment for $SERVICE_NAME in $PROJECT_ID..."

# Get Service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --project $PROJECT_ID --region $REGION --format 'value(status.url)')

if [ -z "$SERVICE_URL" ]; then
    echo "❌ Service URL not found. Is the service deployed?"
    exit 1
fi

echo "✅ Service URL: $SERVICE_URL"

# Check Health
echo "Checking health endpoint..."
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health")

echo "Response: $HEALTH_RESPONSE"

if [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed or returned unexpected response."
    exit 1
fi

# Check /docs access (optional)
echo "Checking documentation endpoint..."
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/docs")

if [ "$DOCS_STATUS" -eq 200 ]; then
    echo "✅ Docs accessible at $SERVICE_URL/docs"
else
    echo "⚠️ Docs endpoint returned $DOCS_STATUS"
fi

echo "Deployment verification complete."
