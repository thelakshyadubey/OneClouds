from abc import ABC, abstractmethod
from datetime import datetime
import requests
from typing import List, Dict, Any, Optional
import time
import httpx
from httpx import HTTPStatusError

class RateLimiter:
    """Simple rate limiter to handle API rate limits"""
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests = []
    
    def wait_if_needed(self):
        """Wait if we've hit the rate limit"""
        now = time.time()
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests if now - req_time < 60]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = 60 - (now - self.requests[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.requests.append(now)

class CloudStorageProvider(ABC):
    """Abstract base class for cloud storage providers"""
    
    def __init__(self, access_token: str, refresh_token: str = None, mode: str = "read-write"):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.mode = mode
        self.rate_limiter = RateLimiter()
    
    @staticmethod
    @abstractmethod
    def get_authorization_url(client_id: str, redirect_uri: str, state: str, scopes: List[str], authorization_base_url: str) -> str:
        """Generate the authorization URL for the provider"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name"""
        pass
    
    @abstractmethod
    async def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        pass

    @abstractmethod
    async def update_db_tokens(self, access_token: str, refresh_token: Optional[str], expires_in: int) -> None:
        """Update the access and refresh tokens in the database."""
        pass
    
    @abstractmethod
    async def get_user_info(self) -> Dict[str, Any]:
        """Get user information"""
        pass
    
    @abstractmethod
    async def list_files(self, page_token: str = None, max_results: int = 100) -> Dict[str, Any]:
        """
        List files from the provider
        Returns: {
            'files': [list of file metadata],
            'next_page_token': str or None
        }
        """
        pass
    
    @abstractmethod
    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a specific file"""
        pass
    
    def normalize_file_metadata(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize file metadata to a common format
        Override in subclasses for provider-specific formatting
        """
        return {
            'provider_file_id': raw_metadata.get('id'),
            'name': raw_metadata.get('name'),
            'path': raw_metadata.get('path'),
            'size': raw_metadata.get('size'),
            'mime_type': raw_metadata.get('mimeType'),
            'created_at': self.parse_datetime(raw_metadata.get('createdTime')),
            'modified_at': self.parse_datetime(raw_metadata.get('modifiedTime')),
            'preview_link': raw_metadata.get('webViewLink'),
            'download_link': raw_metadata.get('downloadUrl'),
            'web_view_link': raw_metadata.get('webViewLink')
        }
    
    def parse_datetime(self, date_string: str) -> Optional[datetime]:
        """Parse datetime string from provider API"""
        if not date_string:
            return None
        
        # Common datetime formats from different providers
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        return None
    
    async def make_request(self, method: str, url: str, headers: Dict = None, params: Dict = None, json: Dict = None) -> httpx.Response:
        """Make HTTP request with rate limiting and error handling"""
        self.rate_limiter.wait_if_needed()
        
        default_headers = {'Authorization': f'Bearer {self.access_token}'}
        if headers:
            default_headers.update(headers)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=default_headers,
                    params=params,
                    json=json,
                    timeout=30
                )

                if response.status_code == 401:
                    if self.refresh_token:
                        # Attempt to refresh token
                        if await self.refresh_access_token():
                            # Token refreshed, persist to DB and retry request
                            # We need to get expires_in from refresh_access_token or derive it
                            # For now, we'll assume a default expiry of 1 hour if not provided by the refresh call.
                            await self.update_db_tokens(self.access_token, self.refresh_token, 3600) # Assume 1 hour for now
                            default_headers['Authorization'] = f'Bearer {self.access_token}'
                            async with httpx.AsyncClient() as client:
                                response = await client.request(
                                    method=method,
                                    url=url,
                                    headers=default_headers,
                                    params=params,
                                    json=json,
                                    timeout=30
                                )
                                if response.status_code == 401:
                                    raise Exception("Refreshed token is still unauthorized.")
                        else:
                            raise Exception("Failed to refresh access token.")
                    else:
                        raise Exception("Access token unauthorized and no refresh token available.")

            return response
            
        except HTTPStatusError as e:
            raise Exception(f"Request failed with status {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def get_file_extension(self, filename: str, mime_type: str = None) -> str:
        """Extract file extension from filename or mime type"""
        if filename and '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        
        # Fallback to mime type mapping
        mime_extensions = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'application/pdf': 'pdf',
            'text/plain': 'txt',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/vnd.ms-excel': 'xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx'
        }
        
        return mime_extensions.get(mime_type, 'unknown')
