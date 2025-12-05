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
from app.auth import create_access_token, get_current_user
from app.utils import (
    get_user_by_email,
    get_user_by_username,
    verify_password,
    get_password_hash,
    create_default_subscription,
    create_default_user_balance,
)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

# OAuth state storage (in production, use Redis or database)
oauth_states = {}

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

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
    from app.database.models import ReferralBonus
    
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
    valid_categories = ['politics', 'economy', 'security', 'rights', 'environment', 'mexico-us-relations', 'institutions']
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
    oauth_states[state] = datetime.utcnow()
    
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
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    logger.info(f"Google OAuth callback received: code={'present' if code else 'missing'}, state={'present' if state else 'missing'}, error={error}")
    
    if error:
        logger.warning(f"Google OAuth error: {error}")
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=oauth_cancelled")
    
    if not code or not state:
        logger.error(f"Missing code or state: code={bool(code)}, state={bool(state)}")
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=invalid_callback")
    
    # Verify state (CSRF protection)
    if state not in oauth_states:
        logger.error(f"Invalid state token: {state[:10]}... (not in oauth_states)")
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=invalid_state")
    
    # Check if state is expired (older than 10 minutes)
    state_created = oauth_states.get(state)
    if state_created and (datetime.utcnow() - state_created).total_seconds() > 600:
        logger.error(f"Expired state token: {state[:10]}...")
        del oauth_states[state]
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=expired_state")
    
    # Remove used state (one-time use)
    del oauth_states[state]
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("Google OAuth not configured: missing CLIENT_ID or CLIENT_SECRET")
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=oauth_not_configured")
    
    try:
        # Exchange code for tokens
        logger.info("Exchanging authorization code for tokens...")
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
            token_response.raise_for_status()
            tokens = token_response.json()
        
        access_token = tokens.get("access_token")
        if not access_token:
            logger.error("Failed to get access_token from Google")
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
        logger.error(f"HTTP error during OAuth: {e.response.status_code} - {e.response.text}")
        db.rollback()
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=oauth_http_error")
    except httpx.HTTPError as e:
        logger.error(f"HTTP error during OAuth: {str(e)}")
        db.rollback()
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=oauth_error")
    except Exception as e:
        logger.error(f"Unexpected error during OAuth: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        db.rollback()
        # Include error details in redirect for debugging (remove in production)
        error_detail = str(e).replace(' ', '_')[:50]  # Sanitize for URL
        return RedirectResponse(url=f"{FRONTEND_URL}/signin?error=server_error&detail={error_detail}")
