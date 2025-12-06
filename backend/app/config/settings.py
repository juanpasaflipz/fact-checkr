import os
import logging

logger = logging.getLogger(__name__)

def get_frontend_url():
    """Get and sanitize FRONTEND_URL from environment"""
    url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Fix common typos
    if "wwww" in url:
        logger.warning(f"⚠️  Fixing typo in FRONTEND_URL: {url} -> replacing 'wwww' with 'www'")
        url = url.replace("wwww", "www")
    
    if url.endswith("/"):
        url = url.rstrip("/")
        
    return url

FRONTEND_URL = get_frontend_url()

