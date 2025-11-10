from .base import CloudStorageProvider
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime, timedelta

class OneDriveProvider(CloudStorageProvider):
    """Microsoft OneDrive API integration via Microsoft Graph API"""
    
    def __init__(self, access_token: str, refresh_token: str = None, client_id: str = None, client_secret: str = None, mode: str = "read-write", db_session: Any = None, storage_account_id: int = None):
        super().__init__(access_token, refresh_token, mode)
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.db_session = db_session
        self.storage_account_id = storage_account_id
    
    def get_provider_name(self) -> str:
        return "onedrive"

    async def update_db_tokens(self, access_token: str, refresh_token: Optional[str], expires_in: int) -> None:
        """Update the access and refresh tokens in the database"""
        if not self.db_session or not self.storage_account_id:
            print("DEBUG: DB session or storage account ID not available for OneDrive token update.")
            return
        
        try:
            from backend.models import StorageAccount  # Import locally to avoid circular dependency
            from backend.utils import SecurityUtils  # Import SecurityUtils locally

            storage_account = self.db_session.query(StorageAccount).filter(StorageAccount.id == self.storage_account_id).first()
            if storage_account:
                security_utils = SecurityUtils()  # Initialize SecurityUtils
                storage_account.access_token = security_utils.encrypt_token(access_token)
                if refresh_token:
                    storage_account.refresh_token = security_utils.encrypt_token(refresh_token)
                storage_account.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                storage_account.updated_at = datetime.utcnow()
                self.db_session.commit()
                print(f"DEBUG: Successfully updated tokens for OneDrive storage account {self.storage_account_id} in DB.")
            else:
                print(f"DEBUG: OneDrive storage account {self.storage_account_id} not found for token update.")
        except Exception as e:
            print(f"ERROR: Failed to update DB tokens for OneDrive: {e}")
            self.db_session.rollback()

    @staticmethod
    async def exchange_code_for_token(code: str, client_id: str, client_secret: str, redirect_uri: str, scopes: List[str]) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens"""
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
            
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"Error exchanging code for OneDrive token: {e}")
            raise Exception("Failed to exchange code for OneDrive token")

    @staticmethod
    def get_authorization_url(client_id: str, redirect_uri: str, state: str, scopes: List[str], authorization_base_url: str) -> str:
        """Generate OneDrive authorization URL"""
        from urllib.parse import urlencode
        
        params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ' '.join(scopes),
            'state': state,
            'response_mode': 'query'
        }
        
        return f"{authorization_base_url}?{urlencode(params)}"

    async def refresh_access_token(self) -> bool:
        """Refresh access token using Microsoft OAuth"""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://login.microsoftonline.com/common/oauth2/v2.0/token',
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
                new_refresh_token = data.get('refresh_token', self.refresh_token)
                expires_in = data.get('expires_in', 3600)
                
                await self.update_db_tokens(self.access_token, new_refresh_token, expires_in)
                self.refresh_token = new_refresh_token
                print(f"DEBUG: OneDrive token refreshed successfully")
                return True
            else:
                print(f"ERROR: Token refresh failed with status {response.status_code}: {response.text}")
                return False
            
        except Exception as e:
            print(f"Failed to refresh OneDrive token: {e}")
            return False
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get OneDrive user information"""
        try:
            # Get user profile
            user_response = await self.make_request('GET', f"{self.base_url}/me")
            
            # Get drive info (includes quota)
            drive_response = await self.make_request('GET', f"{self.base_url}/me/drive")
            
            if user_response.status_code == 200 and drive_response.status_code == 200:
                user_data = user_response.json()
                drive_data = drive_response.json()
                
                quota = drive_data.get('quota', {})
                
                return {
                    'email': user_data.get('userPrincipalName') or user_data.get('mail'),
                    'name': user_data.get('displayName'),
                    'storage_used': quota.get('used', 0),
                    'storage_limit': quota.get('total', 0)
                }
            
            return {}
        
        except Exception as e:
            print(f"Failed to get OneDrive user info: {e}")
            return {}

    async def get_storage_quota(self) -> Dict[str, Any]:
        """Get OneDrive storage quota information"""
        try:
            response = await self.make_request('GET', f"{self.base_url}/me/drive")
            
            if response.status_code == 200:
                drive_data = response.json()
                quota = drive_data.get('quota', {})
                
                total = quota.get('total', 0)
                used = quota.get('used', 0)
                
                return {
                    'total': total,
                    'used': used,
                    'remaining': total - used
                }
            
            return {'total': 0, 'used': 0, 'remaining': 0}
        
        except Exception as e:
            print(f"Failed to get OneDrive storage quota: {e}")
            return {'total': 0, 'used': 0, 'remaining': 0}
    
    async def list_files(self, page_token: str = None, max_results: int = 100) -> Dict[str, Any]:
        """List files from OneDrive"""
        try:
            # Use skipToken for pagination if provided
            if page_token:
                url = page_token  # Microsoft Graph returns full URL for next page
            else:
                # List all items recursively from root
                url = f"{self.base_url}/me/drive/root/children?$top={max_results}"
            
            response = await self.make_request('GET', url)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('value', [])
                
                files = []
                for item in items:
                    # Skip folders unless you want to list them
                    if 'folder' in item:
                        continue
                    
                    normalized_file = await self.normalize_onedrive_metadata(item)
                    files.append(normalized_file)
                
                # Get next page token
                next_link = data.get('@odata.nextLink')
                
                return {
                    'files': files,
                    'next_page_token': next_link
                }
            
            return {'files': [], 'next_page_token': None}
        
        except Exception as e:
            print(f"Failed to list OneDrive files: {e}")
            return {'files': [], 'next_page_token': None}
    
    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a specific OneDrive file"""
        try:
            response = await self.make_request('GET', f"{self.base_url}/me/drive/items/{file_id}")
            
            if response.status_code == 200:
                item = response.json()
                return await self.normalize_onedrive_metadata(item)
            
            return {}
        
        except Exception as e:
            print(f"Failed to get OneDrive file metadata: {e}")
            return {}
    
    async def normalize_onedrive_metadata(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize OneDrive file metadata to unified format"""
        
        # Get file properties
        file_info = item.get('file', {})
        
        # Get hashes for duplicate detection
        hashes = file_info.get('hashes', {})
        content_hash = hashes.get('quickXorHash') or hashes.get('sha1Hash')
        
        # Get preview and download links
        web_url = item.get('webUrl')  # Browser preview link
        download_url = item.get('@microsoft.graph.downloadUrl')  # Direct download (expires in 1 hour)
        
        # Get timestamps
        created_time = item.get('createdDateTime')
        modified_time = item.get('lastModifiedDateTime')
        
        # Parse timestamps
        created_at = None
        modified_at = None
        
        if created_time:
            try:
                created_at = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
            except:
                pass
        
        if modified_time:
            try:
                modified_at = datetime.fromisoformat(modified_time.replace('Z', '+00:00'))
            except:
                pass
        
        return {
            'provider_file_id': item.get('id'),
            'name': item.get('name'),
            'path': item.get('parentReference', {}).get('path', '') + '/' + item.get('name', ''),
            'size': item.get('size', 0),
            'mime_type': file_info.get('mimeType') or 'application/octet-stream',
            'file_extension': self.get_file_extension(item.get('name', '')),
            'created_at': created_at,
            'modified_at': modified_at,
            'preview_link': web_url,
            'download_link': download_url,
            'web_view_link': web_url,
            'thumbnail_link': None,  # Can be added if needed
            'content_hash': content_hash
        }
    
    def get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        if '.' in filename:
            return filename.rsplit('.', 1)[-1].lower()
        return ''
    
    async def upload_file(self, file_name: str, file_content: bytes, folder_path: str = "/", mime_type: str = None) -> Dict[str, Any]:
        """Upload a file to OneDrive"""
        if self.mode == "metadata":
            raise Exception("File upload not allowed in metadata mode")
        
        try:
            # Refresh token first
            if self.refresh_token and self.client_id and self.client_secret:
                try:
                    await self.refresh_access_token()
                except Exception as refresh_error:
                    print(f"DEBUG: Token refresh failed: {refresh_error}")
            
            # Construct upload path
            if folder_path == "/" or folder_path == "":
                upload_path = f"/me/drive/root:/{file_name}:/content"
            else:
                # Clean folder path
                folder_path = folder_path.strip('/')
                upload_path = f"/me/drive/root:/{folder_path}/{file_name}:/content"
            
            url = f"{self.base_url}{upload_path}"
            
            print(f"DEBUG: Uploading to OneDrive path: {upload_path}")
            
            # Upload using PUT request
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': mime_type or 'application/octet-stream'
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.put(url, content=file_content, headers=headers)
            
            if response.status_code in [200, 201]:
                item = response.json()
                print(f"DEBUG: File uploaded successfully to OneDrive: {file_name}")
                
                normalized = await self.normalize_onedrive_metadata(item)
                
                return {
                    'success': True,
                    'file': normalized
                }
            else:
                raise Exception(f"Upload failed with status {response.status_code}: {response.text}")
        
        except Exception as e:
            print(f"ERROR: Failed to upload file to OneDrive: {e}")
            raise Exception(f"Failed to upload file to OneDrive: {str(e)}")
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from OneDrive"""
        if self.mode == "metadata":
            raise Exception("File deletion not allowed in metadata mode")
        
        try:
            # Refresh token first
            if self.refresh_token and self.client_id and self.client_secret:
                try:
                    await self.refresh_access_token()
                except Exception as refresh_error:
                    print(f"DEBUG: Token refresh failed: {refresh_error}")
            
            response = await self.make_request('DELETE', f"{self.base_url}/me/drive/items/{file_id}")
            
            if response.status_code == 204:
                print(f"DEBUG: File deleted successfully from OneDrive: {file_id}")
                return True
            
            return False
        
        except Exception as e:
            print(f"ERROR: Failed to delete file from OneDrive: {e}")
            raise Exception(f"Failed to delete file from OneDrive: {str(e)}")
    
    async def get_preview_link(self, file_id: str) -> Optional[str]:
        """Get preview link for a file"""
        try:
            response = await self.make_request('GET', f"{self.base_url}/me/drive/items/{file_id}")
            
            if response.status_code == 200:
                item = response.json()
                return item.get('webUrl')
            
            return None
        
        except Exception as e:
            print(f"Failed to get OneDrive preview link: {e}")
            return None
