"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

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

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

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
    
    # Create user
    hashed_password = get_password_hash(register_data.password)
    user = User(
        email=register_data.email,
        username=register_data.username,
        hashed_password=hashed_password,
        full_name=register_data.full_name,
        is_active=True,
        is_verified=False,  # Email verification can be added later
        last_login=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create default FREE subscription
    create_default_subscription(db, user.id)
    
    # Create default user balance with demo credits
    create_default_user_balance(db, user.id)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
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
    access_token = create_access_token(data={"sub": user.id})
    
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
