"""
Security utilities and helper functions
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging
import pyotp
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from itsdangerous import URLSafeTimedSerializer
from .config import settings
from .audit_logger import AuditLogger # For audit logging
from backend.models import FileMetadata # NEW: Import FileMetadata

logger = logging.getLogger(__name__)

# Configure FastAPI Mail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS, # Updated from MAIL_TLS
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS, # Updated from MAIL_SSL
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(conf)

class SecurityUtils:
    """Security utilities for encryption and data protection"""
    
    def __init__(self):
        if not settings.ENCRYPTION_KEY:
            logger.error("ENCRYPTION_KEY is not set in settings. Tokens cannot be securely encrypted/decrypted.")
            raise ValueError("ENCRYPTION_KEY is not set.")
        # Direct use of ENCRYPTION_KEY for Fernet, it must be 44 URL-safe base64-encoded bytes.
        print(f"DEBUG: ENCRYPTION_KEY value: {settings.ENCRYPTION_KEY}, length: {len(settings.ENCRYPTION_KEY or '')}")
        self.cipher_suite = Fernet(settings.ENCRYPTION_KEY.encode())
        self.login_rate_limiter = RateLimiter() # Initialize RateLimiter here
    
    def generate_otp_secret(self) -> str:
        """Generate a base32 encoded secret for OTP."""
        return pyotp.random_base32()

    def generate_otp_uri(self, email: str, secret: str) -> str:
        """Generate a Google Authenticator compatible OTP URI."""
        # Issuer name can be configured in settings if needed
        return pyotp.totp.TOTP(secret).provisioning_uri(email, issuer_name="OneClouds")

    def generate_otp(self, secret: str) -> str:
        """Generate an OTP using the provided secret."""
        totp = pyotp.TOTP(secret, interval=settings.OTP_TTL_MINUTES * 60, digits=settings.OTP_LENGTH)
        return totp.now()

    def verify_otp(self, secret: str, otp: str) -> bool:
        """Verifies a TOTP code."""
        totp = pyotp.TOTP(secret, interval=settings.OTP_TTL_MINUTES * 60, digits=settings.OTP_LENGTH) # OTP valid for OTP_TTL_MINUTES
        is_valid = totp.verify(otp, valid_window=1) # Add valid_window for time skew tolerance
        logger.info(f"DEBUG: pyotp verification - Secret: {secret}, OTP: {otp}, Is valid: {is_valid}")
        return is_valid

    async def send_email(self, recipient: str, subject: str, body: str):
        """Send an email."""
        message = MessageSchema(recipients=[recipient], subject=subject, body=body, subtype="html")
        try:
            await fm.send_message(message)
            logger.info(f"Email sent successfully to {recipient} with subject: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            raise

    async def send_otp_email(self, recipient: str, otp: str):
        """Send an email containing the OTP."""
        subject = "Your OneClouds Verification Code"
        body = f"""
        <html>
            <body>
                <p>Hello,</p>
                <p>Your OneClouds verification code is: <strong>{otp}</strong></p>
                <p>This code is valid for {settings.OTP_TTL_MINUTES} minutes. Do not share this code with anyone.</p>
                <p>If you did not request this, please ignore this email.</p>
                <p>Thanks,</p>
                <p>The OneClouds Team</p>
            </body>
        </html>
        """
        await self.send_email(recipient, subject, body)

    def generate_device_fingerprint(self, user_agent: Optional[str], ip_address: Optional[str]) -> str:
        """Generates a basic device fingerprint from user-agent and IP address.
        In a real-world scenario, this would be more sophisticated, potentially involving client-side JS.
        """
        raw_fingerprint = f"{user_agent or ''}-{ip_address or ''}"
        return hashlib.sha256(raw_fingerprint.encode()).hexdigest()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed using the internal login rate limiter."""
        return self.login_rate_limiter.is_allowed(key, max_requests, window_seconds)

    def increment_failed_login_attempts(self, db: Any, user: Optional[Any], ip_address: str):
        """Increments failed login attempts for a user or tracks by IP if user is None.
        This needs to be in SecurityUtils to avoid circular dependencies with main.py.
        """
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.FAILED_LOGIN_ATTEMPTS_LIMIT:
                user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
                user.failed_login_attempts = 0
            db.commit()
        else:
            # If user is None (e.g., non-existent email), track failed attempts by IP
            # This uses the RateLimiter class for IP-based lockout if user cannot be identified.
            # We'll use a separate key for IP-based lockout specifically for unknown users.
            rate_limiter = self.login_rate_limiter # Use the instance from __init__
            if not rate_limiter.is_allowed(f"failed_login_ip:{ip_address}", settings.FAILED_LOGIN_ATTEMPTS_LIMIT, settings.LOGIN_LOCKOUT_MINUTES * 60):
                logger.warning(f"Excessive failed login attempts from IP: {ip_address}. Temporary lockout.")

    def encrypt_token(self, token: str) -> str:
        """Encrypt a token for secure storage"""
        try:
            if not token:
                logger.warning("Attempted to encrypt an empty token.")
                return ""
            encrypted_token = self.cipher_suite.encrypt(token.encode())
            logger.debug("Token encrypted successfully.")
            return base64.urlsafe_b64encode(encrypted_token).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt token: {e}", exc_info=True)
            raise
    
    def decrypt_token(self, encrypted_token: str) -> Optional[str]:
        """Decrypt a token"""
        try:
            if not encrypted_token:
                logger.warning("Attempted to decrypt an empty encrypted token.")
                return None
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_token.encode())
            decrypted_token = self.cipher_suite.decrypt(encrypted_bytes)
            logger.debug("Token decrypted successfully.")
            return decrypted_token.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt token: {e}", exc_info=True)
            return None
    
    def generate_secure_filename(self, original_filename: str) -> str:
        """Generate a secure filename"""
        # Get file extension
        name, ext = os.path.splitext(original_filename)
        # Generate secure random name
        secure_name = secrets.token_urlsafe(16)
        return f"{secure_name}{ext}"
    
    def validate_file_type(self, filename: str, allowed_extensions: list = None) -> bool:
        """Validate file type based on extension"""
        if allowed_extensions is None:
            # Default allowed extensions
            allowed_extensions = [
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',  # Images
                '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',  # Videos
                '.pdf', '.doc', '.docx', '.txt', '.rtf',  # Documents
                '.xls', '.xlsx', '.csv', '.ppt', '.pptx',  # Office
                '.zip', '.rar', '.7z', '.tar', '.gz',  # Archives
                '.mp3', '.wav', '.flac', '.aac', '.ogg'  # Audio
            ]
        
        _, ext = os.path.splitext(filename.lower())
        return ext in allowed_extensions
    
    def sanitize_path(self, path: str) -> str:
        """Sanitize file path to prevent directory traversal"""
        # Remove dangerous characters and patterns
        dangerous_patterns = ['../', '..\\', '~/', '~\\']
        sanitized = path
        
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern, '')
        
        # Remove leading slashes and normalize
        sanitized = sanitized.lstrip('/')
        sanitized = os.path.normpath(sanitized)
        
        return sanitized
    
    def hash_file_content(self, content: bytes) -> str:
        """Generate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    def is_safe_redirect_url(self, url: str) -> bool:
        """Check if redirect URL is safe"""
        if not url:
            return False
        
        # Allow only specific domains
        allowed_domains = [
            'localhost',
            '127.0.0.1',
            settings.FRONTEND_URL.replace('http://', '').replace('https://', ''),
        ]
        
        # Simple check - in production, use more robust URL parsing
        for domain in allowed_domains:
            if domain in url:
                return True
        
        return False

class FileUtils:
    """Utilities for file operations and metadata handling"""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if not size_bytes:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    @staticmethod
    def get_file_type_from_mime(mime_type: str) -> str:
        """Get file type category from MIME type"""
        if not mime_type:
            return "other"
        
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type.startswith("audio/"):
            return "audio"
        elif mime_type in [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "text/csv"
        ]:
            return "document"
        else:
            return "other"
    
    @staticmethod
    def create_file_metadata(user_id: int, storage_account_id: int, file_data: Dict[str, Any]) -> FileMetadata:
        """Create FileMetadata instance from provider data"""
        file_metadata = FileMetadata(
            user_id=user_id,
            storage_account_id=storage_account_id,
            provider_file_id=file_data["provider_file_id"],
            name=file_data["name"],
            path=file_data.get("path"),
            size=file_data.get("size"),
            mime_type=file_data.get("mime_type"),
            file_extension=FileUtils.get_file_extension(file_data["name"]),
            created_at_source=file_data.get("created_at"),
            modified_at_source=file_data.get("modified_at"),
            preview_link=file_data.get("preview_link"),
            download_link=file_data.get("download_link"),
            web_view_link=file_data.get("web_view_link"),
            thumbnail_link=file_data.get("thumbnail_link"),
            content_hash=file_data.get("content_hash")
        )
        
        # Generate size hash for duplicate detection
        if file_metadata.name and file_metadata.size:
            file_metadata.size_hash = file_metadata.generate_size_hash()
        
        # Classify file type
        file_metadata.classify_file_type()
        
        return file_metadata
    
    @staticmethod
    def update_file_metadata(existing_file: FileMetadata, file_data: Dict[str, Any]) -> None:
        """Update existing FileMetadata with new data"""
        existing_file.name = file_data["name"]
        existing_file.path = file_data.get("path")
        existing_file.size = file_data.get("size")
        existing_file.mime_type = file_data.get("mime_type")
        existing_file.file_extension = FileUtils.get_file_extension(file_data["name"])
        existing_file.modified_at_source = file_data.get("modified_at")
        existing_file.preview_link = file_data.get("preview_link")
        existing_file.download_link = file_data.get("download_link")
        existing_file.web_view_link = file_data.get("web_view_link")
        existing_file.thumbnail_link = file_data.get("thumbnail_link")
        existing_file.content_hash = file_data.get("content_hash")
        existing_file.updated_at = datetime.utcnow()
        
        # Update size hash if size or name changed
        if existing_file.name and existing_file.size:
            existing_file.size_hash = existing_file.generate_size_hash()
        
        # Update file type classification
        existing_file.classify_file_type()
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Extract file extension from filename"""
        if not filename:
            return ""
        
        _, ext = os.path.splitext(filename.lower())
        return ext.lstrip('.')
    
    @staticmethod
    def file_to_response(file: FileMetadata) -> Dict[str, Any]:
        """Convert FileMetadata to response dict"""
        return {
            "id": file.id,
            "provider": file.storage_account.provider if file.storage_account else None,
            "provider_file_id": file.provider_file_id,
            "name": file.name,
            "path": file.path,
            "size": file.size,
            "size_formatted": FileUtils.format_file_size(file.size) if file.size else "Unknown",
            "mime_type": file.mime_type,
            "file_extension": file.file_extension,
            "created_at_source": file.created_at_source.isoformat() if file.created_at_source else None,
            "modified_at_source": file.modified_at_source.isoformat() if file.modified_at_source else None,
            "preview_link": file.preview_link,
            "download_link": file.download_link,
            "web_view_link": file.web_view_link,
            "thumbnail_link": file.thumbnail_link,
            "is_duplicate": file.is_duplicate,
            "is_image": file.is_image,
            "is_video": file.is_video,
            "is_document": file.is_document,
            "storage_account": {
                "id": file.storage_account.id,
                "provider": file.storage_account.provider,
                "account_email": file.storage_account.account_email,
                "mode": file.storage_account.mode
            } if file.storage_account else None
        }

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        """Check if request is allowed under rate limit"""
        now = datetime.utcnow().timestamp()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [
            timestamp for timestamp in self.requests[key]
            if now - timestamp < window_seconds
        ]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= max_requests:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
