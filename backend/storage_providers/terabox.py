"""
Terabox API integration provider
Note: Terabox has limited API documentation, this is a basic implementation
that may need adjustment based on actual API behavior
"""

import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import CloudStorageProvider

class TeraboxProvider(CloudStorageProvider):
    """Terabox API integration (limited support)"""
    
    def __init__(self, access_token: str, refresh_token: str = None, client_id: str = None, client_secret: str = None):
        super().__init__(access_token, refresh_token)
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.terabox.com"
    
    def get_provider_name(self) -> str:
        return "terabox"
    
    async def refresh_access_token(self) -> bool:
        """Refresh access token using Terabox OAuth"""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/oauth/token",
                    data={
                        'grant_type': 'refresh_token',
                        'refresh_token': self.refresh_token,
                        'client_id': self.client_id,
                        'client_secret': self.client_secret
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'access_token' in data:
                            self.access_token = data['access_token']
                            return True
        except Exception as e:
            print(f"Failed to refresh Terabox token: {e}")
        
        return False
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get Terabox user information"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/user/info",
                    headers={'Authorization': f'Bearer {self.access_token}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'email': data.get('email', 'Unknown'),
                            'name': data.get('username', 'Terabox User'),
                            'storage_used': data.get('used_space', 0),
                            'storage_limit': data.get('total_space', 0)
                        }
        except Exception as e:
            print(f"Failed to get Terabox user info: {e}")
        
        return {}
    
    async def list_files(self, page_token: str = None, max_results: int = 100) -> Dict[str, Any]:
        """List files from Terabox"""
        try:
            params = {
                'limit': min(max_results, 100),
                'folder': '/',  # Start from root
            }
            
            if page_token:
                params['offset'] = page_token
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/file/list",
                    headers={'Authorization': f'Bearer {self.access_token}'},
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        files = []
                        
                        for item in data.get('files', []):
                            # Skip folders if they have a type indicator
                            if item.get('isdir', False):
                                continue
                            
                            normalized_file = self.normalize_terabox_metadata(item)
                            files.append(normalized_file)
                        
                        # Calculate next page token
                        next_page_token = None
                        if len(files) == max_results:
                            current_offset = int(page_token) if page_token else 0
                            next_page_token = str(current_offset + max_results)
                        
                        return {
                            'files': files,
                            'next_page_token': next_page_token
                        }
        except Exception as e:
            print(f"Failed to list Terabox files: {e}")
        
        return {'files': [], 'next_page_token': None}
    
    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a specific Terabox file"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/file/info",
                    headers={'Authorization': f'Bearer {self.access_token}'},
                    params={'file_id': file_id}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'file' in data:
                            return self.normalize_terabox_metadata(data['file'])
        except Exception as e:
            print(f"Failed to get Terabox file metadata: {e}")
        
        return {}
    
    def normalize_terabox_metadata(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Terabox file metadata"""
        # Parse timestamps
        created_at = None
        modified_at = None
        
        if item.get('create_time'):
            try:
                created_at = datetime.fromtimestamp(int(item['create_time']))
            except:
                pass
        
        if item.get('modify_time'):
            try:
                modified_at = datetime.fromtimestamp(int(item['modify_time']))
            except:
                pass
        
        # Build download and preview URLs
        download_url = item.get('download_url')
        preview_url = item.get('preview_url')
        web_view_url = item.get('web_url')
        
        return {
            'provider_file_id': str(item.get('fs_id', item.get('file_id', ''))),
            'name': item.get('server_filename', item.get('filename', 'Unknown')),
            'path': item.get('path', '/'),
            'size': item.get('size'),
            'mime_type': self.guess_mime_type(item.get('server_filename', '')),
            'file_extension': self.get_file_extension(item.get('server_filename', '')),
            'created_at': created_at,
            'modified_at': modified_at,
            'preview_link': preview_url,
            'download_link': download_url,
            'web_view_link': web_view_url,
            'thumbnail_link': item.get('thumbs', {}).get('url3') if item.get('thumbs') else None,
            'content_hash': item.get('md5')
        }
    
    def guess_mime_type(self, filename: str) -> str:
        """Guess MIME type from filename since Terabox might not provide it"""
        if not filename:
            return 'application/octet-stream'
        
        ext = self.get_file_extension(filename).lower()
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
            'avi': 'video/x-msvideo',
            'mp3': 'audio/mpeg',
            'zip': 'application/zip'
        }
        
        return mime_types.get(ext, 'application/octet-stream')
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from Terabox"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/file/delete",
                    headers={'Authorization': f'Bearer {self.access_token}'},
                    json={'file_ids': [file_id]}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('success', False)
        except Exception as e:
            print(f"Failed to delete Terabox file: {e}")
        
        return False
    
    async def upload_file(self, file_name: str, file_content: bytes, folder_path: str = "/", mime_type: str = None) -> Dict[str, Any]:
        """Upload a file to Terabox"""
        try:
            # This is a simplified implementation
            # Actual Terabox upload might require multi-step process
            
            form_data = aiohttp.FormData()
            form_data.add_field('file', file_content, filename=file_name, content_type=mime_type)
            form_data.add_field('path', folder_path)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/file/upload",
                    headers={'Authorization': f'Bearer {self.access_token}'},
                    data=form_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success') and 'file' in data:
                            return self.normalize_terabox_metadata(data['file'])
                    else:
                        raise Exception(f"Upload failed with status {response.status}")
        
        except Exception as e:
            print(f"Failed to upload to Terabox: {e}")
            raise
    
    async def get_preview_link(self, file_id: str) -> Optional[str]:
        """Get preview link for a Terabox file"""
        try:
            file_metadata = await self.get_file_metadata(file_id)
            return file_metadata.get('preview_link')
        except Exception as e:
            print(f"Failed to get Terabox preview link: {e}")
            return None
    
    @classmethod
    async def exchange_code_for_token(cls, code: str, client_id: str, client_secret: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://openapi.terabox.com/oauth/token',
                    data={
                        'code': code,
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'redirect_uri': redirect_uri,
                        'grant_type': 'authorization_code'
                    }
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"Token exchange failed with status {response.status}")
        except Exception as e:
            print(f"Failed to exchange code for Terabox token: {e}")
            raise
    
    @classmethod
    def get_authorization_url(cls, client_id: str, redirect_uri: str, state: str) -> str:
        """Get OAuth authorization URL for Terabox"""
        return (
            f"https://openapi.terabox.com/oauth/authorize?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"state={state}"
        )
