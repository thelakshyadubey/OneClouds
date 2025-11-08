from .base import CloudStorageProvider
from typing import Dict, Any, List, Optional
import httpx # Import httpx
from urllib.parse import urlencode
from datetime import datetime, timedelta

class GoogleDriveProvider(CloudStorageProvider):
    """Google Drive API integration"""
    
    def __init__(self, access_token: str, refresh_token: str = None, client_id: str = None, client_secret: str = None, mode: str = "read-write", db_session: Any = None, storage_account_id: int = None):
        super().__init__(access_token, refresh_token, mode)
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://www.googleapis.com/drive/v3"
        self.db_session = db_session # Store DB session
        self.storage_account_id = storage_account_id # Store storage account ID
    
    def get_provider_name(self) -> str:
        return "google_drive"

    @staticmethod
    def get_authorization_url(client_id: str, redirect_uri: str, state: str, scopes: List[str], authorization_base_url: str) -> str:
        """Generate Google Drive authorization URL."""
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(scopes),
            'access_type': 'offline', # To get a refresh token
            'prompt': 'consent',     # To ensure refresh token is always returned
            'state': state
        }
        
        return f"{authorization_base_url}?{urlencode(params)}"

    @staticmethod
    async def exchange_code_for_token(code: str, client_id: str, client_secret: str, redirect_uri: str, scopes: List[str]) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
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
            print(f"Error exchanging code for token: {e}")
            raise Exception("Failed to exchange code for token")

    async def refresh_access_token(self) -> bool:
        """Refresh access token using Google OAuth"""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://oauth2.googleapis.com/token',
                    data={
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'refresh_token': self.refresh_token,
                        'grant_type': 'refresh_token'
                    }
                )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                # If refresh token is also returned, update it. Otherwise, keep the existing one.
                new_refresh_token = data.get('refresh_token', self.refresh_token)
                expires_in = data.get('expires_in', 3600) # Default to 1 hour if not provided
                await self.update_db_tokens(self.access_token, new_refresh_token, expires_in)
                self.refresh_token = new_refresh_token # Update instance's refresh token
                return True
            
        except Exception as e:
            print(f"Failed to refresh Google Drive token: {e}")
        
        return False
    
    async def update_db_tokens(self, access_token: str, refresh_token: Optional[str], expires_in: int) -> None:
        if not self.db_session or not self.storage_account_id:
            print("DEBUG: DB session or storage account ID not available for token update.")
            return
        
        try:
            from backend.models import StorageAccount # Import locally to avoid circular dependency
            from backend.utils import SecurityUtils # Import SecurityUtils locally

            storage_account = self.db_session.query(StorageAccount).filter(StorageAccount.id == self.storage_account_id).first()
            if storage_account:
                security_utils = SecurityUtils() # Initialize SecurityUtils
                storage_account.access_token = security_utils.encrypt_token(access_token)
                if refresh_token:
                    storage_account.refresh_token = security_utils.encrypt_token(refresh_token)
                storage_account.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                storage_account.updated_at = datetime.utcnow()
                self.db_session.commit()
                print(f"DEBUG: Successfully updated tokens for storage account {self.storage_account_id} in DB.")
            else:
                print(f"DEBUG: Storage account {self.storage_account_id} not found for token update.")
        except Exception as e:
            print(f"ERROR: Failed to update DB tokens for Google Drive: {e}")
            self.db_session.rollback()

    async def get_user_info(self) -> Dict[str, Any]:
        """Get Google Drive user information"""
        try:
            response = await self.make_request(
                'GET',
                f"{self.base_url}/about",
                params={'fields': 'user,storageQuota'}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'email': data['user']['emailAddress'],
                    'name': data['user']['displayName'],
                    'storage_used': data['storageQuota'].get('usage', 0),
                    'storage_limit': data['storageQuota'].get('limit', 0)
                }
        
        except Exception as e:
            print(f"Failed to get Google Drive user info: {e}")
            raise Exception("Failed to retrieve user information from Google Drive")
    
    async def list_files(self, page_token: str = None, max_results: int = 100) -> Dict[str, Any]:
        """List files from Google Drive"""
        # webViewLink is available for both modes (read-only preview)
        # Other fields like md5Checksum are only for full_access mode
        fields = 'nextPageToken,files(id,name,parents,mimeType,size,createdTime,modifiedTime,webViewLink,thumbnailLink,fullFileExtension)'
        if self.mode == "full_access":
            fields = 'nextPageToken,files(id,name,parents,mimeType,size,createdTime,modifiedTime,webViewLink,thumbnailLink,fullFileExtension,md5Checksum,webContentLink)'

        params = {
            'pageSize': min(max_results, 1000),
            'fields': fields,
            'q': "trashed=false"  # Only get non-trashed files
        }
        
        if page_token:
            params['pageToken'] = page_token
        
        try:
            response = await self.make_request('GET', f"{self.base_url}/files", params=params)
            
            if response.status_code == 200:
                data = response.json()
                files = []
                
                for file_data in data.get('files', []):
                    # Skip folders
                    if file_data.get('mimeType') == 'application/vnd.google-apps.folder':
                        continue
                    
                    normalized_file = await self.normalize_google_drive_metadata(file_data)
                    files.append(normalized_file)
                
                return {
                    'files': files,
                    'next_page_token': data.get('nextPageToken')
                }
            else:
                print(f"DEBUG: Google Drive list_files API returned status {response.status_code}: {response.text}")
                return {'files': [], 'next_page_token': None} # Return empty list on non-200 status
        
        except Exception as e:
            print(f"Failed to list Google Drive files: {e}")
            return {'files': [], 'next_page_token': None} # Return empty list on exception
    
    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a specific Google Drive file"""
        # webViewLink is available for both modes (read-only preview)
        fields = 'id,name,parents,mimeType,size,createdTime,modifiedTime,webViewLink,thumbnailLink,fullFileExtension'
        if self.mode == "full_access":
            fields = 'id,name,parents,mimeType,size,createdTime,modifiedTime,webViewLink,thumbnailLink,fullFileExtension,md5Checksum,webContentLink'

        try:
            response = await self.make_request(
                'GET',
                f"{self.base_url}/files/{file_id}",
                params={
                    'fields': fields
                }
            )
            
            if response.status_code == 200:
                file_data = response.json()
                return await self.normalize_google_drive_metadata(file_data)
        
        except Exception as e:
            print(f"Failed to get Google Drive file metadata: {e}")
            raise # Re-raise the exception
    
    async def get_preview_link(self, file_id: str) -> Optional[str]:
        """Get a preview link for a file, if available and in full_access mode"""
        if self.mode == "metadata":
            return None

        try:
            response = await self.make_request(
                'GET',
                f"{self.base_url}/files/{file_id}",
                params={'fields': 'webViewLink,thumbnailLink'}
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('webViewLink') or data.get('thumbnailLink')
        except Exception as e:
            print(f"Failed to get Google Drive preview link: {e}")
        return None

    async def normalize_google_drive_metadata(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Google Drive file metadata"""
        # Get file path by resolving parent folders
        path = await self.get_file_path(raw_metadata.get('parents', []))
        
        # web_view_link is always available for both modes (read-only preview)
        # preview_link, download_link, and content_hash are only for full_access mode
        web_view_link = raw_metadata.get('webViewLink')
        preview_link = raw_metadata.get('thumbnailLink') if self.mode == "full_access" else None
        download_link = raw_metadata.get('webContentLink') if self.mode == "full_access" else None
        content_hash = raw_metadata.get('md5Checksum') if self.mode == "full_access" else None

        return {
            'provider_file_id': raw_metadata['id'],
            'name': raw_metadata['name'],
            'path': path,
            'size': int(raw_metadata.get('size', 0)) if raw_metadata.get('size') else None,
            'mime_type': raw_metadata.get('mimeType'),
            'file_extension': self.get_file_extension(
                raw_metadata.get('fullFileExtension', raw_metadata.get('name')),
                raw_metadata.get('mimeType')
            ),
            'created_at': self.parse_datetime(raw_metadata.get('createdTime')),
            'modified_at': self.parse_datetime(raw_metadata.get('modifiedTime')),
            'preview_link': preview_link,
            'download_link': download_link,
            'web_view_link': web_view_link,
            'content_hash': content_hash
        }
    
    async def get_file_path(self, parent_ids: List[str]) -> str:
        """Get the full path of a file by resolving parent folder names"""
        if not parent_ids:
            return "/"
        
        try:
            # For simplicity, just get the immediate parent folder name
            # In a production app, you might want to build the full path
            parent_id = parent_ids[0]
            response = await self.make_request(
                'GET',
                f"{self.base_url}/files/{parent_id}",
                params={'fields': 'name'}
            )
            
            if response.status_code == 200:
                parent_data = response.json()
                return f"/{parent_data.get('name', 'Unknown')}"
        
        except Exception as e:
            print(f"Failed to get parent folder name: {e}")
        
        return "/"

    async def get_storage_quota(self) -> Dict[str, Any]:
        """Get Google Drive storage quota information"""
        try:
            response = await self.make_request(
                'GET',
                f"{self.base_url}/about",
                params={'fields': 'storageQuota'}
            )

            if response.status_code == 200:
                data = response.json()
                storage_quota = data.get('storageQuota', {})
                return {
                    'total': int(storage_quota.get('limit', 0)),
                    'used': int(storage_quota.get('usage', 0)),
                    'remaining': int(storage_quota.get('limit', 0)) - int(storage_quota.get('usage', 0))
                }
            else:
                print(f"DEBUG: Google Drive get_storage_quota API returned status {response.status_code}: {response.text}")
                return {'total': 0, 'used': 0, 'remaining': 0}
        except Exception as e:
            print(f"Failed to get Google Drive storage quota: {e}")
            return {'total': 0, 'used': 0, 'remaining': 0}
    
    async def upload_file(self, file_name: str, file_content: bytes, folder_path: str = "/", mime_type: str = None) -> Dict[str, Any]:
        """Upload a file to Google Drive"""
        if self.mode == "metadata":
            raise Exception("File upload not allowed in metadata mode")
        
        try:
            # Upload URL for simple upload - request all necessary fields
            upload_url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,parents,mimeType,size,createdTime,modifiedTime,webViewLink,thumbnailLink,fullFileExtension,md5Checksum,webContentLink"
            
            # Create metadata
            metadata = {
                'name': file_name,
                'mimeType': mime_type or 'application/octet-stream'
            }
            
            # Create multipart request
            boundary = '-------314159265358979323846'
            delimiter = f"\r\n--{boundary}\r\n"
            close_delim = f"\r\n--{boundary}--"
            
            import json
            metadata_part = delimiter + 'Content-Type: application/json; charset=UTF-8\r\n\r\n' + json.dumps(metadata)
            file_part = delimiter + f'Content-Type: {mime_type or "application/octet-stream"}\r\n\r\n'
            
            body = metadata_part.encode('utf-8') + file_part.encode('utf-8') + file_content + close_delim.encode('utf-8')
            
            headers = {
                'Content-Type': f'multipart/related; boundary={boundary}',
                'Content-Length': str(len(body))
            }
            
            # Use make_request equivalent with retry logic
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    upload_url,
                    content=body,
                    headers={**headers, 'Authorization': f'Bearer {self.access_token}'}
                )
                
                # Handle 401 - try to refresh token and retry
                if response.status_code == 401:
                    if self.refresh_token:
                        if await self.refresh_access_token():
                            # Retry with new token
                            response = await client.post(
                                upload_url,
                                content=body,
                                headers={**headers, 'Authorization': f'Bearer {self.access_token}'}
                            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                # Return normalized metadata
                return await self.normalize_google_drive_metadata(data)
            else:
                raise Exception(f"Upload failed with status {response.status_code}: {response.text}")
        
        except Exception as e:
            print(f"Failed to upload file to Google Drive: {e}")
            raise
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive"""
        if self.mode == "metadata":
            raise Exception("File deletion not allowed in metadata mode")
        
        try:
            response = await self.make_request(
                'DELETE',
                f"{self.base_url}/files/{file_id}"
            )
            
            return response.status_code == 204
        
        except Exception as e:
            print(f"Failed to delete file from Google Drive: {e}")
            raise
