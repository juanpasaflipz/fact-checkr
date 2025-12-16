from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
from datetime import datetime
import os
import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User, UserRole
from app.core.utils import get_user_by_id
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
# On Cloud Run, this uses the default service account automatically.
# On local/Railway, you must set GOOGLE_APPLICATION_CREDENTIALS env var to the path of your service account JSON.
try:
    if not firebase_admin._apps:
        cred = None
        # Check for Base64 encoded credentials (deployment friendly)
        firebase_creds_b64 = settings.FIREBASE_CREDENTIALS_B64
        if firebase_creds_b64:
            import base64
            import json
            try:
                json_str = base64.b64decode(firebase_creds_b64).decode('utf-8')
                cred_dict = json.loads(json_str)
                cred = credentials.Certificate(cred_dict)
                logger.info("🔑 Loaded Firebase credentials from Base64 env var")
            except Exception as e:
                logger.error(f"❌ Failed to decode FIREBASE_CREDENTIALS_B64: {e}")
        
        firebase_admin.initialize_app(cred)
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

class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        # Support legacy is_admin flag for graceful migration
        if user.is_admin and (UserRole.ADMIN in self.allowed_roles or UserRole.SUPER_ADMIN in self.allowed_roles):
             return user
             
        if user.role not in self.allowed_roles:
            logger.warning(f"⛔ Access denied for user {user.email} (Role: {user.role}). Required: {self.allowed_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Operation not permitted"
            )
        return user

def allow_roles(roles: List[UserRole]):
    return RoleChecker(roles)

async def get_admin_user(
    user: User = Depends(get_current_user)
) -> User:
    """Require admin privileges - checking both legacy boolean and new role enum"""
    # Check legacy flag OR new role enum
    is_authorized = (
        user.is_admin or 
        user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    )
    
    if not is_authorized:
        logger.warning(f"⛔ Admin access denied for user {user.email}")
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
