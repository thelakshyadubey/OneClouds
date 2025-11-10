"""
Unified Multi-Cloud Storage Web Application
Main FastAPI application with comprehensive cloud storage integration
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
import json
import base64 # Added for base64 URL-safe encoding/decoding
import re # Added for email validation
from collections import defaultdict # Added for efficient duplicate grouping
import hashlib

from fastapi import FastAPI, Depends, HTTPException, Request, Response, BackgroundTasks, UploadFile, status, Form
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # Disabled for testing
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr # Explicitly import BaseModel and EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from email_validator import validate_email, EmailNotValidError # For email validation
from starlette.background import BackgroundTasks
from jose import JWTError # Added for JWT verification
from fastapi.security import HTTPAuthorizationCredentials # Added for HTTPBearer

# Local imports
from backend.config import settings, PROVIDER_CONFIGS

from backend.database import engine, SessionLocal, Base, get_db

from backend.models import User, StorageAccount, FileMetadata, SyncLog, UserSession, TrustedDevice, Job, UserPreferences # New models
from backend.storage_providers import get_provider_class, SUPPORTED_PROVIDERS
from backend.auth import AuthHandler # Use AuthHandler instance directly
from backend.utils import SecurityUtils, FileUtils, fm # Import fm for sending emails
import backend.schemas as schemas # Import schemas as an alias to resolve NameError

from backend.audit_logger import AuditLogger # Added for audit logging

# Initialize FastAPI app
app = FastAPI(
    title="Unified Multi-Cloud Storage API",
    description="A comprehensive API for managing files across multiple cloud storage providers",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Explicitly allow frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
auth_handler = AuthHandler()
# security = HTTPBearer()  # Disabled for testing
security_utils = SecurityUtils()
file_utils = FileUtils()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine) # Uncommented to ensure table creation on startup

# Dependency for getting current user - PROPER AUTHENTICATION
async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(auth_handler.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current user from JWT token - Requires authentication."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    logger.debug(f"get_current_user: Received token.credentials: {token.credentials}")
    try:
        payload = auth_handler.verify_token(token.credentials, token_type="access")
        if payload is None:
            logger.warning("get_current_user: Token verification returned None payload.")
            raise credentials_exception
        user_id: int = payload.get("user_id")
        if user_id is None:
            logger.warning("get_current_user: Token payload missing user_id.")
            raise credentials_exception
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception
        return user
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise credentials_exception

# Helper function to get the correct provider config key
def get_provider_config_key(provider: str, mode: str) -> str:
    """Get the correct config key for a provider and mode combination."""
    # Handle special case where database stores "metadata" but config uses "metadata_only"
    if mode == "metadata":
        return f"{provider}_metadata_only"
    else:
        return f"{provider}_{mode}"

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Authentication endpoints
@app.post("/api/auth/register", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_register: schemas.UserRegister, request: Request, db: Session = Depends(get_db)):
    """Register a new user - simplified without OTP"""
    print(f"DEBUG: Incoming registration data: {user_register.model_dump_json()}") # Log incoming data
    try:
        if user_register.password != user_register.confirm_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

        # Validate email format
        valid_email = validate_email(user_register.email, check_deliverability=False).email

        existing_user = db.query(User).filter(User.email == user_register.email).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

        hashed_password = auth_handler.hash_password(user_register.password)

        new_user = User(
            email=user_register.email,
            name=user_register.name,
            hashed_password=hashed_password,
            is_active=True, # User is active immediately (no OTP verification)
            is_2fa_enabled=False,
            mode="full_access" # New users start in full_access mode
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Generate tokens immediately
        access_token = auth_handler.create_token(data={"user_id": new_user.id}, token_type="access")
        refresh_token = auth_handler.create_token(data={"user_id": new_user.id}, token_type="refresh")

        logger.info(f"User {new_user.email} registered successfully.")
        return schemas.TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_id=new_user.id,
            email=new_user.email,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            requires_2fa=False,
            device_trusted=True
        )
    except EmailNotValidError as e:
        print(f"DEBUG: Email validation error: {e}") # Log email validation error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email address format.")
    except HTTPException as e:
        # Allow FastAPI's HTTPException to propagate as is
        raise e
    except Exception as e:
        logger.error(f"DEBUG: Unexpected error during registration: {e}", exc_info=True) # Log full exception info
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

# OTP verification endpoints disabled for testing - will be re-implemented later
# @app.post("/api/auth/verify-otp", response_model=schemas.TokenResponse)
# async def verify_otp(otp_verification: schemas.OTPVerification, request: Request, db: Session = Depends(get_db)):
#     """Verify OTP and activate user account, then return tokens."""
#     pass

@app.post("/api/auth/login", response_model=schemas.TokenResponse)
async def login(user_login: schemas.UserLogin, request: Request, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens - simplified without 2FA/OTP."""
    # Basic rate limiting for login attempts per IP
    ip_address = request.client.host
    if not security_utils.is_allowed(f"login_ip:{ip_address}", settings.FAILED_LOGIN_ATTEMPTS_LIMIT * 2, 300): # 10 attempts in 5 minutes
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts. Please try again later.")

    user = db.query(User).filter(User.email == user_login.email).first()

    if not user:
        # Increment failed attempts for a non-existent user as well to prevent enumeration
        security_utils.increment_failed_login_attempts(db, None, ip_address) # Pass None for user_id to track by IP
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")

    # Check if user is locked out
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account locked. Please try again later.")

    if not auth_handler.verify_password(user_login.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.FAILED_LOGIN_ATTEMPTS_LIMIT:
            user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
            user.failed_login_attempts = 0 # Reset for next lockout period
            db.commit()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Too many failed login attempts. Account locked.")
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")

    # Reset failed login attempts on successful password verification
    user.failed_login_attempts = 0
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Generate tokens
    access_token = auth_handler.create_token(data={"user_id": user.id}, token_type="access")
    refresh_token = auth_handler.create_token(data={"user_id": user.id}, token_type="refresh")

    logger.info(f"User {user.email} logged in successfully.")
    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        requires_2fa=False,
        device_trusted=True
    )

# OTP 2FA device verification disabled for testing - will be re-implemented later
# @app.post("/api/auth/device/verify-otp", response_model=schemas.TokenResponse)
# async def verify_device_otp(otp_verification: schemas.OTPVerification, request: Request, db: Session = Depends(get_db)):
#     """Verify OTP for a trusted device and return tokens."""
#     pass

@app.get("/api/auth/devices", response_model=List[schemas.TrustedDeviceResponse])
async def get_trusted_devices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all trusted devices for the current user."""
    devices = db.query(TrustedDevice).filter(TrustedDevice.user_id == current_user.id, TrustedDevice.is_active == True).all()
    return [
        schemas.TrustedDeviceResponse(
            id=device.id,
            device_fingerprint=device.device_fingerprint,
            name=device.name,
            last_used_at=device.last_used_at,
            created_at=device.created_at,
            is_active=device.is_active
        ) for device in devices
    ]

@app.delete("/api/auth/devices/{device_id}", response_model=schemas.GenericResponse)
async def delete_trusted_device(device_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a specific trusted device for the current user."""
    device = db.query(TrustedDevice).filter(
        and_(
            TrustedDevice.id == device_id,
            TrustedDevice.user_id == current_user.id
        )
    ).first()

    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trusted device not found.")
    
    # Instead of deleting, we can mark it inactive to keep an audit trail
    device.is_active = False
    db.commit()

    logger.info(f"User {current_user.email} revoked trusted device {device_id}.")
    return schemas.GenericResponse(message="Trusted device revoked successfully.")

@app.delete("/api/user/sessions/all", response_model=schemas.GenericResponse, status_code=status.HTTP_200_OK)
async def revoke_all_sessions(
    revoke_request: schemas.RevokeAllSessions,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke all active sessions and trusted devices for the current user."""
    # 1. Verify current password
    if not auth_handler.verify_password(revoke_request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password.")

    # 2. Invalidate all UserSession entries
    db.query(UserSession).filter(UserSession.user_id == current_user.id).delete()
    
    # 3. Mark all TrustedDevice entries as inactive
    db.query(TrustedDevice).filter(TrustedDevice.user_id == current_user.id).update({TrustedDevice.is_active: False})
    
    db.commit()

    AuditLogger.log_security_event(
        event_type="ALL_SESSIONS_REVOKED",
        details={
            "user_id": current_user.id,
            "user_email": current_user.email,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    logger.info(f"User {current_user.email} revoked all sessions and untrusted all devices.")
    return schemas.GenericResponse(message="All sessions and trusted devices have been revoked. You will be logged out from all devices.")

@app.delete("/api/user", response_model=schemas.GenericResponse, status_code=status.HTTP_200_OK)
async def delete_user_account(
    delete_request: schemas.UserDeleteAccount,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete the current user's account and all associated data."""
    # 1. Verify current password
    if not auth_handler.verify_password(delete_request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password.")

    # 2. Delete all associated data
    # Delete all file metadata
    db.query(FileMetadata).filter(FileMetadata.user_id == current_user.id).delete()
    # Delete all storage accounts
    db.query(StorageAccount).filter(StorageAccount.user_id == current_user.id).delete()
    # Delete all sync logs
    db.query(SyncLog).filter(SyncLog.user_id == current_user.id).delete()
    # Delete all user sessions
    db.query(UserSession).filter(UserSession.user_id == current_user.id).delete()
    # Delete all trusted devices
    db.query(TrustedDevice).filter(TrustedDevice.user_id == current_user.id).delete()
    # Delete user preferences
    db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).delete()

    # 3. Delete the user account itself
    db.delete(current_user)
    db.commit()

    AuditLogger.log_security_event(
        event_type="USER_ACCOUNT_DELETED",
        details={
            "user_id": current_user.id,
            "user_email": current_user.email,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    logger.info(f"User account {current_user.email} and all associated data deleted successfully.")
    return schemas.GenericResponse(message="Your account and all associated data have been permanently deleted.")

@app.post("/api/auth/refresh-token", response_model=schemas.TokenResponse)
async def refresh_access_token(refresh_token: str, request: Request, db: Session = Depends(get_db)):
    """Refresh an access token using a refresh token."""
    payload = auth_handler.verify_token(refresh_token, token_type="refresh")

    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found for refresh token.")

    # Optionally, verify device fingerprint if associated with the refresh token for extra security
    # For this implementation, we assume refresh tokens are generally tied to user and are valid until expiration

    new_access_token = auth_handler.create_token(data={"user_id": user.id}, token_type="access")
    logger.info(f"Access token refreshed for user {user.email}.")

    return schemas.TokenResponse(
        access_token=new_access_token,
        refresh_token=refresh_token, # Return the same refresh token unless we implement rotation
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        requires_2fa=user.is_2fa_enabled,
        device_trusted=True # Assume device is trusted if refresh token is valid
    )

# User Mode Endpoints
@app.get("/api/user/mode", response_model=schemas.ModeUpdate)
async def get_user_mode(current_user: User = Depends(get_current_user)):
    """Get the current user's access mode."""
    return schemas.ModeUpdate(mode=current_user.mode)

@app.get("/api/user", response_model=schemas.UserResponse)
async def get_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user details."""
    # Fetch additional data required for UserResponse
    storage_accounts_count = db.query(StorageAccount).filter(StorageAccount.user_id == current_user.id).count()
    total_files_count = db.query(FileMetadata).filter(FileMetadata.user_id == current_user.id).count()
    
    # Load preferences explicitly if they exist
    user_preferences = db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).first()
    
    return schemas.UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at, # Add created_at
        storage_accounts_count=storage_accounts_count, # Add storage_accounts_count
        total_files_count=total_files_count, # Add total_files_count
        mode=current_user.mode,
        is_2fa_enabled=current_user.is_2fa_enabled,
        is_active=current_user.is_active,
        last_login_at=current_user.last_login_at,
        # Pass UserPreferences instance directly if found, else None
        preferences=schemas.UserPreferences(**json.loads(user_preferences.preferences)) if user_preferences else None
    )

@app.put("/api/user/mode", response_model=schemas.GenericResponse)
async def update_user_mode(mode_update: schemas.ModeUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update the current user's access mode with audit logging."""
    if current_user.mode == mode_update.mode:
        return schemas.GenericResponse(message=f"User already in {mode_update.mode} mode.")

    previous_mode = current_user.mode
    current_user.mode = mode_update.mode
    current_user.last_mode_change_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    # Audit log entry for mode change
    AuditLogger.log_security_event(
        event_type="USER_MODE_CHANGE",
        details={
            "user_id": current_user.id,
            "user_email": current_user.email,
            "previous_mode": previous_mode,
            "new_mode": mode_update.mode,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    logger.info(f"User {current_user.email} changed mode from {previous_mode} to {mode_update.mode}.")
    return schemas.GenericResponse(message=f"User mode updated to {mode_update.mode}.")

@app.put("/api/user/email", response_model=schemas.GenericResponse, status_code=status.HTTP_200_OK)
async def update_user_email(
    email_update: schemas.UserEmailUpdate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current user's email address."""
    # 1. Verify current password
    if not auth_handler.verify_password(email_update.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password.")

    # 2. Validate new email
    try:
        valid_new_email = validate_email(email_update.new_email, check_deliverability=False).email
    except EmailNotValidError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid new email address format.")

    if valid_new_email == current_user.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email is the same as the current email.")

    existing_user_with_new_email = db.query(User).filter(User.email == valid_new_email).first()
    if existing_user_with_new_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This email address is already registered.")

    # 3. Invalidate all sessions (force re-login after email change for security)
    db.query(UserSession).filter(UserSession.user_id == current_user.id).delete()
    db.query(TrustedDevice).filter(TrustedDevice.user_id == current_user.id).update({TrustedDevice.is_active: False})
    
    # 4. Update user's email and mark as inactive until new email is verified
    current_user.email = valid_new_email
    current_user.is_active = False
    current_user.email_verification_token = secrets.token_urlsafe(32)
    current_user.email_verification_expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_TTL_MINUTES)
    db.commit()
    db.refresh(current_user)

    # 5. Send new OTP to the new email address for verification
    otp = security_utils.generate_otp(current_user.otp_secret)
    background_tasks.add_task(security_utils.send_otp_email, current_user.email, otp)

    AuditLogger.log_security_event(
        event_type="USER_EMAIL_CHANGE_INITIATED",
        details={
            "user_id": current_user.id,
            "old_email": current_user.email, # This will log the old email
            "new_email": valid_new_email,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    logger.info(f"User {current_user.email} initiated email change to {valid_new_email}. Verification email sent.")
    return schemas.GenericResponse(message="Email change initiated. Please check your new email for verification to reactivate your account.")

@app.put("/api/user/password", response_model=schemas.GenericResponse, status_code=status.HTTP_200_OK)
async def update_user_password(
    password_update: schemas.UserPasswordUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current user's password."""
    # 1. Verify current password
    if not auth_handler.verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password.")

    # 2. Check if new password is same as old password
    if auth_handler.verify_password(password_update.new_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password cannot be the same as the old password.")

    # 3. Hash new password and update
    current_user.hashed_password = auth_handler.hash_password(password_update.new_password)
    current_user.password_changed_at = datetime.utcnow()
    db.commit()

    # 4. Invalidate all sessions (force re-login after password change for security)
    db.query(UserSession).filter(UserSession.user_id == current_user.id).delete()
    db.query(TrustedDevice).filter(TrustedDevice.user_id == current_user.id).update({TrustedDevice.is_active: False})
    db.commit()

    AuditLogger.log_security_event(
        event_type="USER_PASSWORD_CHANGE",
        details={
            "user_id": current_user.id,
            "user_email": current_user.email,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    logger.info(f"User {current_user.email} successfully changed password. All sessions revoked.")
    return schemas.GenericResponse(message="Password updated successfully. You have been logged out from all devices.")

@app.post("/api/user/2fa/setup", response_model=Dict[str, str], status_code=status.HTTP_200_OK)
async def setup_two_factor_auth(
    auth_setup: schemas.TwoFactorAuthSetup,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate 2FA setup: verify password and return OTP secret and QR code URL."""
    if not auth_handler.verify_password(auth_setup.password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password.")

    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is already enabled for this account.")

    # Generate a new OTP secret if none exists or if re-setting
    if not current_user.otp_secret:
        current_user.otp_secret = security_utils.generate_otp_secret()
        db.commit()
        db.refresh(current_user)

    # Generate QR code for authenticator app
    otp_uri = security_utils.generate_otp_uri(current_user.email, current_user.otp_secret)
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={otp_uri}" # External QR code API

    AuditLogger.log_security_event(
        event_type="2FA_SETUP_INITIATED",
        details={
            "user_id": current_user.id,
            "user_email": current_user.email,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    logger.info(f"User {current_user.email} initiated 2FA setup. OTP secret generated.")
    return {"otp_secret": current_user.otp_secret, "qr_code_url": qr_code_url}

@app.post("/api/user/2fa/verify", response_model=schemas.GenericResponse, status_code=status.HTTP_200_OK)
async def verify_two_factor_auth(
    auth_verify: schemas.TwoFactorAuthVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify 2FA setup with OTP and enable 2FA for the user account."""
    if not current_user.otp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA setup not initiated. Please generate a secret first.")
    
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is already enabled for this account.")

    if not security_utils.verify_otp(current_user.otp_secret, auth_verify.otp):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP. Please try again.")

    current_user.is_2fa_enabled = True
    current_user.otp_verified_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    AuditLogger.log_security_event(
        event_type="2FA_SETUP_COMPLETED",
        details={
            "user_id": current_user.id,
            "user_email": current_user.email,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    logger.info(f"User {current_user.email} successfully enabled 2FA.")
    return schemas.GenericResponse(message="Two-Factor Authentication enabled successfully.")

@app.get("/api/user/preferences", response_model=schemas.UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's preferences."""
    preferences = db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).first()
    if not preferences:
        # If no preferences exist, return default preferences
        return schemas.UserPreferencesResponse(
            id=0, # Placeholder ID for default
            user_id=current_user.id,
            preferences=schemas.UserPreferences(),
            updated_at=datetime.utcnow()
        )
    return schemas.UserPreferencesResponse(
        id=preferences.id,
        user_id=preferences.user_id,
        preferences=schemas.UserPreferences(**json.loads(preferences.preferences)),
        updated_at=preferences.updated_at
    )

@app.put("/api/user/preferences", response_model=schemas.UserPreferencesResponse)
async def update_user_preferences(
    updated_preferences: schemas.UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's preferences."""
    preferences_db = db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).first()

    if not preferences_db:
        # Create default preferences if they don't exist
        default_preferences = schemas.UserPreferences().model_dump_json()
        preferences_db = UserPreferences(
            user_id=current_user.id,
            preferences=default_preferences,
            updated_at=datetime.utcnow()
        )
        db.add(preferences_db)
        db.commit()
        db.refresh(preferences_db)

    # Load existing preferences, update with new values, then save
    existing_preferences_dict = json.loads(preferences_db.preferences)
    update_data = updated_preferences.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        existing_preferences_dict[key] = value
    
    preferences_db.preferences = json.dumps(existing_preferences_dict)
    preferences_db.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(preferences_db)

    return schemas.UserPreferencesResponse(
        id=preferences_db.id,
        user_id=preferences_db.user_id,
        preferences=schemas.UserPreferences(**json.loads(preferences_db.preferences)),
        updated_at=preferences_db.updated_at
    )

@app.get("/api/storage-accounts", response_model=List[schemas.StorageAccountResponse])
async def get_storage_accounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all storage accounts linked to the current user."""
    accounts = db.query(StorageAccount).filter(StorageAccount.user_id == current_user.id).all()
    responses = []
    for account in accounts:
        files_count = db.query(FileMetadata).filter(
            FileMetadata.storage_account_id == account.id,
            FileMetadata.is_active == True
        ).count()
        responses.append(
            schemas.StorageAccountResponse(
                id=account.id,
                provider=account.provider,
                mode=account.mode,
                account_email=account.account_email,
                is_active=account.is_active,
                created_at=account.created_at,
                storage_used=account.storage_used,
                storage_limit=account.storage_limit,
                files_count=files_count
            )
        )
    return responses

@app.get("/api/auth/{provider}")
async def initiate_auth(
    provider: str,
    mode: str, # Added to specify metadata-only or read-write
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate OAuth flow for a cloud provider"""
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported provider: {provider}")

    if mode not in ["metadata", "full_access"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported mode: {mode}. Must be 'metadata' or 'full_access'.")
    
    # Enforce mode access: if user is in metadata mode, they can only connect metadata accounts
    if current_user.mode == "metadata" and mode == "full_access":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot connect full access account while in metadata mode. Switch mode in settings first."
        )
    elif current_user.mode == "full_access" and mode == "metadata":
        # Allow connecting metadata account even if in full access mode for flexibility
        pass

    try:
        # Map frontend mode to backend config key
        mode_mapping = {
            "metadata": "metadata_only",
            "full_access": "full_access"
        }
        mapped_mode = mode_mapping.get(mode, mode)
        
        # Construct the configuration key based on provider and mode
        # e.g., "google_drive_metadata_only" or "google_drive_full_access"
        config_key = f"{provider}_{mapped_mode}"
        provider_config = PROVIDER_CONFIGS.get(config_key)

        if not provider_config:
            logger.error(f"Missing configuration for {config_key}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Provider configuration missing for the selected mode")

        provider_class = get_provider_class(provider)
        client_id = provider_config["client_id"]
        redirect_uri = provider_config["redirect_uri"]
        scopes = provider_config["scopes"]
        authorization_base_url = provider_config["authorization_base_url"]

        # Remove direct access to settings.GOOGLE_DRIVE_FULL_ACCESS_CLIENT_ID etc.
        # Instead, use the variables already extracted from provider_config
        print(f"DEBUG (initiate_auth): Client ID: {client_id}")
        print(f"DEBUG (initiate_auth): Redirect URI: {redirect_uri}")
        print(f"DEBUG (initiate_auth): Scopes being used: {scopes}")
        print(f"DEBUG (initiate_auth): Using redirect_uri: {redirect_uri} for {config_key}") # Using print for guaranteed output
        if not client_id or not redirect_uri or not scopes:
            logger.error(f"Incomplete configuration for {config_key}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Provider configuration incomplete")

        # Encode user_id, mode, and a CSRF nonce into the state parameter
        state_data = {"user_id": current_user.id, "mode": mode, "nonce": secrets.token_urlsafe(32)}
        state_encoded = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

        oauth_url = provider_class.get_authorization_url(
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state_encoded,
            scopes=scopes,
            authorization_base_url=authorization_base_url
        )
        
        if not oauth_url:
            logger.error(f"Failed to generate OAuth URL for {provider} in {mode} mode.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate OAuth URL for provider.")

        logger.info(f"Returning OAuth URL for {provider} in {mode} mode: {oauth_url}")
        return JSONResponse(content={"oauth_url": oauth_url})
    
    except AttributeError as ae:
        logger.error(f"Configuration error for {provider}: {ae}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Provider configuration error")
    except Exception as e:
        logger.error(f"Auth initiation error for {provider}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initiate authentication")

@app.get("/api/auth/{provider}/{callback_suffix}-callback")
async def auth_callback(
    provider: str, 
    callback_suffix: str, # Capture the suffix like 'readwrite' or 'metadata'
    code: str,
    background_tasks: BackgroundTasks, # Moved to correct position
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from cloud provider"""
    # Extract the mode directly from the state parameter
    if not state:
        print("DEBUG (auth_callback): Auth callback received without state parameter.") # Using print
        logger.error("Auth callback received without state parameter.")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/error?detail=No state parameter")

    try:
        # Decode and parse state parameter
        state_decoded_bytes = base64.urlsafe_b64decode(state.encode())
        state_data = json.loads(state_decoded_bytes.decode())
        user_id = state_data.get("user_id")
        mode = state_data.get("mode") # Retrieve the mode directly from state
        # nonce = state_data.get("nonce") # For CSRF validation if needed

        print(f"DEBUG (auth_callback): Reconstructed mode from state: '{mode}'") # Using print
        print(f"DEBUG (auth_callback): Callback suffix: {callback_suffix}") # Added for debugging
        print(f"DEBUG (auth_callback): settings.BACKEND_URL: {settings.BACKEND_URL}") # Added for debugging

        if not user_id or not mode:
            print(f"DEBUG (auth_callback): Callback state missing user_id or mode for provider {provider}") # Using print
            logger.error(f"Callback state missing user_id or mode for provider {provider}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state parameter: missing user ID or mode")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"DEBUG (auth_callback): User with ID {user_id} not found during auth callback for provider {provider}") # Using print
            logger.error(f"User with ID {user_id} not found during auth callback for provider {provider}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Map frontend mode to backend config key
        mode_mapping = {
            "metadata": "metadata_only",
            "full_access": "full_access"
        }
        mapped_mode = mode_mapping.get(mode, mode)
        
        # Construct the configuration key based on provider and mode
        config_key = f"{provider}_{mapped_mode}"
        print(f"DEBUG (auth_callback): Config key constructed: '{config_key}'") # Using print
        provider_config = PROVIDER_CONFIGS.get(config_key)

        if not provider_config:
            print(f"DEBUG (auth_callback): Missing configuration for {config_key} during callback") # Using print
            logger.error(f"Missing configuration for {config_key} during callback")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Provider configuration missing for the selected mode during callback")
        
        provider_class = get_provider_class(provider)
        
        # Exchange code for tokens using mode-specific credentials
        token_data = await provider_class.exchange_code_for_token(
            code=code,
            client_id=provider_config["client_id"],
            client_secret=provider_config["client_secret"],
            redirect_uri=provider_config["redirect_uri"],
            scopes=provider_config["scopes"]
        )
        print(f"DEBUG (auth_callback): Received token_data from provider: {token_data}") # NEW: Log token_data

        # Initialize a temporary provider instance to get user info before querying/creating storage account
        temp_provider_instance = provider_class(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            mode=mode,
            client_id=provider_config["client_id"],
            client_secret=provider_config["client_secret"],
            db_session=None, # No DB session needed for temp instance
            storage_account_id=None # No ID needed for temp instance
        )

        # Get user info from the cloud provider (this gives the external account's email)
        user_info = await temp_provider_instance.get_user_info()
        
        # Find or create storage account associated with the specific user, external email, AND MODE
        storage_account = db.query(StorageAccount).filter(
            and_(
                StorageAccount.user_id == user.id, # Link to the authenticated internal user
                StorageAccount.provider == provider,
                StorageAccount.account_email == user_info["email"],
                StorageAccount.mode == mode # IMPORTANT: Filter by mode
            )
        ).first()

        # Now, initialize the main provider instance with the correct db_session and storage_account_id
        provider_instance = provider_class(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            mode=mode,
            client_id=provider_config["client_id"],
            client_secret=provider_config["client_secret"],
            db_session=db, # Pass the database session
            storage_account_id=storage_account.id if storage_account else None # Pass existing ID or None
        )
        
        # If the token was refreshed during get_user_info, update the current access token
        # Note: This implies provider_instance.refresh_access_token() might be called internally
        # by make_request if a token expires, and then access_token on the instance is updated.
        # We need to ensure that update propagates back to the DB.
        # However, for now, we rely on the initial token_data and future scheduled refreshes.

        if not storage_account:
            # This is a new storage account for this user
            storage_account = StorageAccount(
                user_id=user.id,
                provider=provider,
                mode=mode, # Store the mode
                account_email=user_info["email"],
                access_token=security_utils.encrypt_token(token_data["access_token"]),
                refresh_token=security_utils.encrypt_token(token_data.get("refresh_token")) if token_data.get("refresh_token") else None,
                token_expires_at=datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600)),
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(storage_account)
        else:
            # Update existing storage account
            storage_account.access_token = security_utils.encrypt_token(token_data["access_token"])
            if token_data.get("refresh_token"):
                storage_account.refresh_token = security_utils.encrypt_token(token_data["refresh_token"])
            storage_account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
            storage_account.is_active = True
            storage_account.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Schedule initial sync for the newly connected/updated storage account
        background_tasks.add_task(sync_account_files, storage_account.id, db, user.id, security_utils)
        
        # Create JWT token for the user (the internal user, not the external account)
        access_token_jwt = auth_handler.create_token(data={"user_id": user.id}, token_type="access")
        
        logger.info(f"DEBUG: Backend generated FULL JWT for user {user.id}: {access_token_jwt}") # Log full token

        # Redirect to frontend with token
        frontend_url = f"{settings.FRONTEND_URL}/auth/success?token={access_token_jwt}&provider={provider}&mode={mode}"
        print(f"DEBUG (auth_callback): FINAL REDIRECT URL: {frontend_url}") # Add this print statement
        logger.info(f"DEBUG: Redirecting to frontend URL: {frontend_url}")
        return RedirectResponse(url=frontend_url)
    
    except Exception as e:
        logger.error(f"Auth callback FAILED for {provider}. Error details: {e}", exc_info=True) # Log full exception
        # Log the exact redirect_uri that was used in the failed OAuth call if possible
        failed_redirect_uri = provider_config.get("redirect_uri", "N/A") if 'provider_config' in locals() else "N/A"
        logger.error(f"DEBUG: Failed OAuth redirect_uri: {failed_redirect_uri}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/error?detail={e}")

# Background task for syncing files
async def sync_account_files(
    account_id: int,
    db: Session,
    user_id: int,
    security_utils_instance: SecurityUtils # Pass the instance
):
    """Background task to synchronize files for a storage account."""
    try:
        # Re-fetch the account within this new session context to avoid issues with stale objects
        storage_account = db.query(StorageAccount).filter(StorageAccount.id == account_id, StorageAccount.user_id == user_id).first()
        if not storage_account:
            logger.error(f"Sync: Storage account {account_id} not found for user {user_id}.")
            return

        provider_class = get_provider_class(storage_account.provider)
        
        # Get the correct config key for this provider and mode
        config_key = get_provider_config_key(storage_account.provider, storage_account.mode)
        
        provider_config = PROVIDER_CONFIGS.get(config_key)
        if not provider_config:
            logger.error(f"Sync: Provider config not found for key '{config_key}'")
            return
        
        provider_instance = provider_class(
            access_token=security_utils_instance.decrypt_token(storage_account.access_token),
            refresh_token=security_utils_instance.decrypt_token(storage_account.refresh_token) if storage_account.refresh_token else None,
            mode=storage_account.mode,
            client_id=provider_config["client_id"],
            client_secret=provider_config["client_secret"],
            db_session=db, # Pass the database session
            storage_account_id=storage_account.id # Pass the storage account ID
        )

        logger.info(f"Sync: Starting sync for account {account_id} ({storage_account.provider} - {storage_account.account_email}) in {storage_account.mode} mode.")

        # Fetch files from cloud provider
        cloud_files = await provider_instance.list_files()

        # Add a null check for cloud_files to prevent TypeError
        if cloud_files is None or not isinstance(cloud_files, dict) or "files" not in cloud_files:
            logger.error(f"Sync: Failed to fetch files for account {account_id}. Received unexpected response: {cloud_files}")
            return # Exit sync if file fetching failed

        logger.info(f"Sync: Fetched {len(cloud_files.get('files', []))} files from {storage_account.provider} for account {account_id}.")

        # Retrieve existing file metadata for this account
        existing_metadata = {
            f.provider_file_id: f for f in db.query(FileMetadata).filter(FileMetadata.storage_account_id == account_id).all()
        }

        new_or_updated_count = 0
        deleted_count = 0
        
        # Track files that are still present in the cloud
        current_cloud_file_ids = set()

        # Proceed with file processing only if cloud_files is valid
        if cloud_files and "files" in cloud_files and isinstance(cloud_files["files"], list):
            # Process cloud files: add new or update existing
            for cloud_file_data in cloud_files.get('files', []):
                provider_file_id = cloud_file_data["provider_file_id"]
                current_cloud_file_ids.add(provider_file_id)

                existing_file = existing_metadata.get(provider_file_id)

                # For metadata mode, we don't store content hash or size directly if not provided
                # We'll rely on the provider to give us what it can.

                # compute a size-based hash (name + size + mime_type) to help duplicate detection
                def _compute_size_hash(name, size, mime_type):
                    try:
                        if name and size is not None:
                            s = f"{name.lower()}_{size}_{mime_type or ''}"
                            return hashlib.md5(s.encode()).hexdigest()
                    except Exception:
                        return None
                    return None

                computed_size_hash = _compute_size_hash(cloud_file_data.get("name"), cloud_file_data.get("size"), cloud_file_data.get("mime_type"))

                if existing_file:
                    # Update existing file metadata if changed
                    # Only update fields that might change and are relevant for metadata mode
                    if (existing_file.name != cloud_file_data["name"] or
                        existing_file.mime_type != cloud_file_data["mime_type"] or
                        existing_file.is_folder != cloud_file_data.get("is_folder", False) or # Compare is_folder
                        existing_file.size != cloud_file_data.get("size") or
                        existing_file.modified_at_source != cloud_file_data.get("modified_at") or
                        existing_file.content_hash != cloud_file_data.get("content_hash") or
                        existing_file.web_view_link != cloud_file_data.get("web_view_link") or # Check if web_view_link changed
                        existing_file.preview_link != cloud_file_data.get("preview_link")): # Check if preview_link changed

                        existing_file.name = cloud_file_data["name"]
                        existing_file.path = cloud_file_data.get("path")
                        existing_file.mime_type = cloud_file_data["mime_type"]
                        existing_file.is_folder = cloud_file_data.get("is_folder", False)
                        existing_file.size = cloud_file_data.get("size")
                        existing_file.created_at_source = cloud_file_data.get("created_at")
                        existing_file.modified_at_source = cloud_file_data.get("modified_at")
                        existing_file.download_link = cloud_file_data.get("download_link")
                        existing_file.preview_link = cloud_file_data.get("preview_link")
                        existing_file.web_view_link = cloud_file_data.get("web_view_link") # Added web_view_link
                        existing_file.content_hash = cloud_file_data.get("content_hash") # Use 'content_hash' from provider for content_hash
                        # Ensure we always populate a size_hash for fallback duplicate detection
                        existing_file.size_hash = computed_size_hash or existing_file.size_hash
                        existing_file.updated_at = datetime.utcnow()
                        existing_file.is_active = True # Ensure it's marked active
                        new_or_updated_count += 1
                else:
                    # Create new file metadata entry
                    new_file = FileMetadata(
                        user_id=user_id,
                        storage_account_id=account_id,
                        provider_file_id=provider_file_id,
                        name=cloud_file_data["name"],
                        path=cloud_file_data.get("path"),  # Use 'path' from normalized data
                        mime_type=cloud_file_data["mime_type"],
                        is_folder=cloud_file_data.get("is_folder", False), # Added is_folder
                        size=cloud_file_data.get("size"),
                        # Explicitly map created_at to created_at_source and modified_at to modified_at_source
                        created_at_source=cloud_file_data.get("created_at"),
                        modified_at_source=cloud_file_data.get("modified_at"),
                        download_link=cloud_file_data.get("download_link"),
                        preview_link=cloud_file_data.get("preview_link"),
                        web_view_link=cloud_file_data.get("web_view_link"), # Added web_view_link
                        content_hash=cloud_file_data.get("content_hash"), # Use 'content_hash' from provider for content_hash
                        size_hash=computed_size_hash,
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(new_file)
                    new_or_updated_count += 1

            # Mark files as inactive if they are no longer in the cloud and list_files was successful
            for provider_file_id, file_obj in existing_metadata.items():
                if provider_file_id not in current_cloud_file_ids and file_obj.is_active:
                    file_obj.is_active = False
                    file_obj.updated_at = datetime.utcnow()
                    deleted_count += 1

        else:
            logger.warning(f"Sync: Skipping file inactivation for account {account_id} due to invalid or empty cloud file list from API.")

        db.commit()
        
        # Update storage metrics for the account from provider API
        try:
            quot_info = await provider_instance.get_storage_quota()
            if quot_info:
                # Always update both used and limit from API (most accurate)
                if quot_info.get("total"):
                    storage_account.storage_limit = quot_info["total"]
                if quot_info.get("used") is not None:
                    storage_account.storage_used = quot_info["used"]
                logger.info(f"Sync: Updated storage quota from API - Used: {file_utils.format_file_size(quot_info.get('used', 0))}, Limit: {file_utils.format_file_size(quot_info.get('total', 0))}")
        except Exception as quota_e:
            logger.warning(f"Could not fetch storage quota for account {account_id}: {quota_e}")
            # Fallback: calculate from file metadata if API fails
            total_used_bytes = db.query(func.sum(FileMetadata.size)).filter(
                and_(
                    FileMetadata.storage_account_id == account_id,
                    FileMetadata.is_folder == False,
                    FileMetadata.is_active == True
                )
            ).scalar() or 0
            storage_account.storage_used = total_used_bytes

        db.commit()
        db.refresh(storage_account) # Refresh to get latest storage_used/limit
        
        logger.info(f"Sync: Completed sync for account {account_id}. New/Updated: {new_or_updated_count}, Inactive: {deleted_count}.")
    
    except Exception as e:
        logger.error(f"Sync: Failed to synchronize account {account_id}: {e}", exc_info=True)
        db.rollback() # Rollback any changes if sync fails

@app.post("/api/storage-accounts/{account_id}/sync", response_model=schemas.GenericResponse)
async def sync_account(
    account_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger synchronization for a specific storage account."""
    storage_account = db.query(StorageAccount).filter(
        and_(
            StorageAccount.id == account_id,
            StorageAccount.user_id == current_user.id
        )
    ).first()

    if not storage_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage account not found.")

    # Sync is allowed for both metadata and full_access modes
    # Metadata mode can read file metadata, just can't modify files

    # Schedule the sync as a background task
    background_tasks.add_task(sync_account_files, storage_account.id, db, current_user.id, security_utils)

    logger.info(f"Sync: User {current_user.email} triggered manual sync for account {account_id}.")
    return schemas.GenericResponse(message="Synchronization initiated successfully.")

@app.post("/api/storage-accounts/sync-all", response_model=schemas.GenericResponse)
async def sync_all_accounts(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger synchronization for all connected storage accounts."""
    accounts_to_sync = db.query(StorageAccount).filter(
        and_(
            StorageAccount.user_id == current_user.id,
            StorageAccount.is_active == True
            # Sync is now allowed for both metadata and full_access modes
        )
    ).all()

    if not accounts_to_sync:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active storage accounts found for synchronization.")

    for account in accounts_to_sync:
        background_tasks.add_task(sync_account_files, account.id, db, current_user.id, security_utils)

    logger.info(f"Sync: User {current_user.email} triggered manual sync for all eligible accounts.")
    return schemas.GenericResponse(message=f"Synchronization initiated for {len(accounts_to_sync)} accounts.")

# File management endpoints
@app.get("/api/files", response_model=schemas.FileListResponse)
async def get_files(
    provider: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "modified_at_source",
    sort_order: str = "desc",
    page: int = 1,
    per_page: int = 50,
    mode: Optional[str] = None, # New: Add mode parameter
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's files with filtering, searching, and sorting"""
    from sqlalchemy.orm import joinedload
    
    query = db.query(FileMetadata).options(joinedload(FileMetadata.storage_account)).filter(FileMetadata.user_id == current_user.id)
    
    # Only show active files by default, unless explicitly requested
    query = query.filter(FileMetadata.is_active == True)
    
    logger.debug(f"get_files: user_id={current_user.id}, provider={provider}, mode={mode}, search={search}")
    
    # Join with StorageAccount if we need to filter by mode or provider
    needs_join = mode or provider
    if needs_join:
        query = query.join(StorageAccount)
    
    # Apply mode filter
    if mode:
        query = query.filter(
            and_(
                StorageAccount.mode == mode,
                StorageAccount.user_id == current_user.id # Ensure account belongs to current user
            )
        )

    # Apply provider filter
    if provider:
        query = query.filter(
            and_(
                StorageAccount.provider == provider,
                StorageAccount.user_id == current_user.id # Ensure provider belongs to current user
            )
        )
    
    if search:
        query = query.filter(FileMetadata.name.contains(search))
    
    # Apply sorting
    if hasattr(FileMetadata, sort_by):
        sort_column = getattr(FileMetadata, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    
    # Pagination
    total = query.count()
    files = query.offset((page - 1) * per_page).limit(per_page).all()
    
    logger.debug(f"get_files: Found {total} total files, returning {len(files)} files for page {page}")
    
    return schemas.FileListResponse(
        files=[file_utils.file_to_response(file) for file in files],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page
    )

@app.get("/api/large-files", response_model=schemas.FileListResponse)
async def get_large_files(
    size_threshold_mb: int = 100, # Default to 100MB
    provider: Optional[str] = None,
    sort_by: str = "size",
    sort_order: str = "desc",
    page: int = 1,
    per_page: int = 50,
    mode: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's large files with filtering, searching, and sorting"""
    size_threshold_bytes = size_threshold_mb * (1024 ** 2)

    query = db.query(FileMetadata).filter(
        FileMetadata.user_id == current_user.id,
        FileMetadata.is_active == True,
        FileMetadata.is_folder == False, # Only consider actual files, not folders
        FileMetadata.size >= size_threshold_bytes
    )
    
    # Apply mode filter
    if mode:
        query = query.join(StorageAccount).filter(
            and_(
                StorageAccount.mode == mode,
                StorageAccount.user_id == current_user.id
            )
        )

    # Apply provider filter
    if provider:
        query = query.join(StorageAccount).filter(
            and_(
                StorageAccount.provider == provider,
                StorageAccount.user_id == current_user.id
            )
        )
    
    # Apply sorting
    if hasattr(FileMetadata, sort_by):
        sort_column = getattr(FileMetadata, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    
    # Pagination
    total = query.count()
    files = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return schemas.FileListResponse(
        files=[file_utils.file_to_response(file) for file in files],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page
    )

@app.post("/api/duplicates/remove")
async def remove_duplicate_files(
    request_data: schemas.RemoveDuplicatesRequest, # Import from schemas
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove selected duplicate files from cloud storage and local database"""
    successful_deletions = []
    failed_deletions = []
    errors = []

    for file_id in request_data.file_ids:
        file_metadata = db.query(FileMetadata).filter(
            and_(
                FileMetadata.id == file_id,
                FileMetadata.user_id == current_user.id
            )
        ).first()

        if not file_metadata:
            errors.append(f"File with ID {file_id} not found or does not belong to user.")
            failed_deletions.append(file_id)
            continue
        
        try:
            storage_account = file_metadata.storage_account
            if not storage_account:
                errors.append(f"Storage account not found for file ID {file_id}.")
                failed_deletions.append(file_id)
                continue

            # CRITICAL: Enforce mode-based restriction
            if storage_account.mode == "metadata":
                errors.append(f"File deletion not allowed for metadata mode account ('{storage_account.account_email}' in {storage_account.provider}). File ID: {file_id}")
                failed_deletions.append(file_id)
                continue

            config_key = f"{storage_account.provider}_{storage_account.mode}"
            if config_key not in PROVIDER_CONFIGS:
                errors.append(f"Provider configuration not found: {config_key} for file ID {file_id}")
                failed_deletions.append(file_id)
                continue

            provider_class = get_provider_class(storage_account.provider)
            provider = provider_class(
                access_token=security_utils.decrypt_token(storage_account.access_token),
                refresh_token=security_utils.decrypt_token(storage_account.refresh_token) if storage_account.refresh_token else None,
                mode=storage_account.mode,
                client_id=PROVIDER_CONFIGS[config_key]["client_id"],
                client_secret=PROVIDER_CONFIGS[config_key]["client_secret"],
                db_session=db,
                storage_account_id=storage_account.id
            )
            
            await provider.delete_file(file_metadata.provider_file_id)
            db.delete(file_metadata)
            db.commit()
            successful_deletions.append(file_id)
        
        except Exception as e:
            db.rollback() # Rollback changes for this specific file if an error occurs
            logger.error(f"Failed to delete file {file_id} from cloud or database: {e}", exc_info=True)
            errors.append(f"Failed to delete file {file_id}: {str(e)}")
            failed_deletions.append(file_id)
            
    if failed_deletions:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            "message": "Some files could not be deleted.",
            "successful_deletions": successful_deletions,
            "failed_deletions": failed_deletions,
            "errors": errors
        })
    
    return {"message": "Selected duplicate files deleted successfully", "successful_deletions": successful_deletions}

@app.get("/api/duplicates", response_model=List[schemas.DuplicateGroupResponse])
async def get_duplicates(
    mode: Optional[str] = None, # New: Add mode parameter
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get duplicate files grouped by hash"""
    # We'll attempt duplicates detection in multiple passes to handle providers that don't
    # always provide content_hash:
    # 1) Group by content_hash (most reliable)
    # 2) Group by size_hash (fallback, computed from name+size+mime)
    # 3) Final fallback: group by (lower(name), size)

    duplicate_groups = []
    seen_file_ids = set()

    # Helper to apply mode filter
    def apply_mode_filter(q):
        if mode:
            q = q.join(StorageAccount).filter(
                and_(
                    StorageAccount.mode == mode,
                    StorageAccount.user_id == current_user.id
                )
            )
        return q

    # PASS 1: content_hash based groups
    content_q = db.query(FileMetadata).filter(
        FileMetadata.user_id == current_user.id,
        FileMetadata.content_hash.isnot(None),
        FileMetadata.is_active == True
    )
    content_q = apply_mode_filter(content_q)

    content_duplicates = content_q.with_entities(FileMetadata.content_hash, func.count(FileMetadata.id).label('cnt'))\
        .group_by(FileMetadata.content_hash).having(func.count(FileMetadata.id) > 1).all()

    for row in content_duplicates:
        chash = row[0]
        files = db.query(FileMetadata).filter(
            FileMetadata.user_id == current_user.id,
            FileMetadata.content_hash == chash,
            FileMetadata.is_active == True
        )
        files = apply_mode_filter(files).order_by(FileMetadata.name).all()
        group_files = [f for f in files if f.id not in seen_file_ids]
        if len(group_files) > 1:
            for f in group_files:
                seen_file_ids.add(f.id)
            duplicate_groups.append(schemas.DuplicateGroupResponse(
                hash=chash,
                count=len(group_files),
                files=[file_utils.file_to_response(file) for file in group_files]
            ))

    # PASS 2: size_hash based groups (fallback)
    size_q = db.query(FileMetadata).filter(
        FileMetadata.user_id == current_user.id,
        FileMetadata.size_hash.isnot(None),
        FileMetadata.is_active == True
    )
    size_q = apply_mode_filter(size_q)

    size_duplicates = size_q.with_entities(FileMetadata.size_hash, func.count(FileMetadata.id).label('cnt'))\
        .group_by(FileMetadata.size_hash).having(func.count(FileMetadata.id) > 1).all()

    for row in size_duplicates:
        shash = row[0]
        files = db.query(FileMetadata).filter(
            FileMetadata.user_id == current_user.id,
            FileMetadata.size_hash == shash,
            FileMetadata.is_active == True
        )
        files = apply_mode_filter(files).order_by(FileMetadata.name).all()
        group_files = [f for f in files if f.id not in seen_file_ids]
        if len(group_files) > 1:
            for f in group_files:
                seen_file_ids.add(f.id)
            duplicate_groups.append(schemas.DuplicateGroupResponse(
                hash=shash,
                count=len(group_files),
                files=[file_utils.file_to_response(file) for file in group_files]
            ))

    # PASS 3: final fallback grouping by (lower(name), size) for providers that give only name/size
    name_size_q = db.query(FileMetadata).filter(
        FileMetadata.user_id == current_user.id,
        FileMetadata.name.isnot(None),
        FileMetadata.size.isnot(None),
        FileMetadata.is_active == True
    )
    name_size_q = apply_mode_filter(name_size_q)

    # build an in-memory map keyed by (lower(name), size)
    groups = defaultdict(list)
    for f in name_size_q.order_by(FileMetadata.name).all():
        if f.id in seen_file_ids:
            continue
        key = (f.name.lower(), f.size)
        groups[key].append(f)

    for key, files_in_group in groups.items():
        if len(files_in_group) > 1:
            for f in files_in_group:
                seen_file_ids.add(f.id)
            # create a synthetic hash key for display (name_size::<name>::<size>)
            synthetic_hash = f"name_size::{key[0]}::{key[1]}"
            duplicate_groups.append(schemas.DuplicateGroupResponse(
                hash=synthetic_hash,
                count=len(files_in_group),
                files=[file_utils.file_to_response(file) for file in files_in_group]
            ))

    return duplicate_groups

@app.delete("/api/files/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a file from cloud storage and local database"""
    file_metadata = db.query(FileMetadata).filter(
        and_(
            FileMetadata.id == file_id,
            FileMetadata.user_id == current_user.id
        )
    ).first()
    
    if not file_metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    try:
        # Get provider instance
        storage_account = file_metadata.storage_account
        if storage_account.mode == "metadata":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="File deletion is not available in Metadata Mode. Please switch to Full Access Mode to delete files."
            )
    
        config_key = f"{storage_account.provider}_{storage_account.mode}"
        if config_key not in PROVIDER_CONFIGS:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Provider configuration not found: {config_key}")
        
        provider_class = get_provider_class(storage_account.provider)
        provider = provider_class(
            access_token=security_utils.decrypt_token(storage_account.access_token),
            refresh_token=security_utils.decrypt_token(storage_account.refresh_token) if storage_account.refresh_token else None,
            mode=storage_account.mode,
            client_id=PROVIDER_CONFIGS[config_key]["client_id"],
            client_secret=PROVIDER_CONFIGS[config_key]["client_secret"],
            db_session=db,
            storage_account_id=storage_account.id
        )
        
        # Delete from cloud storage
        await provider.delete_file(file_metadata.provider_file_id)
        
        # Delete from database
        db.delete(file_metadata)
        db.commit()
        
        return {"message": "File deleted successfully"}
    
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete file")

@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile,
    provider: str = Form(...),
    folder_path: str = Form("/"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file to a specific cloud storage provider"""
    logger.info(f"=== UPLOAD ENDPOINT HIT ===")
    logger.info(f"File: {file.filename}, Content-Type: {file.content_type}")
    logger.info(f"Provider: {provider}")
    logger.info(f"Folder Path: {folder_path}")
    logger.info(f"User ID: {current_user.id}")
    logger.info(f"========================")
    
    storage_account = db.query(StorageAccount).filter(
        and_(
            StorageAccount.user_id == current_user.id,
            StorageAccount.provider == provider,
            StorageAccount.is_active == True
        )
    ).first()
    
    if not storage_account:
        logger.error(f"Storage account not found - User: {current_user.id}, Provider: {provider}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage account not found")

    if storage_account.mode == "metadata":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Uploads not allowed for metadata mode accounts")
    
    try:
        # Get provider configuration
        config_key = f"{storage_account.provider}_{storage_account.mode}"
        if config_key not in PROVIDER_CONFIGS:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Provider configuration not found: {config_key}")
        
        # Get provider instance with full configuration
        provider_class = get_provider_class(provider)
        provider_instance = provider_class(
            access_token=security_utils.decrypt_token(storage_account.access_token),
            refresh_token=security_utils.decrypt_token(storage_account.refresh_token) if storage_account.refresh_token else None,
            mode=storage_account.mode,
            client_id=PROVIDER_CONFIGS[config_key]["client_id"],
            client_secret=PROVIDER_CONFIGS[config_key]["client_secret"],
            db_session=db,
            storage_account_id=storage_account.id
        )
        
        # Upload file
        logger.info(f"Reading file content for: {file.filename}")
        file_content = await file.read()
        logger.info(f"File size: {len(file_content)} bytes")
        
        logger.info(f"Uploading to {provider} via provider instance")
        result = await provider_instance.upload_file(
            file_name=file.filename,
            file_content=file_content,
            folder_path=folder_path,
            mime_type=file.content_type
        )
        
        logger.info(f"Upload successful, creating metadata for: {file.filename}")
        # Create file metadata in database - extract file data from result
        file_data = result.get('file', result)  # Handle both formats
        file_metadata = file_utils.create_file_metadata(
            storage_account.user_id,
            storage_account.id,
            file_data
        )
        db.add(file_metadata)
        db.commit()
        db.refresh(file_metadata)
        
        logger.info(f"File uploaded successfully: {file.filename}")
        return {"message": "File uploaded successfully", "file": file_utils.file_to_response(file_metadata)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload file: {str(e)}")

@app.delete("/api/storage-accounts/{account_id}")
async def delete_storage_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a storage account and its associated files"""
    storage_account = db.query(StorageAccount).filter(
        and_(
            StorageAccount.id == account_id,
            StorageAccount.user_id == current_user.id
        )
    ).first()

    if not storage_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage account not found")

    try:
        # Invalidate provider tokens first if possible (provider-specific logic needed)
        # For now, we only delete from our DB.
        
        # Delete all files associated with this storage account
        db.query(FileMetadata).filter(FileMetadata.storage_account_id == account_id).delete()
        
        # Delete the storage account itself
        db.delete(storage_account)
        db.commit()

        AuditLogger.log_action(current_user.id, "DELETE_STORAGE_ACCOUNT", "storage_account", account_id, {"provider": storage_account.provider, "email": storage_account.account_email})

        return {"message": "Storage account and all associated files deleted successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete storage account {account_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete storage account")

@app.get("/api/files/{file_id}/preview")
async def get_file_preview(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get preview link for a file"""
    file_metadata = db.query(FileMetadata).filter(
        and_(
            FileMetadata.id == file_id,
            FileMetadata.user_id == current_user.id
        )
    ).first()
    
    if not file_metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    storage_account = file_metadata.storage_account
    
    # For metadata mode, return web_view_link if available (read-only preview)
    # For full_access mode, return preview_link (can view and download)
    if storage_account.mode == "metadata":
        if file_metadata.web_view_link:
            return {"preview_url": file_metadata.web_view_link}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview link not available for this file")
    
    if file_metadata.preview_link:
        return {"preview_url": file_metadata.preview_link}
    
    # Generate preview link if not available (full_access mode only)
    try:
        
        provider_class = get_provider_class(storage_account.provider)
        provider = provider_class(
            access_token=security_utils.decrypt_token(storage_account.access_token),
            refresh_token=security_utils.decrypt_token(storage_account.refresh_token) if storage_account.refresh_token else None,
            mode=storage_account.mode # Pass the mode to the provider instance
        )
        
        preview_url = await provider.get_preview_link(file_metadata.provider_file_id)
        
        # Update file metadata with preview link
        file_metadata.preview_link = preview_url
        db.commit()
        
        return {"preview_url": preview_url}
    
    except Exception as e:
        logger.error(f"Failed to get preview link: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate preview link")

# Statistics endpoint
@app.get("/api/stats", response_model=schemas.StatsResponse)
async def get_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user statistics"""
    total_files = db.query(FileMetadata).filter(FileMetadata.user_id == current_user.id).count()
    total_size = db.query(func.sum(FileMetadata.size)).filter(FileMetadata.user_id == current_user.id).scalar() or 0
    
    provider_stats = db.query(
        StorageAccount.provider,
        func.count(FileMetadata.id).label("file_count"),
        func.sum(FileMetadata.size).label("total_size")
    ).join(FileMetadata).filter(
        StorageAccount.user_id == current_user.id
    ).group_by(StorageAccount.provider).all()
    
    duplicate_count = db.query(FileMetadata.content_hash).filter(
        and_(
            FileMetadata.user_id == current_user.id,
            FileMetadata.content_hash.isnot(None)
        )
    ).group_by(FileMetadata.content_hash).having(func.count(FileMetadata.id) > 1).count()
    
    # Compute file type distribution
    file_type_distribution_raw = db.query(
        func.lower(FileMetadata.file_extension),
        func.count(FileMetadata.id)
    ).filter(
        FileMetadata.user_id == current_user.id,
        FileMetadata.is_active == True
    ).group_by(func.lower(FileMetadata.file_extension)).all()

    file_type_distribution = defaultdict(int)
    for ext, count in file_type_distribution_raw:
        if ext:
            # Group common extensions into broader categories if desired
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                file_type_distribution["images"] += count
            elif ext in ['.mp4', '.avi', '.mov']:
                file_type_distribution["videos"] += count
            elif ext in ['.pdf', '.doc', '.docx', '.txt']:
                file_type_distribution["documents"] += count
            else:
                file_type_distribution["other"] += count
        else:
            file_type_distribution["unknown"] += count

    return schemas.StatsResponse(
        total_files=total_files,
        total_size=total_size,
        total_size_formatted=file_utils.format_file_size(total_size),
        provider_stats=[
            schemas.ProviderStats(
                provider=stat[0],
                file_count=stat[1],
                total_size=stat[2] or 0,
                total_size_formatted=file_utils.format_file_size(stat[2] or 0)
            ).model_dump() for stat in provider_stats # Use model_dump for ProviderStats
        ],
        duplicate_groups=duplicate_count,
        file_type_distribution=file_type_distribution
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        # Removed: reload=True,
        # Removed: reload_dirs=["backend"]
    )
