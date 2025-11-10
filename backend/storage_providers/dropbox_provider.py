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
            async with httpx.AsyncClient() as client:
                response = await client.post(
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
                print(f"DEBUG: Dropbox token refreshed successfully")
                return True
            else:
                print(f"ERROR: Token refresh failed with status {response.status_code}: {response.text}")
                return False
            
        except Exception as e:
            print(f"Failed to refresh Dropbox token: {e}")
            return False
        
        return False
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get Dropbox user information"""
        try:
            # Get current account info (Dropbox SDK is synchronous, not async)
            account = self.dbx.users_get_current_account()
            
            # Get space usage
            space_usage = self.dbx.users_get_space_usage()
            
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
            # Dropbox SDK is synchronous
            space_usage = self.dbx.users_get_space_usage()
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
            # Dropbox SDK is synchronous
            if page_token:
                # Continue from cursor
                result = self.dbx.files_list_folder_continue(page_token)
            else:
                # Start from root
                result = self.dbx.files_list_folder(
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
                    try:
                        normalized_file = await self.normalize_dropbox_metadata(entry)
                        files.append(normalized_file)
                    except Exception as norm_error:
                        print(f"ERROR: Failed to normalize metadata for {entry.name}: {norm_error}")
                        # Continue with next file instead of failing the whole sync
                        continue
            
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
            # Dropbox SDK is synchronous
            metadata = self.dbx.files_get_metadata(file_id)
            
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
        
        # For metadata mode: Try to get shared links (read-only, doesn't require sharing.write)
        # For full_access mode: Try to create shared links
        if self.mode == "metadata":
            try:
                # Try to get existing shared links first (works with metadata scope)
                existing_links = self.dbx.sharing_list_shared_links(path=file_metadata.path_lower)
                if existing_links.links:
                    web_view_link = existing_links.links[0].url
                    # Create a direct download link from shared link
                    download_link = web_view_link.replace('?dl=0', '?dl=1')
                    preview_link = web_view_link
                    print(f"DEBUG: Found existing shared link for {file_metadata.name}: {web_view_link}")
                else:
                    # If no existing links, construct a Dropbox preview URL
                    # This will open the file in Dropbox web interface (requires user to be logged in)
                    import urllib.parse
                    file_path = file_metadata.path_display
                    # Encode the path for URL
                    encoded_path = urllib.parse.quote(file_path)
                    web_view_link = f"https://www.dropbox.com/preview{encoded_path}"
                    preview_link = web_view_link
                    print(f"DEBUG: Generated preview link for {file_metadata.name}: {web_view_link}")
            except Exception as e:
                print(f"DEBUG: Failed to get Dropbox preview link for {file_metadata.name}: {e}")
                # Fallback: construct preview URL
                try:
                    import urllib.parse
                    file_path = file_metadata.path_display
                    encoded_path = urllib.parse.quote(file_path)
                    web_view_link = f"https://www.dropbox.com/preview{encoded_path}"
                    preview_link = web_view_link
                    print(f"DEBUG: Fallback preview URL for {file_metadata.name}: {web_view_link}")
                except:
                    pass
        elif self.mode == "full_access":
            try:
                # Get shared link for preview (Dropbox SDK is synchronous)
                shared_link = self.dbx.sharing_create_shared_link_with_settings(
                    file_metadata.path_lower,
                    dropbox.sharing.SharedLinkSettings(
                        require_password=False,
                        link_password=None,
                        expires=None
                    )
                )
                web_view_link = shared_link.url
                
                # Create direct download link
                download_link = shared_link.url.replace('?dl=0', '?dl=1')
                preview_link = web_view_link
                print(f"DEBUG: Created shared link for {file_metadata.name}: {web_view_link}")
                
            except Exception as e:
                # Catch ALL exceptions (ApiError, BadInputError, etc.)
                print(f"DEBUG: Failed to create shared link for {file_metadata.name}: {e}")
                # Link might already exist or sharing not allowed, or app doesn't have permission
                try:
                    # Try to get existing shared links
                    existing_links = self.dbx.sharing_list_shared_links(path=file_metadata.path_lower)
                    if existing_links.links:
                        web_view_link = existing_links.links[0].url
                        download_link = web_view_link.replace('?dl=0', '?dl=1')
                        preview_link = web_view_link
                        print(f"DEBUG: Found existing shared link for {file_metadata.name}: {web_view_link}")
                    else:
                        # Final fallback to preview URL
                        import urllib.parse
                        file_path = file_metadata.path_display
                        encoded_path = urllib.parse.quote(file_path)
                        web_view_link = f"https://www.dropbox.com/preview{encoded_path}"
                        preview_link = web_view_link
                        print(f"DEBUG: Fallback preview URL for {file_metadata.name}: {web_view_link}")
                except Exception as e2:
                    print(f"DEBUG: Failed to get existing links for {file_metadata.name}: {e2}")
                    # Final fallback to preview URL
                    try:
                        import urllib.parse
                        file_path = file_metadata.path_display
                        encoded_path = urllib.parse.quote(file_path)
                        web_view_link = f"https://www.dropbox.com/preview{encoded_path}"
                        preview_link = web_view_link
                        print(f"DEBUG: Final fallback preview URL for {file_metadata.name}: {web_view_link}")
                    except:
                        pass
        
        print(f"DEBUG normalize_dropbox_metadata FINAL: name={file_metadata.name}, web_view_link={web_view_link}, preview_link={preview_link}")
        
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
    
    async def upload_file(self, file_name: str, file_content: bytes, folder_path: str = "/", mime_type: str = None) -> Dict[str, Any]:
        """Upload a file to Dropbox"""
        if self.mode == "metadata":
            raise Exception("File upload not allowed in metadata mode")
        
        try:
            # Try to refresh token first if we have refresh token
            if self.refresh_token and self.client_id and self.client_secret:
                try:
                    await self.refresh_access_token()
                    # Update dbx instance with new token
                    self.dbx = dropbox.Dropbox(self.access_token)
                except Exception as refresh_error:
                    print(f"DEBUG: Token refresh failed: {refresh_error}, proceeding with existing token")
            
            # Construct the full path
            if folder_path == "/" or folder_path == "":
                full_path = f"/{file_name}"
            else:
                # Ensure folder_path starts with / and doesn't end with /
                folder_path = folder_path.strip()
                if not folder_path.startswith("/"):
                    folder_path = "/" + folder_path
                if folder_path.endswith("/"):
                    folder_path = folder_path[:-1]
                full_path = f"{folder_path}/{file_name}"
            
            print(f"DEBUG: Uploading to Dropbox path: {full_path}")
            
            # Upload file using Dropbox SDK (synchronous)
            # Use files_upload for files up to 150MB
            file_metadata = self.dbx.files_upload(
                file_content,
                full_path,
                mode=dropbox.files.WriteMode.add,  # Don't overwrite, create new
                autorename=True,  # Auto-rename if file exists
                mute=False
            )
            
            print(f"DEBUG: File uploaded successfully: {file_metadata.name}")
            
            # Normalize the metadata to match our format
            normalized = await self.normalize_dropbox_metadata(file_metadata)
            
            return {
                'success': True,
                'file': normalized
            }
            
        except dropbox.exceptions.AuthError as auth_error:
            print(f"ERROR: Dropbox auth error during upload: {auth_error}")
            # Try to refresh token one more time
            if self.refresh_token and self.client_id and self.client_secret:
                try:
                    print(f"DEBUG: Attempting token refresh after auth error...")
                    await self.refresh_access_token()
                    self.dbx = dropbox.Dropbox(self.access_token)
                    
                    # Retry upload with refreshed token
                    file_metadata = self.dbx.files_upload(
                        file_content,
                        full_path,
                        mode=dropbox.files.WriteMode.add,
                        autorename=True,
                        mute=False
                    )
                    
                    print(f"DEBUG: File uploaded successfully after token refresh: {file_metadata.name}")
                    normalized = await self.normalize_dropbox_metadata(file_metadata)
                    
                    return {
                        'success': True,
                        'file': normalized
                    }
                except Exception as retry_error:
                    print(f"ERROR: Failed to upload even after token refresh: {retry_error}")
                    raise Exception(f"Failed to upload file to Dropbox (auth error): {str(retry_error)}")
            else:
                raise Exception(f"Dropbox authentication failed. Please reconnect your account.")
        except Exception as e:
            print(f"ERROR: Failed to upload file to Dropbox: {e}")
            raise Exception(f"Failed to upload file to Dropbox: {str(e)}")
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from Dropbox"""
        if self.mode == "metadata":
            raise Exception("File deletion not allowed in metadata mode")
        
        try:
            # In Dropbox, file_id is the file path
            # Refresh token first if we have refresh capabilities
            if self.refresh_token and self.client_id and self.client_secret:
                try:
                    await self.refresh_access_token()
                    self.dbx = dropbox.Dropbox(self.access_token)
                except Exception as refresh_error:
                    print(f"DEBUG: Token refresh failed before delete: {refresh_error}")
            
            # Delete the file using Dropbox SDK (synchronous)
            self.dbx.files_delete_v2(file_id)
            
            print(f"DEBUG: File deleted successfully from Dropbox: {file_id}")
            return True
        
        except dropbox.exceptions.AuthError as auth_error:
            print(f"ERROR: Dropbox auth error during delete: {auth_error}")
            # Try to refresh token and retry
            if self.refresh_token and self.client_id and self.client_secret:
                try:
                    print(f"DEBUG: Attempting token refresh after auth error...")
                    await self.refresh_access_token()
                    self.dbx = dropbox.Dropbox(self.access_token)
                    
                    # Retry delete with refreshed token
                    self.dbx.files_delete_v2(file_id)
                    print(f"DEBUG: File deleted successfully after token refresh: {file_id}")
                    return True
                except Exception as retry_error:
                    print(f"ERROR: Failed to delete even after token refresh: {retry_error}")
                    raise Exception(f"Failed to delete file from Dropbox (auth error): {str(retry_error)}")
            else:
                raise Exception(f"Dropbox authentication failed. Please reconnect your account.")
        except Exception as e:
            print(f"ERROR: Failed to delete file from Dropbox: {e}")
            raise Exception(f"Failed to delete file from Dropbox: {str(e)}")

