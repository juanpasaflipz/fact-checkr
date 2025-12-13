"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
import os
import secrets
import httpx
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

from app.database.connection import get_db
from app.database.models import User
from app.core.auth import create_access_token, get_current_user
from app.core.utils import (
    get_user_by_email,
    get_user_by_username,
    verify_password,
    get_password_hash,
    create_default_subscription,
    create_default_user_balance,
    get_redis_url,
)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

# OAuth state storage - use Redis in production, fallback to in-memory for local dev
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    logger.warning("⚠️  redis package not installed, OAuth state will use in-memory storage")

# Lazy Redis initialization - don't block startup with connection attempts
_redis_client = None
_redis_initialized = False
_use_redis = None


def _get_redis_client():
    """Lazily initialize Redis client on first use, not at import time"""
    global _redis_client, _redis_initialized, _use_redis
    
    if _redis_initialized:
        return _redis_client, _use_redis
    
    _redis_initialized = True
    _use_redis = False
    
    if not REDIS_AVAILABLE:
        logger.warning("⚠️  Redis package not available, using in-memory OAuth state storage")
        return None, False
    
    try:
        redis_url = get_redis_url()
        _redis_client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
        _redis_client.ping()  # Test connection
        _use_redis = True
        logger.info("✅ Using Redis for OAuth state storage")
    except Exception as e:
        logger.warning(f"⚠️  Redis not available for OAuth state storage: {e}")
        logger.warning("⚠️  Falling back to in-memory storage (not recommended for production)")
        _redis_client = None
        _use_redis = False
    
    return _redis_client, _use_redis


# Backwards compatibility - these are now lazily evaluated
def _get_use_redis():
    _, use = _get_redis_client()
    return use

def _get_client():
    client, _ = _get_redis_client()
    return client

# Fallback in-memory storage (only used if Redis unavailable)
oauth_states = {}

# Google OAuth configuration
from app.config.settings import FRONTEND_URL

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

# Validate OAuth configuration on startup
def validate_oauth_config():
    """Validate Google OAuth configuration and log warnings"""
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        logger.info("✅ Google OAuth configured")
        logger.info(f"   Client ID: {GOOGLE_CLIENT_ID[:20]}...")
        logger.info(f"   Redirect URI: {GOOGLE_REDIRECT_URI}")
        logger.info(f"   Frontend URL: {FRONTEND_URL}")
        
        # Validate redirect URI format
        if not GOOGLE_REDIRECT_URI.startswith(("http://", "https://")):
            logger.warning(f"⚠️  GOOGLE_REDIRECT_URI should start with http:// or https://")
        if not GOOGLE_REDIRECT_URI.endswith("/api/auth/google/callback"):
            logger.warning(f"⚠️  GOOGLE_REDIRECT_URI should end with /api/auth/google/callback")
        if " " in GOOGLE_REDIRECT_URI:
            logger.warning(f"⚠️  GOOGLE_REDIRECT_URI contains spaces - this will cause redirect_uri_mismatch errors")
        
        # Validate FRONTEND_URL format
        if not FRONTEND_URL.startswith(("http://", "https://")):
            logger.error(f"❌ FRONTEND_URL must start with http:// or https://")
        if "wwww" in FRONTEND_URL or "wwww" in FRONTEND_URL.lower():
            logger.error(f"❌ FRONTEND_URL appears to have a typo (wwww instead of www): {FRONTEND_URL}")
        if ".com" in FRONTEND_URL and "factcheck.mx" not in FRONTEND_URL:
            logger.warning(f"⚠️  FRONTEND_URL appears incorrect: {FRONTEND_URL} (expected factcheck.mx domain)")
    else:
        logger.warning("⚠️  Google OAuth not configured - set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")

# Run validation on module import
validate_oauth_config()

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    referral_code: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    preferred_categories: Optional[List[str]] = None
    onboarding_completed: Optional[bool] = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

@router.post("/register", response_model=TokenResponse)
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    import secrets
    from app.database.models import ReferralBonus, UserBalance
    
    # Check if email already exists
    existing_user = get_user_by_email(db, register_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = get_user_by_username(db, register_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Validate password
    if len(register_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Handle referral code if provided
    referred_by_user_id = None
    if register_data.referral_code:
        referrer = db.query(User).filter(
            User.referral_code == register_data.referral_code
        ).first()
        if referrer:
            referred_by_user_id = referrer.id
    
    # Generate unique referral code for new user
    referral_code = secrets.token_urlsafe(8)
    while db.query(User).filter(User.referral_code == referral_code).first():
        referral_code = secrets.token_urlsafe(8)
    
    # Create user
    hashed_password = get_password_hash(register_data.password)
    user = User(
        email=register_data.email,
        username=register_data.username,
        hashed_password=hashed_password,
        full_name=register_data.full_name,
        is_active=True,
        is_verified=False,  # Email verification can be added later
        last_login=datetime.utcnow(),
        referred_by_user_id=referred_by_user_id,
        referral_code=referral_code
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create default FREE subscription
    create_default_subscription(db, user.id)
    
    # Create default user balance with demo credits
    balance = create_default_user_balance(db, user.id)
    
    # Process referral bonus if applicable
    if referred_by_user_id:
        # Create referral bonus record
        referral_bonus = ReferralBonus(
            referrer_id=referred_by_user_id,
            referred_id=user.id,
            bonus_credits=100.0,
            paid=False
        )
        db.add(referral_bonus)
        
        # Add bonus credits to referrer
        referrer_balance = db.query(UserBalance).filter(
            UserBalance.user_id == referred_by_user_id
        ).first()
        if referrer_balance:
            referrer_balance.available_credits += 100.0
            referral_bonus.paid = True
        
        db.commit()
    
    # Create access token
    # Subject (sub) must be a string for JWT compliance
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            preferred_categories=user.preferred_categories,
            onboarding_completed=user.onboarding_completed or False
        )
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login user"""
    # Find user by email
    user = get_user_by_email(db, login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    # Subject (sub) must be a string for JWT compliance
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            preferred_categories=user.preferred_categories,
            onboarding_completed=user.onboarding_completed or False
        )
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user),
):
    """Get current user information"""
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        preferred_categories=user.preferred_categories,
        onboarding_completed=user.onboarding_completed or False
    )

class UpdatePreferencesRequest(BaseModel):
    preferred_categories: List[str]
    onboarding_completed: bool = True

@router.put("/me/preferences", response_model=UserResponse)
async def update_preferences(
    preferences: UpdatePreferencesRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences for market categories"""
    # Validate categories
    valid_categories = [
        'politics', 'economy', 'security', 'rights', 'environment', 
        'mexico-us-relations', 'institutions',
        'sports', 'financial-markets', 'weather', 'social-incidents'
    ]
    for cat in preferences.preferred_categories:
        if cat not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {cat}. Must be one of: {', '.join(valid_categories)}"
            )
    
    # Update user preferences
    user.preferred_categories = preferences.preferred_categories
    user.onboarding_completed = preferences.onboarding_completed
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        preferred_categories=user.preferred_categories,
        onboarding_completed=user.onboarding_completed
    )

@router.get("/google/login")
async def google_login():
    """Initiate Google OAuth login"""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    state_timestamp = datetime.utcnow()
    
    # Store state in Redis (with 10 minute expiration) or in-memory fallback
    redis_client, use_redis = _get_redis_client()
    if use_redis and redis_client:
        try:
            redis_client.setex(f"oauth_state:{state}", 600, state_timestamp.isoformat())  # 10 minutes
            logger.info(f"OAuth state stored in Redis: {state[:10]}...")
        except Exception as e:
            logger.error(f"Failed to store OAuth state in Redis: {e}, falling back to in-memory")
            oauth_states[state] = state_timestamp
    else:
        oauth_states[state] = state_timestamp
        logger.info(f"OAuth state stored in memory: {state[:10]}...")
    
    # Google OAuth URL
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent"
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url=auth_url)

@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    # Enhanced logging for debugging
    logger.info("=" * 60)
    logger.info("Google OAuth callback hit")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Query params: code={'present' if code else 'missing'}, state={'present' if state else 'missing'}, error={error}")
    logger.info(f"Configured redirect_uri: {GOOGLE_REDIRECT_URI}")
    logger.info(f"Frontend URL: {FRONTEND_URL}")
    logger.info(f"Client ID configured: {bool(GOOGLE_CLIENT_ID)}")
    logger.info(f"Client Secret configured: {bool(GOOGLE_CLIENT_SECRET)}")
    logger.info("=" * 60)
    
    if error:
        logger.warning(f"Google OAuth error from callback: {error}")
        logger.warning(f"Full query params: {dict(request.query_params)}")
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=oauth_cancelled")
    
    if not code or not state:
        logger.error(f"Missing required parameters: code={bool(code)}, state={bool(state)}")
        logger.error(f"Full query params: {dict(request.query_params)}")
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=invalid_callback")
    
    # Verify state (CSRF protection) - check Redis first, then in-memory fallback
    state_created = None
    state_found = False
    
    redis_client, use_redis = _get_redis_client()
    if use_redis and redis_client:
        try:
            state_timestamp_str = redis_client.get(f"oauth_state:{state}")
            if state_timestamp_str:
                state_created = datetime.fromisoformat(state_timestamp_str)
                state_found = True
                # Delete state immediately (one-time use)
                redis_client.delete(f"oauth_state:{state}")
                logger.info(f"OAuth state found in Redis: {state[:10]}...")
        except Exception as e:
            logger.warning(f"Error reading OAuth state from Redis: {e}, checking in-memory fallback")
    
    # Fallback to in-memory storage
    if not state_found:
        if state in oauth_states:
            state_created = oauth_states[state]
            state_found = True
            # Remove used state (one-time use)
            del oauth_states[state]
            logger.info(f"OAuth state found in memory: {state[:10]}...")
    
    if not state_found:
        logger.error(f"Invalid state token: {state[:10]}... (not found in Redis or memory)")
        logger.error(f"Available states in memory: {len(oauth_states)}")
        if use_redis and redis_client:
            try:
                redis_keys = redis_client.keys("oauth_state:*")
                logger.error(f"Available states in Redis: {len(redis_keys)}")
            except Exception:
                pass
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=invalid_state")
    
    # Check if state is expired (older than 10 minutes)
    if state_created and (datetime.utcnow() - state_created).total_seconds() > 600:
        logger.error(f"Expired state token: {state[:10]}... (created at {state_created})")
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=expired_state")
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("Google OAuth not configured: missing CLIENT_ID or CLIENT_SECRET")
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=oauth_not_configured")
    
    try:
        # Exchange code for tokens
        logger.info("Exchanging authorization code for tokens...")
        logger.info(f"Using redirect_uri: {GOOGLE_REDIRECT_URI}")
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            
            # Enhanced error logging for token exchange
            if not token_response.is_success:
                error_text = token_response.text
                error_status = token_response.status_code
                logger.error(f"Token exchange failed: HTTP {error_status}")
                logger.error(f"Response body: {error_text}")
                try:
                    error_json = token_response.json()
                    logger.error(f"Error details: {error_json}")
                    # Check for common Google OAuth errors
                    if "error" in error_json:
                        error_type = error_json.get("error")
                        error_description = error_json.get("error_description", "")
                        logger.error(f"Google OAuth error: {error_type} - {error_description}")
                        if error_type == "redirect_uri_mismatch":
                            logger.error(f"Redirect URI mismatch! Configured: {GOOGLE_REDIRECT_URI}")
                            logger.error("Make sure this exact URI is in Google Cloud Console")
                except Exception:
                    pass
                return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=token_exchange_failed")
            
            token_response.raise_for_status()
            tokens = token_response.json()
        
        access_token = tokens.get("access_token")
        if not access_token:
            logger.error("Failed to get access_token from Google response")
            logger.error(f"Token response keys: {list(tokens.keys())}")
            return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=token_exchange_failed")
        
        logger.info("Successfully exchanged code for access token")
        
        # Get user info from Google
        logger.info("Fetching user info from Google...")
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(userinfo_url, headers=headers)
            userinfo_response.raise_for_status()
            google_user = userinfo_response.json()
        
        email = google_user.get("email")
        google_id = google_user.get("id")
        name = google_user.get("name", "")
        given_name = google_user.get("given_name", "")
        family_name = google_user.get("family_name", "")
        picture = google_user.get("picture")
        
        logger.info(f"Google user info retrieved: email={email}, id={google_id}")
        
        if not email or not google_id:
            logger.error(f"Invalid user info from Google: email={email}, id={google_id}")
            return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=invalid_user_info")
        
        # Check if user exists by email
        user = get_user_by_email(db, email)
        
        if user:
            logger.info(f"Existing user found: {user.email} (id: {user.id})")
            # User exists - update last login
            try:
                user.last_login = datetime.utcnow()
                db.commit()
            except Exception as e:
                logger.error(f"Error updating last login: {str(e)}")
                db.rollback()
                raise
        else:
            logger.info(f"Creating new user for email: {email}")
            try:
                # Create new user from Google OAuth
                # Generate username from email or name
                base_username = email.split("@")[0]
                username = base_username
                counter = 1
                while get_user_by_username(db, username):
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Generate referral code
                referral_code = secrets.token_urlsafe(8)
                while db.query(User).filter(User.referral_code == referral_code).first():
                    referral_code = secrets.token_urlsafe(8)
                
                # Create user with placeholder password (OAuth users won't use it)
                # Bcrypt has a 72-byte limit on input password, so we use a shorter token
                # 16 bytes = ~22 chars when base64url encoded, well under 72-byte limit
                placeholder_password = secrets.token_urlsafe(16)
                hashed_password = get_password_hash(placeholder_password)
                
                user = User(
                    email=email,
                    username=username,
                    hashed_password=hashed_password,
                    full_name=name or f"{given_name} {family_name}".strip(),
                    is_active=True,
                    is_verified=True,  # Google emails are verified
                    last_login=datetime.utcnow(),
                    referral_code=referral_code
                )
                
                db.add(user)
                db.commit()
                db.refresh(user)
                
                logger.info(f"New user created: {user.email} (id: {user.id})")
                
                # Create default subscription and balance
                try:
                    create_default_subscription(db, user.id)
                    logger.info(f"Default subscription created for user {user.id}")
                except Exception as e:
                    logger.error(f"Error creating default subscription: {str(e)}")
                    db.rollback()
                    # Don't fail the whole flow if subscription creation fails

                try:
                    create_default_user_balance(db, user.id)
                    logger.info(f"Default user balance created for user {user.id}")
                except Exception as e:
                    logger.error(f"Error creating default user balance: {str(e)}")
                    db.rollback()
                    # Don't fail the whole flow if balance creation fails
                    
            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                db.rollback()
                raise
        
        # Create JWT token
        # Subject (sub) must be a string for JWT compliance
        access_token_jwt = create_access_token(data={"sub": str(user.id)})
        logger.info(f"JWT token created for user {user.id}")
        
        # Redirect to frontend with token in URL (frontend should extract and store securely)
        # Using URL fragment would be more secure but requires JavaScript on frontend
        redirect_url = f"{FRONTEND_URL}/signin?token={access_token_jwt}&success=true"
        logger.info(f"Redirecting to frontend: {FRONTEND_URL}/signin")
        
        response = RedirectResponse(url=redirect_url)
        
        # Also set token in httpOnly cookie as backup (more secure)
        # Frontend can check cookie first, then fall back to URL param
        response.set_cookie(
            key="access_token",
            value=access_token_jwt,
            httponly=True,
            secure=os.getenv("ENVIRONMENT") == "production",  # Only secure in production (HTTPS)
            samesite="lax",
            max_age=86400 * 7  # 7 days
        )
        
        return response
        
    except httpx.HTTPStatusError as e:
        logger.error("=" * 60)
        logger.error("HTTP Status Error during OAuth")
        logger.error(f"Status code: {e.response.status_code}")
        logger.error(f"Response text: {e.response.text}")
        logger.error(f"Request URL: {e.request.url if hasattr(e, 'request') else 'N/A'}")
        try:
            error_json = e.response.json()
            logger.error(f"Error JSON: {error_json}")
            if "error" in error_json:
                logger.error(f"OAuth error type: {error_json.get('error')}")
                logger.error(f"Error description: {error_json.get('error_description', 'N/A')}")
        except Exception:
            pass
        logger.error("=" * 60)
        db.rollback()
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=oauth_http_error")
    except httpx.HTTPError as e:
        logger.error("=" * 60)
        logger.error(f"HTTP Error during OAuth: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error("=" * 60)
        db.rollback()
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=oauth_error")
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Unexpected error during OAuth: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        logger.error("=" * 60)
        db.rollback()
        # Include error details in redirect for debugging (remove in production)
        error_detail = str(e).replace(' ', '_')[:50]  # Sanitize for URL
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=server_error&detail={error_detail}")
