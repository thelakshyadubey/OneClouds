from .base import CloudStorageProvider
from typing import Dict, Any, List, Optional
import httpx
from urllib.parse import urlencode
from datetime import datetime, timedelta

class OneDriveProvider(CloudStorageProvider):
    """Microsoft OneDrive API integration"""

    def __init__(self, access_token: str, refresh_token: str = None, client_id: str = None, client_secret: str = None, mode: str = "read-write"):
        super().__init__(access_token, refresh_token, mode)
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.oauth_authority = "https://login.microsoftonline.com/common"

    def get_provider_name(self) -> str:
        return "onedrive"

    @staticmethod
    def get_authorization_url(client_id: str, redirect_uri: str, state: str, scopes: List[str], authorization_base_url: str) -> str:
        """Generate OneDrive authorization URL."""
        params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ' '.join(scopes),
            'state': state,
            'response_mode': 'query' # Or 'form_post' depending on preference
        }
        
        return f"{authorization_base_url}?{urlencode(params)}"

    @staticmethod
    async def exchange_code_for_token(code: str, client_id: str, client_secret: str, redirect_uri: str, scopes: List[str]) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            'client_id': client_id,
            'scope': ' '.join(scopes),
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
            'client_secret': client_secret
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data=data
                )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"Error exchanging code for OneDrive token: {e}")
            raise Exception("Failed to exchange code for OneDrive token")

    async def refresh_access_token(self) -> bool:
        """Refresh access token using OneDrive OAuth"""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            print("Missing refresh token or client credentials for OneDrive")
            return False
        
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            'client_id': self.client_id,
            'scope': ' '.join(scopes),
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token',
            'client_secret': self.client_secret
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data=data
                )
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data['access_token']
            # Microsoft might return a new refresh token, update if available
            if 'refresh_token' in token_data:
                self.refresh_token = token_data['refresh_token']
            return True
        except httpx.RequestError as e:
            print(f"Failed to refresh OneDrive token: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during OneDrive token refresh: {e}")
            return False

    async def get_user_info(self) -> Dict[str, Any]:
        """Get OneDrive user information"""
        try:
            response = await self.make_request(
                'GET',
                f"{self.base_url}/me"
            )
            response.raise_for_status()
            data = response.json()
            
            # Get storage quota separately if needed, as /me doesn't include it directly
            # For simplicity, we'll use placeholders for now.
            storage_response = await self.make_request(
                'GET',
                f"{self.base_url}/me/drive"
            )
            storage_response.raise_for_status()
            storage_data = storage_response.json()

            return {
                'email': data.get('mail') or data.get('userPrincipalName'),
                'name': data.get('displayName'),
                'storage_used': storage_data.get('quota', {}).get('used', 0),
                'storage_limit': storage_data.get('quota', {}).get('total', 0)
            }
        except Exception as e:
            print(f"Failed to get OneDrive user info: {e}")
            raise Exception("Failed to retrieve user information from OneDrive")

    async def list_files(self, page_token: str = None, max_results: int = 100) -> Dict[str, Any]:
        """List files from OneDrive"""
        url = f"{self.base_url}/me/drive/root/children"
        
        select_fields = 'id,name,parentReference,createdDateTime,lastModifiedDateTime'
        if self.mode == "read-write":
            select_fields += ',webUrl,size,file,folder,@microsoft.graph.downloadUrl,fileSystemInfo,hashes'

        params = {
            '$top': max_results,
            '$select': select_fields
        }

        if page_token:
            url = page_token # OneDrive uses the @odata.nextLink directly as the next URL
            params = {}
        
        try:
            response = await self.make_request('GET', url, params=params)
            response.raise_for_status()
            data = response.json()
            
            files = []
            for item in data.get('value', []):
                if 'file' in item: # Only process files, skip folders
                    normalized_file = self.normalize_onedrive_metadata(item)
                    files.append(normalized_file)

            next_link = data.get('@odata.nextLink')
            
            return {
                'files': files,
                'next_page_token': next_link
            }
        except Exception as e:
            print(f"Failed to list OneDrive files: {e}")
            raise # Re-raise the exception

    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a specific OneDrive file"""
        select_fields = 'id,name,parentReference,createdDateTime,lastModifiedDateTime'
        if self.mode == "read-write":
            select_fields += ',webUrl,size,file,folder,@microsoft.graph.downloadUrl,fileSystemInfo,hashes'
        
        try:
            response = await self.make_request(
                'GET',
                f"{self.base_url}/me/drive/items/{file_id}?$select={select_fields}"
            )
            response.raise_for_status()
            file_data = response.json()
            return self.normalize_onedrive_metadata(file_data)
        except Exception as e:
            print(f"Failed to get OneDrive file metadata: {e}")
            raise # Re-raise the exception

    async def get_preview_link(self, file_id: str) -> Optional[str]:
        """Get a preview link for a file, if available and in read-write mode"""
        if self.mode == "metadata-only":
            return None

        try:
            # OneDrive provides 'webUrl' for viewing in browser. Direct download requires @microsoft.graph.downloadUrl
            response = await self.make_request(
                'GET',
                f"{self.base_url}/me/drive/items/{file_id}?$select=webUrl,@microsoft.graph.downloadUrl"
            )
            response.raise_for_status()
            data = response.json()
            return data.get('webUrl') or data.get('@microsoft.graph.downloadUrl')
        except Exception as e:
            print(f"Failed to get OneDrive preview link: {e}")
        return None

    def normalize_onedrive_metadata(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize OneDrive file metadata"""
        # OneDrive typically provides 'id', 'name', 'size', 'createdDateTime', 'lastModifiedDateTime', 'webUrl'
        
        preview_link = None
        download_link = None
        web_view_link = None
        content_hash = None
        mime_type = raw_metadata.get('file', {}).get('mimeType') or raw_metadata.get('folder', {}).get('folderType')

        if self.mode == "read-write":
            preview_link = raw_metadata.get('webUrl')
            download_link = raw_metadata.get('@microsoft.graph.downloadUrl')
            web_view_link = raw_metadata.get('webUrl')
            content_hash = raw_metadata.get('file', {}).get('hashes', {}).get('sha1Hash') # or crc32Hash, quickXorHash

        return {
            'provider_file_id': raw_metadata.get('id'),
            'name': raw_metadata.get('name'),
            'path': self.get_onedrive_path(raw_metadata), # Custom function to build path
            'size': raw_metadata.get('size'),
            'mime_type': mime_type,
            'file_extension': self.get_file_extension(raw_metadata.get('name'), mime_type),
            'created_at': self.parse_datetime(raw_metadata.get('createdDateTime')),
            'modified_at': self.parse_datetime(raw_metadata.get('lastModifiedDateTime')),
            'preview_link': preview_link,
            'download_link': download_link,
            'web_view_link': web_view_link,
            'content_hash': content_hash
        }
    
    def get_onedrive_path(self, raw_metadata: Dict[str, Any]) -> str:
        """Helper to reconstruct file path for OneDrive files."""
        parent_reference = raw_metadata.get('parentReference', {})
        path = parent_reference.get('path', '')
        if path.startswith('/drive/root:'):
            # Remove the '/drive/root:' prefix and decode URL-encoded parts
            path = path[len('/drive/root:'):]
        return path if path else '/'
