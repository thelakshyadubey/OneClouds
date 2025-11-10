"""
Storage providers package initialization and factory
"""

from .google_drive import GoogleDriveProvider
from .google_photos import GooglePhotosProvider
from .onedrive_provider import OneDriveProvider  # Updated import
from .terabox import TeraboxProvider
from .dropbox_provider import DropboxProvider # Changed from .dropbox

# Supported providers registry
SUPPORTED_PROVIDERS = [
    'google_drive',
    'dropbox'
]

# Add optional providers if available
if GooglePhotosProvider:
    SUPPORTED_PROVIDERS.append('google_photos')
if OneDriveProvider:
    SUPPORTED_PROVIDERS.append('onedrive')
if TeraboxProvider:
    SUPPORTED_PROVIDERS.append('terabox')

# Provider class mapping
PROVIDER_CLASSES = {
    'google_drive': GoogleDriveProvider,
    'dropbox': DropboxProvider,
}

if GooglePhotosProvider:
    PROVIDER_CLASSES['google_photos'] = GooglePhotosProvider
if OneDriveProvider:
    PROVIDER_CLASSES['onedrive'] = OneDriveProvider
if TeraboxProvider:
    PROVIDER_CLASSES['terabox'] = TeraboxProvider

def get_provider_class(provider_name: str):
    """Get provider class by name"""
    if provider_name not in PROVIDER_CLASSES:
        raise ValueError(f"Unsupported provider: {provider_name}")
    
    return PROVIDER_CLASSES[provider_name]

def get_storage_provider(provider_name: str, access_token: str, refresh_token: str = None, **kwargs):
    """Factory method to create storage provider instance"""
    provider_class = get_provider_class(provider_name)
    return provider_class(
        access_token=access_token,
        refresh_token=refresh_token,
        **kwargs
    )

def is_provider_supported(provider_name: str) -> bool:
    """Check if provider is supported"""
    return provider_name in SUPPORTED_PROVIDERS

def get_all_providers():
    """Get all supported provider names"""
    return SUPPORTED_PROVIDERS.copy()

__all__ = [
    'CloudStorageProvider',
    'GoogleDriveProvider',
    'DropboxProvider',
    'get_provider_class',
    'get_storage_provider',
    'is_provider_supported',
    'get_all_providers',
    'SUPPORTED_PROVIDERS'
]
