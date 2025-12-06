from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.utils import get_user_by_id

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
if SECRET_KEY == "your-secret-key-change-in-production":
    logger.warning("⚠️ Using default insecure JWT_SECRET_KEY!")
else:
    logger.info("✅ Loaded JWT_SECRET_KEY from environment")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days for better UX

security = HTTPBearer(auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """Verify JWT token and return user from database"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if credentials is None:
        logger.warning("❌ Auth failed: Missing authentication credentials")
        raise credentials_exception
    
    if not credentials.credentials or not credentials.credentials.strip():
        logger.warning("❌ Auth failed: Empty authentication credentials")
        raise credentials_exception
    
    try:
        token = credentials.credentials.strip()
        # Log token prefix for debugging
        logger.info(f"🔑 Verifying token: {token[:10]}...")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        
        if user_id_str is None:
            logger.warning("❌ Auth failed: Token missing 'sub' claim")
            raise credentials_exception
        
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            logger.warning(f"❌ Auth failed: Token 'sub' claim is not a valid integer: {user_id_str}")
            raise credentials_exception
        
        # Get user from database
        user = get_user_by_id(db, user_id)
        if user is None:
            logger.warning(f"❌ Auth failed: User not found for id: {user_id}")
            raise credentials_exception
            
        if not user.is_active:
            logger.warning(f"❌ Auth failed: User {user_id} is inactive")
            raise credentials_exception
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    except JWTError as e:
        logger.warning(f"❌ Auth failed: JWT validation error: {str(e)}")
        # Check if it might be a key mismatch
        if "Signature verification failed" in str(e):
            logger.error("⚠️  Signature verification failed. This often means JWT_SECRET_KEY mismatch between generator and verifier.")
        raise credentials_exception
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected auth error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Do NOT raise credentials_exception here. Let it bubble up as 500.
        raise

# Optional dependency for protected routes
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """Optional authentication - returns user if token present, None otherwise"""
    if credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        
        user = get_user_by_id(db, user_id)
        if user is None or not user.is_active:
            return None
        
        return user
    except JWTError:
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

