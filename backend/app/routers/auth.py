from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.logger import logger

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, Token, UserResponse,SignupResponse
from app.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()

@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"POST /auth/signup - User registration attempt for email: {user_data.email}")
    
    # Check for duplicates
    email_norm = user_data.email.strip().lower()
    existing_user = db.query(User).filter(User.email == email_norm).first()
    if existing_user:
        logger.error(f"POST /auth/signup - Email already registered: {email_norm}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Create and save
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=email_norm,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=hashed_password,
        is_admin=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    logger.info(f"POST /auth/signup - User registered successfully: {email_norm}")

    # Two return options - choose one:

    # a. Return the ORM object itself (the model will extract only the 3 fields):
    return {
         "email": db_user.email,
         "first_name": db_user.first_name,
         "last_name": db_user.last_name
     }

@router.post("/signin", response_model=Token)
async def signin(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    logger.info(f"POST /auth/signin - Login attempt for email: {user_credentials.email}")
    
    # Find user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user:
        logger.error(f"POST /auth/signin - User not found: {user_credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user.hashed_password):
        logger.error(f"POST /auth/signin - Invalid password for user: {user_credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        logger.error(f"POST /auth/signin - Inactive user login attempt: {user_credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    logger.info(f"POST /auth/signin - User logged in successfully: {user_credentials.email}")
    
    return {
        "access_token": access_token,
        "token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_admin=user.is_admin,
            is_active=user.is_active,
            created_at=user.created_at
        )
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    logger.info(f"GET /auth/me - User info requested for: {current_user.email}")
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_admin=current_user.is_admin,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )
