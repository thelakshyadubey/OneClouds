import os
from typing import Optional
from pydantic import validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Core application settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 90 # New: For "Stay logged in" feature
    
    # Email/OTP settings for 2FA
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "apikey") # SendGrid uses "apikey" as the username
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "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") # <<< IMPORTANT: REPLACE WITH YOUR ACTUAL SENDGRID API KEY (starts with SG.)
    MAIL_FROM: str = os.getenv("MAIL_FROM", "lakshya.dubeyji@gmail.com") # <<< IMPORTANT: Use the email you verified in SendGrid
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "465")) # Changed to 465 for implicit SSL/TLS
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.sendgrid.net") # SendGrid SMTP server
    MAIL_STARTTLS: bool = os.getenv("MAIL_STARTTLS", "false").lower() == "true" # Set to false for implicit SSL/TLS
    MAIL_SSL_TLS: bool = os.getenv("MAIL_SSL_TLS", "true").lower() == "true" # Set to true for implicit SSL/TLS
    OTP_LENGTH: int = int(os.getenv("OTP_LENGTH", "6"))
    OTP_TTL_MINUTES: int = int(os.getenv("OTP_TTL_MINUTES", "10"))
    OTP_RATE_LIMIT_SECONDS: int = int(os.getenv("OTP_RATE_LIMIT_SECONDS", "60")) # Time before user can request another OTP
    
    # 2FA Lockout settings
    FAILED_LOGIN_ATTEMPTS_LIMIT: int = int(os.getenv("FAILED_LOGIN_ATTEMPTS_LIMIT", "5"))
    LOGIN_LOCKOUT_MINUTES: int = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))
    
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./unified_storage.db")
    
    # Application URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000") # New: Comma-separated list of allowed origins
    
    # Google Drive API Configuration (Full Access - renamed from GOOGLE_DRIVE_FULL_ACCESS to GOOGLE_DRIVE_RW)
    GOOGLE_DRIVE_RW_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_DRIVE_RW_CLIENT_ID")
    GOOGLE_DRIVE_RW_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_DRIVE_RW_CLIENT_SECRET")
    GOOGLE_DRIVE_RW_REDIRECT_URI: str = os.getenv("GOOGLE_DRIVE_RW_REDIRECT_URI", f"{BACKEND_URL}/api/auth/google_drive/readwrite-callback")

    # Google Drive API Configuration (Metadata Only - keep existing for other modes)
    GOOGLE_DRIVE_METADATA_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_DRIVE_METADATA_CLIENT_ID")
    GOOGLE_DRIVE_METADATA_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_DRIVE_METADATA_CLIENT_SECRET")
    GOOGLE_DRIVE_METADATA_REDIRECT_URI: str = os.getenv("GOOGLE_DRIVE_METADATA_REDIRECT_URI", f"{BACKEND_URL}/api/auth/google_drive/metadata-callback")
    
    # Dropbox Configuration (Full Access - renamed from DROPBOX_FULL_ACCESS to DROPBOX_RW)
    DROPBOX_RW_CLIENT_ID: Optional[str] = os.getenv("DROPBOX_RW_CLIENT_ID")
    DROPBOX_RW_CLIENT_SECRET: Optional[str] = os.getenv("DROPBOX_RW_CLIENT_SECRET")
    DROPBOX_RW_REDIRECT_URI: str = os.getenv("DROPBOX_RW_REDIRECT_URI", f"{BACKEND_URL}/api/auth/dropbox/readwrite-callback")

    # Dropbox Configuration (Metadata Only)
    DROPBOX_METADATA_CLIENT_ID: Optional[str] = os.getenv("DROPBOX_METADATA_CLIENT_ID")
    DROPBOX_METADATA_CLIENT_SECRET: Optional[str] = os.getenv("DROPBOX_METADATA_CLIENT_SECRET")
    DROPBOX_METADATA_REDIRECT_URI: str = os.getenv("DROPBOX_METADATA_REDIRECT_URI", f"{BACKEND_URL}/api/auth/dropbox/metadata-callback")
    
    # Microsoft OneDrive Configuration (Full Access)
    ONEDRIVE_FULL_ACCESS_CLIENT_ID: Optional[str] = os.getenv("ONEDRIVE_FULL_ACCESS_CLIENT_ID")
    ONEDRIVE_FULL_ACCESS_CLIENT_SECRET: Optional[str] = os.getenv("ONEDRIVE_FULL_ACCESS_CLIENT_SECRET")
    ONEDRIVE_FULL_ACCESS_REDIRECT_URI: str = os.getenv("ONEDRIVE_FULL_ACCESS_REDIRECT_URI", f"{BACKEND_URL}/api/auth/onedrive/readwrite-callback")

    # Microsoft OneDrive Configuration (Metadata Only)
    ONEDRIVE_METADATA_CLIENT_ID: Optional[str] = os.getenv("ONEDRIVE_METADATA_CLIENT_ID")
    ONEDRIVE_METADATA_CLIENT_SECRET: Optional[str] = os.getenv("ONEDRIVE_METADATA_CLIENT_SECRET")
    ONEDRIVE_METADATA_REDIRECT_URI: str = os.getenv("ONEDRIVE_METADATA_REDIRECT_URI", f"{BACKEND_URL}/api/auth/onedrive/metadata-callback")
    
    # Google Photos API Configuration (assuming read-only for now, can be split later if needed)
    GOOGLE_PHOTOS_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_PHOTOS_CLIENT_ID")
    GOOGLE_PHOTOS_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_PHOTOS_CLIENT_SECRET")
    GOOGLE_PHOTOS_REDIRECT_URI: str = os.getenv("GOOGLE_PHOTOS_REDIRECT_URI", f"{BACKEND_URL}/api/auth/google_photos/callback")
    
    # Terabox Configuration (assuming read-write for now, can be split later if needed)
    TERABOX_CLIENT_ID: Optional[str] = os.getenv("TERABOX_CLIENT_ID")
    TERABOX_CLIENT_SECRET: Optional[str] = os.getenv("TERABOX_CLIENT_SECRET")
    TERABOX_REDIRECT_URI: str = os.getenv("TERABOX_REDIRECT_URI", f"{BACKEND_URL}/api/auth/terabox/callback")
    
    # Security settings
    # IMPORTANT: Override this in .env for production. Must be exactly 44 characters.
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "dGVzdEVuY3J5cHRpb25LZXlGb3JGZXJuZXRUZXN0aW5nMTIzNA==")
    SESSION_COOKIE_SECURE: bool = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    
    # File processing
    MAX_FILES_PER_SYNC: int = int(os.getenv("MAX_FILES_PER_SYNC", "1000"))
    SYNC_INTERVAL_MINUTES: int = int(os.getenv("SYNC_INTERVAL_MINUTES", "30"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))
    
    # Redis configuration (for caching and background tasks)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Development/Production flags
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    TESTING: bool = os.getenv("TESTING", "false").lower() == "true"
    
    # Validator for SECRET_KEY, ENCRYPTION_KEY, etc.
    @validator("SECRET_KEY")
    def secret_key_must_be_strong(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("ENCRYPTION_KEY")
    def encryption_key_must_be_44_chars(cls, v):
        if len(v) != 44:
            raise ValueError(f"ENCRYPTION_KEY must be exactly 44 characters long for Fernet encryption. Got {len(v)} characters.")
        return v
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = 'ignore' # Allow extra environment variables

# Global settings instance
settings = Settings()

# Provider configurations
PROVIDER_CONFIGS = {
    "google_drive_full_access": {
        "client_id": settings.GOOGLE_DRIVE_RW_CLIENT_ID,
        "client_secret": settings.GOOGLE_DRIVE_RW_CLIENT_SECRET,
        "redirect_uri": f"{settings.BACKEND_URL}/api/auth/google_drive/readwrite-callback",
        "scopes": [
            "https://www.googleapis.com/auth/drive", # Full drive access
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        "authorization_base_url": "https://accounts.google.com/o/oauth2/auth",
        "token_url": "https://oauth2.googleapis.com/token"
    },
    "google_drive_metadata": {
        "client_id": settings.GOOGLE_DRIVE_METADATA_CLIENT_ID,
        "client_secret": settings.GOOGLE_DRIVE_METADATA_CLIENT_SECRET,
        "redirect_uri": f"{settings.BACKEND_URL}/api/auth/google_drive/metadata-callback",
        "scopes": [
            "https://www.googleapis.com/auth/drive.metadata.readonly",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        "authorization_base_url": "https://accounts.google.com/o/oauth2/auth",
        "token_url": "https://oauth2.googleapis.com/token"
    },
    "google_drive_metadata_only": {  # Added alias for consistency
        "client_id": settings.GOOGLE_DRIVE_METADATA_CLIENT_ID,
        "client_secret": settings.GOOGLE_DRIVE_METADATA_CLIENT_SECRET,
        "redirect_uri": f"{settings.BACKEND_URL}/api/auth/google_drive/metadata-callback",
        "scopes": [
            "https://www.googleapis.com/auth/drive.metadata.readonly",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        "authorization_base_url": "https://accounts.google.com/o/oauth2/auth",
        "token_url": "https://oauth2.googleapis.com/token"
    },
    "dropbox_full_access": {
        "client_id": settings.DROPBOX_RW_CLIENT_ID,
        "client_secret": settings.DROPBOX_RW_CLIENT_SECRET,
        "redirect_uri": f"{settings.BACKEND_URL}/api/auth/dropbox/readwrite-callback",
        "scopes": [
            "files.content.read",
            "files.content.write",
            "account_info.read",
            "files.metadata.read",
            "files.metadata.write"
        ],
        "authorization_base_url": "https://www.dropbox.com/oauth2/authorize",
        "token_url": "https://api.dropboxapi.com/oauth2/token"
    },
    "dropbox_metadata_only": {
        "client_id": settings.DROPBOX_METADATA_CLIENT_ID,
        "client_secret": settings.DROPBOX_METADATA_CLIENT_SECRET,
        "redirect_uri": f"{settings.BACKEND_URL}/api/auth/dropbox/metadata-callback",
        "scopes": [
            "files.metadata.read",
            "account_info.read"
        ],
        "authorization_base_url": "https://www.dropbox.com/oauth2/authorize",
        "token_url": "https://api.dropboxapi.com/oauth2/token"
    },
    "onedrive_full_access": {
        "client_id": settings.ONEDRIVE_FULL_ACCESS_CLIENT_ID,
        "client_secret": settings.ONEDRIVE_FULL_ACCESS_CLIENT_SECRET,
        "redirect_uri": f"{settings.BACKEND_URL}/api/auth/onedrive/readwrite-callback",
        "scopes": [
            "User.Read",
            "Files.ReadWrite.All",
            "offline_access"
        ],
        "authorization_base_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    },
    "onedrive_metadata_only": {
        "client_id": settings.ONEDRIVE_METADATA_CLIENT_ID,
        "client_secret": settings.ONEDRIVE_METADATA_CLIENT_SECRET,
        "redirect_uri": f"{settings.BACKEND_URL}/api/auth/onedrive/metadata-callback",
        "scopes": [
            "User.Read",
            "Files.Read", # Files.Read generally gives content access, but we'll enforce metadata-only via code.
            "offline_access"
        ],
        "authorization_base_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    },
    "google_photos": { # Keep as is for now, assuming read-only
        "client_id": settings.GOOGLE_PHOTOS_CLIENT_ID,
        "client_secret": settings.GOOGLE_PHOTOS_CLIENT_SECRET,
        "redirect_uri": f"{settings.BACKEND_URL}/api/auth/google_photos/callback",
        "scopes": ["https://www.googleapis.com/auth/photoslibrary.readonly"],
        "authorization_base_url": "https://accounts.google.com/o/oauth2/auth",
        "token_url": "https://oauth2.googleapis.com/token"
    },
    "terabox": { # Keep as is for now, assuming read-write
        "client_id": settings.TERABOX_CLIENT_ID,
        "client_secret": settings.TERABOX_CLIENT_SECRET,
        "redirect_uri": f"{settings.BACKEND_URL}/api/auth/terabox/callback",
        "authorization_base_url": "https://openapi.terabox.com/oauth/authorize",
        "token_url": "https://openapi.terabox.com/oauth/token"
    }
}