from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import hashlib
from backend.database import Base

class User(Base):
    """User model for managing user accounts"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    name = Column(String(100))
    hashed_password = Column(String(128), nullable=False) # New column for hashed password
    mode = Column(String(20), default="full_access", nullable=False) # 'metadata' or 'full_access'
    is_2fa_enabled = Column(Boolean, default=False)
    otp_secret = Column(String(32), nullable=True) # For TOTP/HOTP secrets
    otp_verified_at = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, default=datetime.utcnow)
    password_changed_at = Column(DateTime, nullable=True) # New: Track last password change
    last_mode_change_at = Column(DateTime, default=datetime.utcnow)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    storage_accounts = relationship("StorageAccount", back_populates="user", cascade="all, delete-orphan")
    files = relationship("FileMetadata", back_populates="user", cascade="all, delete-orphan")
    sync_logs = relationship("SyncLog", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    trusted_devices = relationship("TrustedDevice", back_populates="user", cascade="all, delete-orphan") # New relationship
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan") # Add to User model relationship
    preferences = relationship("UserPreferences", back_populates="user", uselist=False) # New relationship

    def __repr__(self):
        return f"<User(email='{self.email}')>"

class StorageAccount(Base):
    """Storage account model for managing cloud storage connections"""
    __tablename__ = "storage_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # 'google_drive', 'google_photos', 'dropbox', 'onedrive', 'terabox'
    mode = Column(String(20), default="full_access", nullable=False) # 'metadata-only', 'read-write'
    account_email = Column(String(120), nullable=False)
    account_name = Column(String(200), nullable=True) # For display purposes
    access_token = Column(Text, nullable=False)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted
    token_expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    storage_used = Column(BigInteger, default=0) # New: Track storage used
    storage_limit = Column(BigInteger, default=0) # New: Track storage limit
    
    # Relationships
    user = relationship("User", back_populates="storage_accounts")
    files = relationship("FileMetadata", back_populates="storage_account", cascade="all, delete-orphan")
    sync_logs = relationship("SyncLog", back_populates="storage_account", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_provider', 'user_id', 'provider', 'mode'),
        Index('idx_provider_email', 'provider', 'account_email'),
    )

    def __repr__(self):
        return f"<StorageAccount(user_id={self.user_id}, provider='{self.provider}', email='{self.account_email}')>"

class FileMetadata(Base):
    """File metadata model for storing file information from all providers"""
    __tablename__ = "file_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    storage_account_id = Column(Integer, ForeignKey("storage_accounts.id"), nullable=False)
    
    # File identification
    provider_file_id = Column(String(255), nullable=False)
    name = Column(String(500), nullable=False)
    path = Column(Text)  # Full path in the cloud storage
    
    # File metadata
    size = Column(BigInteger)  # Size in bytes
    mime_type = Column(String(100))
    file_extension = Column(String(10))
    is_folder = Column(Boolean, default=False) # New: Added to distinguish files from folders
    
    # Timestamps
    created_at_source = Column(DateTime)  # When file was created in cloud storage
    modified_at_source = Column(DateTime)  # When file was last modified in cloud storage
    created_at = Column(DateTime, default=datetime.utcnow)  # When record was created in our DB
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Preview and access
    preview_link = Column(Text)  # Link for previewing file
    download_link = Column(Text)  # Direct download link (if available)
    web_view_link = Column(Text)  # Web view link
    thumbnail_link = Column(Text)  # Thumbnail preview link
    
    # Duplicate detection
    content_hash = Column(String(64))  # MD5 or SHA-256 hash when available
    size_hash = Column(String(64))  # Hash based on size + name for basic duplicate detection
    is_duplicate = Column(Boolean, default=False)
    original_file_id = Column(Integer, ForeignKey("file_metadata.id"))
    
    # File type classification
    is_image = Column(Boolean, default=False)
    is_video = Column(Boolean, default=False)
    is_document = Column(Boolean, default=False)
    
    # New field to track active status
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="files")
    storage_account = relationship("StorageAccount", back_populates="files")
    duplicates = relationship("FileMetadata", backref="original_file", remote_side=[id])
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_files', 'user_id'),
        Index('idx_storage_files', 'storage_account_id'),
        Index('idx_content_hash', 'content_hash'),
        Index('idx_size_hash', 'size_hash'),
        Index('idx_provider_file', 'storage_account_id', 'provider_file_id'),
        Index('idx_file_name', 'name'),
        Index('idx_file_extension', 'file_extension'),
        Index('idx_modified_date', 'modified_at_source'),
    )
    
    def generate_size_hash(self):
        """Generate a hash based on file size and name for basic duplicate detection"""
        if self.size and self.name:
            hash_string = f"{self.name.lower()}_{self.size}_{self.mime_type or ''}"
            return hashlib.md5(hash_string.encode()).hexdigest()
        return None
    
    def classify_file_type(self):
        """Classify file type based on mime type"""
        if self.mime_type:
            if self.mime_type.startswith('image/'):
                self.is_image = True
            elif self.mime_type.startswith('video/'):
                self.is_video = True
            elif self.mime_type in ['application/pdf', 'application/msword', 
                                   'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                   'text/plain', 'text/csv']:
                self.is_document = True

class SyncLog(Base):
    """Log model for tracking sync operations"""
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    storage_account_id = Column(Integer, ForeignKey("storage_accounts.id"), nullable=False)
    
    sync_started_at = Column(DateTime, default=datetime.utcnow)
    sync_completed_at = Column(DateTime)
    files_processed = Column(Integer, default=0)
    files_added = Column(Integer, default=0)
    files_updated = Column(Integer, default=0)
    files_deleted = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    error_details = Column(Text)
    status = Column(String(20), default='running')  # 'running', 'completed', 'failed'
    
    # Relationships
    user = relationship("User", back_populates="sync_logs")
    storage_account = relationship("StorageAccount", back_populates="sync_logs")

class UserSession(Base):
    """User session model for managing active sessions"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_sessions', 'user_id'),
        Index('idx_session_expires', 'expires_at'),
    )

    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, expires_at='{self.expires_at}')>"

class TrustedDevice(Base): # New Model
    __tablename__ = "trusted_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_fingerprint = Column(String(255), unique=True, nullable=False, index=True) # A unique identifier for the device
    name = Column(String(100), nullable=True) # e.g., "My Laptop", "Work Phone"
    last_used_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="trusted_devices")

    def __repr__(self):
        return f"<TrustedDevice(user_id={self.user_id}, fingerprint='{self.device_fingerprint}')>"

class Job(Base): # New Model
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False) # e.g., 'migration', 'sync', 'deduplication'
    status = Column(String(20), default="pending", nullable=False) # 'pending', 'in_progress', 'completed', 'failed', 'cancelled'
    progress = Column(Integer, default=0) # Percentage completion (0-100)
    details = Column(Text, nullable=True) # JSON string for job-specific details (e.g., source/destination for migration)
    logs = Column(Text, nullable=True) # JSON string for detailed logs/errors
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="jobs")

    def __repr__(self):
        return f"<Job(user_id={self.user_id}, type='{self.type}', status='{self.status}')>"

class UserPreferences(Base): # New Model
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    preferences = Column(Text, nullable=False, default="{}") # JSON string to store preferences
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id})>"
