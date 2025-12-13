from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
from datetime import datetime
import os
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.core.utils import get_user_by_id

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
# On Cloud Run, this uses the default service account automatically.
# On local/Railway, you must set GOOGLE_APPLICATION_CREDENTIALS env var to the path of your service account JSON.
try:
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    logger.info("✅ Firebase Admin SDK initialized")
except Exception as e:
    logger.warning(f"⚠️ Failed to initialize Firebase Admin SDK: {e}")

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """Verify Firebase ID token and return user from database"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if credentials is None:
        # logger.warning("❌ Auth failed: Missing authentication credentials")
        raise credentials_exception
    
    if not credentials.credentials or not credentials.credentials.strip():
        logger.warning("❌ Auth failed: Empty authentication credentials")
        raise credentials_exception
    
    token = credentials.credentials.strip()
    
    try:
        # 1. Verify ID Token with Firebase
        # This checks signature, expiry, and issuer
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        
        if not email:
            logger.warning(f"❌ Auth failed: Firebase token missing email for UID {uid}")
            raise credentials_exception
            
        # 2. Lookup User in our SQL Database
        # TEMPORARY MIGRATION LOGIC: Lookup by Email
        # In the future, we should add a 'firebase_uid' column to the User table
        user = db.query(User).filter(User.email == email).first()
        
        if user is None:
            logger.warning(f"❌ Auth failed: User not found in SQL DB for email: {email}")
            # Optional: Auto-create user here if desired
            raise credentials_exception
            
        if not user.is_active:
            logger.warning(f"❌ Auth failed: User {user.id} is inactive")
            raise credentials_exception
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
        
    except auth.ExpiredIdTokenError:
        logger.warning("❌ Auth failed: Token expired")
        raise credentials_exception
    except auth.InvalidIdTokenError:
        logger.warning("❌ Auth failed: Invalid token")
        raise credentials_exception
    except Exception as e:
        logger.error(f"❌ Unexpected auth error: {str(e)}")
        raise credentials_exception

# Optional dependency for protected routes
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """Optional authentication - returns user if token present, None otherwise"""
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials.strip()
        decoded_token = auth.verify_id_token(token)
        email = decoded_token.get('email')
        
        if not email:
            return None
            
        user = db.query(User).filter(User.email == email).first()
        if user is None or not user.is_active:
            return None
        
        return user
    except Exception:
        return None

async def get_admin_user(
    user: User = Depends(get_current_user)
) -> User:
    """Require admin privileges - raises 403 if user is not admin"""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

# Legacy helpers to prevent ImportErrors in other modules if they still use them
# (We might want to deprecate these)
def create_access_token(data: dict, expires_delta: Optional[datetime] = None):
    # This is now handled by Firebase Client SDK on frontend
    # But we keep it to avoid breaking imports during transition
    logger.warning("⚠️ create_access_token() called manually - this should be handled by Firebase now")
    return "firebase-handled-token"
