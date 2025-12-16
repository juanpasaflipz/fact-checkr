
import os
import subprocess
import sys
import json
import re
import base64

# Configuration
PROJECT_ID = "fact-check-mx-934bc"
BACKEND_DIR = "backend"
ENV_FILE = os.path.join(BACKEND_DIR, ".env")
CLOUDBUILD_YAML = "cloudbuild.yaml"

REQUIRED_KEYS = {
    "ANTHROPIC_API_KEY",
    "DB_PASSWORD",
    "FIREBASE_CREDENTIALS_JSON", # We read this, but transform it
    "JWT_SECRET_KEY",
    "OPENAI_API_KEY",
    "SERPER_API_KEY",
    "STRIPE_PRO_MONTHLY_PRICE_ID",
    "STRIPE_PRO_YEARLY_PRICE_ID",
    "STRIPE_PUBLISHABLE_KEY",
    "STRIPE_SECRET_KEY",
    "STRIPE_TEAM_MONTHLY_PRICE_ID",
    "STRIPE_TEAM_YEARLY_PRICE_ID",
    "STRIPE_WEBHOOK_SECRET",
    "TASKS_OIDC_SERVICE_ACCOUNT_EMAIL",
    "TASKS_TARGET_BASE_URL",
    "TASK_SECRET",
    "TWITTER_ACCESS_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "TWITTER_BEARER_TOKEN",
}

def parse_env_file(filepath):
    """
    Manually parses a .env file to handle multi-line strings and other quirks better than simple split.
    Uses basic heuristics specifically for this use case.
    """
    env_vars = {}
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found")
        sys.exit(1)

    with open(filepath, 'r') as f:
        content = f.read()

    # Simple regex for parsing env vars, handling potential quoted values
    # formatting: KEY='VALUE' or KEY="VALUE" or KEY=VALUE
    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if '=' not in line:
            continue
            
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # Remove surrounding quotes
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
            
        env_vars[key] = value

    return env_vars

def main():
    print(f"Deploying to Project: {PROJECT_ID}")
    print(f"Reading secrets from {ENV_FILE}...")
    
    env_vars = parse_env_file(ENV_FILE)
    
    # Extract DB_PASSWORD from DATABASE_URL if needed
    if "DB_PASSWORD" not in env_vars and "DATABASE_URL" in env_vars:
        db_url = env_vars["DATABASE_URL"]
        try:
            # postgres://user:password@host...
            parts = db_url.split('://', 1)[1]
            auth_part = parts.split('@', 1)[0]
            password = auth_part.split(':', 1)[1]
            env_vars["DB_PASSWORD"] = password
            print("Using derived DB_PASSWORD")
        except Exception:
            print("Warning: Could not derive DB_PASSWORD from DATABASE_URL")

    substitutions = []
    
    for key, value in env_vars.items():
        if key not in REQUIRED_KEYS and key != "DB_PASSWORD":
            continue
            
        # Special handling for FIREBASE_CREDENTIALS_JSON
        if key == "FIREBASE_CREDENTIALS_JSON":
            # Minify JSON logic (safety check)
            if value.startswith('{') and value.endswith('}'):
                try:
                    obj = json.loads(value)
                    value = json.dumps(obj, separators=(',', ':'))
                except json.JSONDecodeError:
                    pass 
            
            # Base64 encode
            b64_val = base64.b64encode(value.encode('utf-8')).decode('utf-8')
            substitutions.append(f"_FIREBASE_CREDENTIALS_B64={b64_val}")
            continue

        # Standard handling
        if value.startswith('{') and value.endswith('}'):
            try:
                obj = json.loads(value)
                value = json.dumps(obj, separators=(',', ':'))
            except json.JSONDecodeError:
                pass 
                
        # Escape special characters for gcloud substitutions
        escaped_value = value.replace(',', '\\,')
        
        substitutions.append(f"_{key}={escaped_value}")

    substitutions_str = ",".join(substitutions)
    
    cmd = [
        "gcloud", "builds", "submit",
        "--config", CLOUDBUILD_YAML,
        "--project", PROJECT_ID,
        "--substitutions", substitutions_str
    ]
    
    print("Submitting build to Cloud Build...")
    print(f"Substitutions count: {len(substitutions)}")
    
    # We call standard subprocess.run 
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
