"""
Authentication handler and JWT token management
"""

import jwt
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials # Import HTTPBearer
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

class AuthHandler:
    """Handle authentication-related operations"""

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS # New
        self.oauth2_scheme = HTTPBearer() # Instantiate HTTPBearer here

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt directly (truncate to 72 bytes for bcrypt compatibility)"""
        try:
            # Bcrypt has a 72-byte limit, always truncate to be safe
            password_bytes = password.encode('utf-8')[:72]
            # Generate salt and hash
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash using bcrypt directly (truncate to 72 bytes for bcrypt compatibility)"""
        try:
            # Bcrypt has a 72-byte limit, always truncate to be safe
            password_bytes = plain_password.encode('utf-8')[:72]
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    def create_token(self, data: dict, token_type: str, expires_minutes: Optional[int] = None) -> str:
        """Create a JWT token (access or refresh) with optional custom expiry."""
        to_encode = data.copy()

        if expires_minutes:
            # Use custom expiry time if provided
            expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
        elif token_type == "access":
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        elif token_type == "refresh":
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        else:
            raise ValueError("Invalid token_type. Must be 'access' or 'refresh'.")

        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "sub": token_type})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token, checking its type."""
        try:
            # Ensure the token is a byte string for jwt.decode
            if isinstance(token, str):
                token_bytes = token.encode("utf-8")
            else:
                token_bytes = token

            logger.debug(f"verify_token: Received token string: {token}")
            logger.debug(f"verify_token: token_bytes length: {len(token_bytes)}")
            logger.debug(f"verify_token: token_bytes segment count: {token_bytes.count(b'.')}")
            logger.debug(f"verify_token: Secret Key: {self.secret_key[:5]}...{self.secret_key[-5:]}") # Log partial key for security
            logger.debug(f"verify_token: Algorithm: {self.algorithm}")

            # Validate JWT structure (header.payload.signature)
            if token_bytes.count(b'.') != 2:
                logger.error("Invalid token format: Token must have three segments.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format: Token must have three segments."
                )

            payload = jwt.decode(token_bytes, self.secret_key, algorithms=[self.algorithm])
            logger.debug(f"verify_token: Decoded payload: {payload}")

            # Validate token type from payload
            if payload.get("sub") == token_type:
                return payload
            return None
        except JWTError:
            return None

    def generate_state_token(self) -> str:
        """Generate a secure random state token for OAuth"""
        return secrets.token_urlsafe(32)

# NOTE: The global helper functions `create_access_token`, `verify_token`, `get_password_hash`, `verify_password`
# will be removed and the AuthHandler instance methods will be used directly in main.py for better clarity.
# This is a refactoring step. For now, they are kept but will be deprecated.

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    raise NotImplementedError("Use auth_handler.create_token(..., token_type='access') instead.")

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    raise NotImplementedError("Use auth_handler.verify_token(..., token_type='access') instead.")
