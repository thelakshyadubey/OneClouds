"""
Pydantic schemas for API request/response models
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, EmailStr, validator
from fastapi import UploadFile
# from backend.models import UserPreferences # Import UserPreferences

# Base schemas
class BaseResponse(BaseModel):
    class Config:
        from_attributes = True

# Settings and preferences schemas
class UserPreferences(BaseModel):
    theme: str = "light"
    default_view: str = "grid"  # 'grid', 'list'
    files_per_page: int = 50
    auto_sync_enabled: bool = True
    sync_interval_minutes: int = 30
    show_thumbnails: bool = True
    default_upload_location: str = "__root__" # New: Default upload location

class UserPreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    default_view: Optional[str] = None
    files_per_page: Optional[int] = None
    auto_sync_enabled: Optional[bool] = None
    sync_interval_minutes: Optional[int] = None
    show_thumbnails: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    language: Optional[str] = None
    default_upload_location: Optional[str] = None # New: Default upload location

class UserPreferencesResponse(BaseResponse):
    id: int
    user_id: int
    preferences: UserPreferences
    updated_at: datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserRegister(UserBase):
    password: str
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('passwords do not match')
        return v

class OTPVerification(BaseModel):
    email: EmailStr
    otp: str
    device_fingerprint: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    device_fingerprint: Optional[str] = None

class UserEmailUpdate(BaseModel):
    new_email: EmailStr
    current_password: str

class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str

    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v

class TwoFactorAuthSetup(BaseModel):
    password: str

class TwoFactorAuthVerify(BaseModel):
    otp: str

class UserResponse(BaseResponse):
    class Config(BaseResponse.Config):
        arbitrary_types_allowed = True
    id: int
    email: str
    name: Optional[str] = None
    created_at: datetime
    storage_accounts_count: int
    total_files_count: int
    mode: str
    is_2fa_enabled: bool
    is_active: bool
    last_login_at: Optional[datetime] = None
    preferences: Optional[UserPreferences] = None

class RevokeAllSessions(BaseModel):
    current_password: str

class UserDeleteAccount(BaseModel):
    current_password: str

# Password reset and email verification schemas
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class VerifyEmailRequest(BaseModel):
    token: str

# Storage Account schemas
class StorageAccountBase(BaseModel):
    provider: str
    account_email: str
    account_name: Optional[str] = None
    mode: str

class StorageAccountResponse(BaseResponse):
    id: int
    provider: str
    account_email: str
    account_name: Optional[str] = None
    is_active: bool
    last_sync: Optional[datetime] = None
    created_at: datetime
    files_count: int
    storage_used: int = 0
    storage_limit: int = 0
    mode: str

# File metadata schemas
class FileMetadataBase(BaseModel):
    name: str
    path: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    file_extension: Optional[str] = None

class FileMetadataResponse(BaseResponse):
    id: int
    provider: str
    provider_file_id: str
    name: str
    path: Optional[str] = None
    size: Optional[int] = None
    size_formatted: Optional[str] = None
    mime_type: Optional[str] = None
    file_extension: Optional[str] = None
    created_at_source: Optional[datetime] = None
    modified_at_source: Optional[datetime] = None
    preview_link: Optional[str] = None
    download_link: Optional[str] = None
    web_view_link: Optional[str] = None
    thumbnail_link: Optional[str] = None
    is_duplicate: bool = False
    is_image: bool = False
    is_video: bool = False
    is_document: bool = False
    storage_account: Optional[Dict[str, Any]] = None

class FileListResponse(BaseModel):
    files: List[FileMetadataResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class FileSearchRequest(BaseModel):
    query: Optional[str] = None
    provider: Optional[str] = None
    file_type: Optional[str] = None  # 'image', 'video', 'document', 'other'
    size_min: Optional[int] = None
    size_max: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = "modified_at_source"
    sort_order: str = "desc"
    page: int = 1
    per_page: int = 50

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be either "asc" or "desc"')
        return v

    @validator('file_type')
    def validate_file_type(cls, v):
        if v and v not in ['image', 'video', 'document', 'other']:
            raise ValueError('file_type must be one of: image, video, document, other')
        return v

# Duplicate files schemas
class DuplicateGroupResponse(BaseModel):
    hash: str
    count: int
    files: List[FileMetadataResponse]

class RemoveDuplicatesRequest(BaseModel):
    file_ids: List[int]
    keep_strategy: str = "newest"  # 'newest', 'oldest', 'largest', 'smallest'

    @validator('keep_strategy')
    def validate_keep_strategy(cls, v):
        if v not in ['newest', 'oldest', 'largest', 'smallest']:
            raise ValueError('keep_strategy must be one of: newest, oldest, largest, smallest')
        return v

# File upload schemas
class FileUploadRequest(BaseModel):
    provider: str
    folder_path: str = "/"
    overwrite: bool = False

class FileUploadResponse(BaseModel):
    message: str
    file: FileMetadataResponse

# Sync schemas
class SyncLogResponse(BaseResponse):
    id: int
    storage_account_id: int
    sync_started_at: datetime
    sync_completed_at: Optional[datetime] = None
    files_processed: int = 0
    files_added: int = 0
    files_updated: int = 0
    files_deleted: int = 0
    errors_count: int = 0
    status: str

class SyncStatusResponse(BaseModel):
    message: str
    account_id: int
    sync_log: Optional[SyncLogResponse] = None

# Statistics schemas
class ProviderStats(BaseModel):
    provider: str
    file_count: int
    total_size: int
    total_size_formatted: str

class StatsResponse(BaseModel):
    total_files: int
    total_size: int
    total_size_formatted: str
    provider_stats: List[Dict[str, Any]]
    duplicate_groups: int
    file_type_distribution: Dict[str, int]

# Authentication schemas
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: int
    email: str
    expires_in: int
    requires_2fa: bool = False
    device_trusted: bool = False

class TrustedDeviceResponse(BaseResponse):
    id: int
    device_fingerprint: str
    name: Optional[str] = None
    last_used_at: datetime
    created_at: datetime
    is_active: bool

class ModeUpdate(BaseModel):
    mode: str

    @validator('mode')
    def validate_mode(cls, v):
        if v not in ['metadata', 'full_access']:
            raise ValueError("Mode must be 'metadata' or 'full_access'")
        return v

class GenericResponse(BaseModel):
    message: str

class JobResponse(BaseResponse):
    id: int
    type: str
    status: str
    progress: int
    details: Optional[Dict[str, Any]] = None
    logs: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

class AuthStatusResponse(BaseModel):
    is_authenticated: bool
    user: Optional[UserResponse] = None
    connected_providers: List[str] = []

# Error schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

class ValidationErrorResponse(BaseModel):
    detail: List[Dict[str, Any]]
    error_code: str = "VALIDATION_ERROR"

# Bulk operations schemas
class BulkDeleteRequest(BaseModel):
    file_ids: List[int]

class BulkDeleteResponse(BaseModel):
    message: str
    deleted_count: int
    failed_count: int
    errors: List[str] = []

class BulkMoveRequest(BaseModel):
    file_ids: List[int]
    destination_provider: str
    destination_folder: str = "/"

class BulkMoveResponse(BaseModel):
    message: str
    moved_count: int
    failed_count: int
    errors: List[str] = []

# Preview schemas
class FilePreviewResponse(BaseModel):
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    web_view_url: Optional[str] = None
    preview_type: str  # 'image', 'video', 'document', 'embed', 'download'
    supports_inline_preview: bool = False

# Activity and audit schemas
class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    action: str  # 'upload', 'delete', 'sync', 'preview', 'download'
    resource_type: str  # 'file', 'storage_account', 'user'
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

# Webhook and notification schemas
class WebhookEvent(BaseModel):
    event_type: str  # 'file_added', 'file_deleted', 'sync_completed', 'sync_failed'
    user_id: int
    data: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()

# System health schemas
class HealthCheckResponse(BaseModel):
    status: str  # 'healthy', 'degraded', 'unhealthy'
    timestamp: datetime
    version: str
    database_status: str
    redis_status: Optional[str] = None
    external_apis: Dict[str, str]  # provider -> status

class FileCopyRequest(BaseModel):
    to_account_id: int
    to_parent_id: Optional[str] = None
    conflict_strategy: str = "keep_both"

    @validator('conflict_strategy')
    def validate_conflict_strategy(cls, v):
        if v not in ['keep_both', 'skip', 'overwrite']:
            raise ValueError("Conflict strategy must be 'keep_both', 'skip', or 'overwrite'")
        return v

class MigrateRequest(BaseModel):
    items: List[Dict[str, Any]]  # List of {'provider', 'accountId', 'fileId', 'is_folder'}
    to_account_id: int
    to_parent_id: Optional[str] = None
    conflict_strategy: str = "keep_both"

    @validator('conflict_strategy')
    def validate_conflict_strategy(cls, v):
        if v not in ['keep_both', 'skip', 'overwrite']:
            raise ValueError("Conflict strategy must be 'keep_both', 'skip', or 'overwrite'")
        return v

class MigrateResponse(BaseModel):
    job_id: int
    message: str
