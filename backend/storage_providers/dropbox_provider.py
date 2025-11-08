from .base import CloudStorageProvider
from typing import Dict, Any, List, Optional
import requests
import dropbox
from datetime import datetime, timedelta
from urllib.parse import urlencode
import httpx

class DropboxProvider(CloudStorageProvider):
    """Dropbox API integration"""
    
    def __init__(self, access_token: str, refresh_token: str = None, client_id: str = None, client_secret: str = None, mode: str = "read-write", db_session: Any = None, storage_account_id: int = None):
        super().__init__(access_token, refresh_token, mode)
        self.client_id = client_id
        self.client_secret = client_secret
        self.dbx = dropbox.Dropbox(access_token)
        self.db_session = db_session # Store DB session
        self.storage_account_id = storage_account_id # Store storage account ID
    
    def get_provider_name(self) -> str:
        return "dropbox"

    @staticmethod
    async def exchange_code_for_token(code: str, client_id: str, client_secret: str, redirect_uri: str, scopes: List[str]) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        token_url = "https://api.dropboxapi.com/oauth2/token"
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
            print(f"Error exchanging code for Dropbox token: {e}")
            raise Exception("Failed to exchange code for Dropbox token")

    @staticmethod
    def get_authorization_url(client_id: str, redirect_uri: str, state: str, scopes: List[str], authorization_base_url: str) -> str:
        """Generate Dropbox authorization URL."""
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(scopes),
            'state': state,
            'token_access_type': 'offline' # To get a refresh token
        }

        return f"{authorization_base_url}?{urlencode(params)}"
    
    async def update_db_tokens(self, access_token: str, refresh_token: Optional[str], expires_in: int) -> None:
        if not self.db_session or not self.storage_account_id:
            print("DEBUG: DB session or storage account ID not available for Dropbox token update.")
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
                print(f"DEBUG: Successfully updated tokens for Dropbox storage account {self.storage_account_id} in DB.")
            else:
                print(f"DEBUG: Dropbox storage account {self.storage_account_id} not found for token update.")
        except Exception as e:
            print(f"ERROR: Failed to update DB tokens for Dropbox: {e}")
            self.db_session.rollback()

    async def refresh_access_token(self) -> bool:
        """Refresh access token using Dropbox OAuth"""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            return False
        
        try:
            response = await self.make_request(
                'POST',
                'https://api.dropboxapi.com/oauth2/token',
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                # Dropbox might not return refresh_token on refresh, keep existing if not provided
                new_refresh_token = data.get('refresh_token', self.refresh_token)
                expires_in = data.get('expires_in', 14400) # Default to 4 hours if not provided
                await self.update_db_tokens(self.access_token, new_refresh_token, expires_in)
                self.refresh_token = new_refresh_token # Update instance's refresh token
                self.dbx = dropbox.Dropbox(self.access_token)
                return True
            
        except Exception as e:
            print(f"Failed to refresh Dropbox token: {e}")
        
        return False
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get Dropbox user information"""
        try:
            # Get current account info
            account = await self.dbx.users_get_current_account()
            
            # Get space usage
            space_usage = await self.dbx.users_get_space_usage()
            
            return {
                'email': account.email,
                'name': account.name.display_name,
                'storage_used': space_usage.used,
                'storage_limit': space_usage.allocation.get_individual().allocated
            }
        
        except Exception as e:
            print(f"Failed to get Dropbox user info: {e}")
            return {}

    async def get_storage_quota(self) -> Dict[str, Any]:
        """Get Dropbox storage quota information"""
        try:
            space_usage = await self.dbx.users_get_space_usage()
            # Dropbox provides `used` and `allocated` for individual accounts.
            # For team accounts, it provides `team`. We're assuming individual here.
            allocated_space = space_usage.allocation.get_individual().allocated
            used_space = space_usage.used
            
            return {
                'total': allocated_space,
                'used': used_space,
                'remaining': allocated_space - used_space
            }
        except Exception as e:
            print(f"Failed to get Dropbox storage quota: {e}")
            return {'total': 0, 'used': 0, 'remaining': 0}
    
    async def list_files(self, page_token: str = None, max_results: int = 100) -> Dict[str, Any]:
        """List files from Dropbox"""
        try:
            if page_token:
                # Continue from cursor
                result = await self.dbx.files_list_folder_continue(page_token)
            else:
                # Start from root
                result = await self.dbx.files_list_folder(
                    "",
                    recursive=True,
                    limit=min(max_results, 2000)
                )
            
            files = []
            for entry in result.entries:
                # Skip folders
                if isinstance(entry, dropbox.files.FolderMetadata):
                    continue
                
                if isinstance(entry, dropbox.files.FileMetadata):
                    normalized_file = await self.normalize_dropbox_metadata(entry)
                    files.append(normalized_file)
            
            return {
                'files': files,
                'next_page_token': result.cursor if result.has_more else None
            }
        
        except Exception as e:
            print(f"Failed to list Dropbox files: {e}")
            return {'files': [], 'next_page_token': None}
    
    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a specific Dropbox file"""
        try:
            # In Dropbox, file_id is actually the path
            metadata = await self.dbx.files_get_metadata(file_id)
            
            if isinstance(metadata, dropbox.files.FileMetadata):
                return await self.normalize_dropbox_metadata(metadata)
        
        except Exception as e:
            print(f"Failed to get Dropbox file metadata: {e}")
        
        return {}
    
    async def normalize_dropbox_metadata(self, file_metadata: dropbox.files.FileMetadata) -> Dict[str, Any]:
        """Normalize Dropbox file metadata"""
        # Get preview link if possible
        preview_link = None
        download_link = None
        web_view_link = None
        
        try:
            # Get shared link for preview
            shared_link = await self.dbx.sharing_create_shared_link_with_settings(
                file_metadata.path_lower,
                dropbox.sharing.SharedLinkSettings(
                    require_password=False,
                    link_password=None,
                    expires=None
                )
            )
            web_view_link = shared_link.url
            
            # Create direct download link
            download_link = shared_link.url.replace('dropbox.com', 'dl.dropboxusercontent.com')
            download_link = download_link.replace('?dl=0', '')
            
        except dropbox.exceptions.ApiError as e:
            # Link might already exist or sharing not allowed
            try:
                # Try to get existing shared links
                existing_links = await self.dbx.sharing_list_shared_links(path=file_metadata.path_lower)
                if existing_links.links:
                    web_view_link = existing_links.links[0].url
                    download_link = web_view_link.replace('dropbox.com', 'dl.dropboxusercontent.com')
                    download_link = download_link.replace('?dl=0', '')
            except:
                pass
        
        return {
            'provider_file_id': file_metadata.path_lower,  # Use path as ID for Dropbox
            'name': file_metadata.name,
            'path': file_metadata.path_display,
            'size': file_metadata.size,
            'mime_type': self.get_mime_type_from_extension(file_metadata.name),
            'file_extension': self.get_file_extension(file_metadata.name),
            'created_at': None,  # Dropbox doesn't provide creation time
            'modified_at': file_metadata.server_modified,
            'preview_link': preview_link,
            'download_link': download_link,
            'web_view_link': web_view_link,
            'content_hash': file_metadata.content_hash
        }
    
    def get_mime_type_from_extension(self, filename: str) -> str:
        """Get MIME type based on file extension"""
        extension = self.get_file_extension(filename)
        
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'mp4': 'video/mp4',
            'mp3': 'audio/mpeg',
            'zip': 'application/zip'
        }
        
        return mime_types.get(extension.lower(), 'application/octet-stream')
