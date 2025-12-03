"""Stripe configuration validation"""
import os
import logging
import stripe
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Required Stripe environment variables
REQUIRED_STRIPE_VARS = [
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_PRO_MONTHLY_PRICE_ID",
    "STRIPE_PRO_YEARLY_PRICE_ID",
    "STRIPE_TEAM_MONTHLY_PRICE_ID",
    "STRIPE_TEAM_YEARLY_PRICE_ID",
]

def validate_stripe_key_format(key: str) -> bool:
    """Validate Stripe API key format"""
    if not key:
        return False
    
    # Stripe secret keys start with sk_test_ or sk_live_
    # Stripe publishable keys start with pk_test_ or pk_live_
    if key.startswith(("sk_test_", "sk_live_", "pk_test_", "pk_live_")):
        return len(key) > 20  # Basic length check
    return False

def validate_webhook_secret_format(secret: str) -> bool:
    """Validate Stripe webhook secret format"""
    if not secret:
        return False
    
    # Webhook secrets start with whsec_
    if secret.startswith("whsec_"):
        return len(secret) > 10
    return False

def validate_price_id_format(price_id: str) -> bool:
    """Validate Stripe price ID format"""
    if not price_id:
        return False
    
    # Price IDs start with price_
    if price_id.startswith("price_"):
        return len(price_id) > 10
    return False

def validate_stripe_config() -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validate all Stripe configuration variables.
    
    Returns:
        Tuple of (is_valid, errors_dict) where errors_dict contains
        missing and invalid variables organized by type.
    """
    errors = {
        "missing": [],
        "invalid_format": [],
        "api_error": []
    }
    
    # Check for missing variables
    for var_name in REQUIRED_STRIPE_VARS:
        value = os.getenv(var_name, "")
        if not value:
            errors["missing"].append(var_name)
    
    # Validate formats
    stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "")
    if stripe_secret_key and not validate_stripe_key_format(stripe_secret_key):
        errors["invalid_format"].append("STRIPE_SECRET_KEY (must start with sk_test_ or sk_live_)")
    
    stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if stripe_webhook_secret and not validate_webhook_secret_format(stripe_webhook_secret):
        errors["invalid_format"].append("STRIPE_WEBHOOK_SECRET (must start with whsec_)")
    
    # Validate price IDs
    price_id_vars = [
        "STRIPE_PRO_MONTHLY_PRICE_ID",
        "STRIPE_PRO_YEARLY_PRICE_ID",
        "STRIPE_TEAM_MONTHLY_PRICE_ID",
        "STRIPE_TEAM_YEARLY_PRICE_ID",
    ]
    
    for var_name in price_id_vars:
        value = os.getenv(var_name, "")
        if value and not validate_price_id_format(value):
            errors["invalid_format"].append(f"{var_name} (must start with price_)")
    
    # Test Stripe API connection if secret key is present
    if stripe_secret_key and validate_stripe_key_format(stripe_secret_key):
        try:
            stripe.api_key = stripe_secret_key
            # Make a lightweight API call to verify the key works
            stripe.Account.retrieve()
            logger.info("✅ Stripe API key validated successfully")
        except stripe.error.AuthenticationError:
            errors["api_error"].append("STRIPE_SECRET_KEY (authentication failed - invalid key)")
        except stripe.error.APIConnectionError:
            errors["api_error"].append("STRIPE_SECRET_KEY (connection error - check network)")
        except Exception as e:
            errors["api_error"].append(f"STRIPE_SECRET_KEY (error: {str(e)})")
    
    is_valid = len(errors["missing"]) == 0 and len(errors["invalid_format"]) == 0 and len(errors["api_error"]) == 0
    
    return is_valid, errors

def log_stripe_config_status():
    """Log Stripe configuration status at startup"""
    logger.info("=" * 50)
    logger.info("Validating Stripe configuration...")
    logger.info("=" * 50)
    
    is_valid, errors = validate_stripe_config()
    
    if is_valid:
        logger.info("✅ Stripe configuration is valid")
        logger.info(f"  - Secret Key: {'*' * 20}...{os.getenv('STRIPE_SECRET_KEY', '')[-4:]}")
        logger.info(f"  - Webhook Secret: {'*' * 20}...{os.getenv('STRIPE_WEBHOOK_SECRET', '')[-4:]}")
        logger.info("  - All price IDs configured")
    else:
        logger.warning("⚠️  Stripe configuration has issues:")
        
        if errors["missing"]:
            logger.warning(f"  Missing variables: {', '.join(errors['missing'])}")
        
        if errors["invalid_format"]:
            logger.warning(f"  Invalid format: {', '.join(errors['invalid_format'])}")
        
        if errors["api_error"]:
            logger.warning(f"  API errors: {', '.join(errors['api_error'])}")
        
        logger.warning("  Stripe features may not work correctly until these are fixed.")
        logger.warning("  See docs/setup/STRIPE_ENV_VERIFICATION.md for setup instructions.")
    
    logger.info("=" * 50)
    
    return is_valid

