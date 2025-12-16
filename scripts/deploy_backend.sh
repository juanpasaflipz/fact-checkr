#!/bin/bash
set -e

# Configuration
PROJECT_ID="fact-check-mx-934bc"
BACKEND_DIR="backend"
ENV_FILE="$BACKEND_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found!"
    exit 1
fi

echo "Deploying to Project: $PROJECT_ID"
echo "Reading secrets from $ENV_FILE..."

# List of required substitutions (from cloudbuild.yaml)
REQUIRED_KEYS=(
    "ANTHROPIC_API_KEY"
    "DB_PASSWORD"
    "FIREBASE_CREDENTIALS_JSON"
    "JWT_SECRET_KEY"
    "OPENAI_API_KEY"
    "SERPER_API_KEY"
    "STRIPE_PRO_MONTHLY_PRICE_ID"
    "STRIPE_PRO_YEARLY_PRICE_ID"
    "STRIPE_PUBLISHABLE_KEY"
    "STRIPE_SECRET_KEY"
    "STRIPE_TEAM_MONTHLY_PRICE_ID"
    "STRIPE_TEAM_YEARLY_PRICE_ID"
    "STRIPE_WEBHOOK_SECRET"
    "TASKS_OIDC_SERVICE_ACCOUNT_EMAIL"
    "TASKS_TARGET_BASE_URL"
    "TASK_SECRET"
    "TWITTER_ACCESS_SECRET"
    "TWITTER_ACCESS_TOKEN"
    "TWITTER_API_KEY"
    "TWITTER_API_SECRET"
    "TWITTER_BEARER_TOKEN"
)

# Extract DB_PASSWORD from DATABASE_URL if not explicit
# DATABASE_URL=postgresql://postgres:PASSWORD@host...
DB_PASSWORD=""
if grep -q "^DATABASE_URL=" "$ENV_FILE"; then
    DB_URL=$(grep "^DATABASE_URL=" "$ENV_FILE" | cut -d'=' -f2-)
    # Extract password between second colon and @
    # postgres://user:password@host
    # Remove protocol
    temp="${DB_URL#*://}"
    # Remove user
    temp="${temp#*:}"
    # Remove host part
    DB_PASSWORD="${temp%%@*}"
    # echo "Found DB_PASSWORD from DATABASE_URL"
fi

SUBSTITUTIONS=""
FOUND_KEYS=()

# Process file line by line
while IFS= read -r line; do
    # Skip comments
    if [[ "$line" =~ ^#.* ]] || [[ -z "$line" ]]; then
        continue
    fi
    
    # Strict regex for KEY=VALUE
    if [[ "$line" =~ ^([A-Z0-9_]+)=(.*)$ ]]; then
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        
        # Trim value (quotes)
        value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
        
        # Check if this key is required
        # Start matching
        REQUIRED=0
        for req in "${REQUIRED_KEYS[@]}"; do
            if [[ "$req" == "$key" ]]; then
                REQUIRED=1
                break
            fi
        done
        
        if [[ $REQUIRED -eq 1 ]]; then
            # Escape commas
            value="${value//,/\\,}"
            
            sub_key="_${key}"
            if [ -z "$SUBSTITUTIONS" ]; then
                SUBSTITUTIONS="${sub_key}=${value}"
            else
                SUBSTITUTIONS="${SUBSTITUTIONS},${sub_key}=${value}"
            fi
            FOUND_KEYS+=("$key")
        fi
    fi
done < "$ENV_FILE"

# Handle derived keys (DB_PASSWORD)
# If DB_PASSWORD was not in .env but derived
if [[ ! " ${FOUND_KEYS[*]} " =~ " DB_PASSWORD " ]] && [[ -n "$DB_PASSWORD" ]]; then
    echo "Using derived DB_PASSWORD"
    sub_key="_DB_PASSWORD"
    # Verify DB_PASSWORD is not empty and escape
    DB_PASSWORD="${DB_PASSWORD//,/\\,}"
    if [ -z "$SUBSTITUTIONS" ]; then
        SUBSTITUTIONS="${sub_key}=${DB_PASSWORD}"
    else
        SUBSTITUTIONS="${SUBSTITUTIONS},${sub_key}=${DB_PASSWORD}"
    fi
fi

# Check for missing keys (Optional but helpful)
for req in "${REQUIRED_KEYS[@]}"; do
    if [[ ! " ${FOUND_KEYS[*]} " =~ " $req " ]] && [[ "$req" != "DB_PASSWORD" ]]; then
        echo "Warning: Required key $req not found in .env"
    fi
done

echo "Submitting build to Cloud Build..."
gcloud builds submit --config cloudbuild.yaml --project "$PROJECT_ID" --substitutions "$SUBSTITUTIONS"
