"""
Google Photos API integration provider
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import CloudStorageProvider

class GooglePhotosProvider(CloudStorageProvider):
    """Google Photos API integration"""
    
    def __init__(self, access_token: str, refresh_token: str = None, client_id: str = None, client_secret: str = None):
        super().__init__(access_token, refresh_token)
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://photoslibrary.googleapis.com/v1"
    
    def get_provider_name(self) -> str:
        return "google_photos"
    
    async def refresh_access_token(self) -> bool:
        """Refresh access token using Google OAuth"""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://oauth2.googleapis.com/token',
                    data={
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'refresh_token': self.refresh_token,
                        'grant_type': 'refresh_token'
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.access_token = data['access_token']
                        return True
        except Exception as e:
            print(f"Failed to refresh Google Photos token: {e}")
        
        return False
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get Google Photos user information"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://www.googleapis.com/oauth2/v1/userinfo',
                    headers={'Authorization': f'Bearer {self.access_token}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'email': data.get('email'),
                            'name': data.get('name'),
                            'storage_used': 0,  # Google Photos doesn't provide this in the basic API
                            'storage_limit': 0
                        }
        except Exception as e:
            print(f"Failed to get Google Photos user info: {e}")
        
        return {}
    
    async def list_files(self, page_token: str = None, max_results: int = 100) -> Dict[str, Any]:
        """List photos and videos from Google Photos"""
        try:
            params = {
                'pageSize': min(max_results, 100)
            }
            
            if page_token:
                params['pageToken'] = page_token
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/mediaItems",
                    headers={'Authorization': f'Bearer {self.access_token}'},
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        files = []
                        
                        for item in data.get('mediaItems', []):
                            normalized_file = self.normalize_google_photos_metadata(item)
                            files.append(normalized_file)
                        
                        return {
                            'files': files,
                            'next_page_token': data.get('nextPageToken')
                        }
        except Exception as e:
            print(f"Failed to list Google Photos files: {e}")
        
        return {'files': [], 'next_page_token': None}
    
    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a specific Google Photos item"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/mediaItems/{file_id}",
                    headers={'Authorization': f'Bearer {self.access_token}'}
                ) as response:
                    if response.status == 200:
                        item = await response.json()
                        return self.normalize_google_photos_metadata(item)
        except Exception as e:
            print(f"Failed to get Google Photos file metadata: {e}")
        
        return {}
    
    def normalize_google_photos_metadata(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Google Photos item metadata"""
        metadata = item.get('mediaMetadata', {})
        
        # Determine file type
        mime_type = item.get('mimeType', '')
        is_video = mime_type.startswith('video/')
        
        # Get creation time
        creation_time = metadata.get('creationTime')
        created_at = None
        if creation_time:
            try:
                created_at = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
            except:
                pass
        
        # Build base URLs (Google Photos uses specific URL patterns)
        base_url = item.get('baseUrl', '')
        
        # Create different sized URLs
        preview_url = f"{base_url}=w800-h600" if base_url else None
        thumbnail_url = f"{base_url}=w200-h200" if base_url else None
        download_url = f"{base_url}=d" if base_url else None  # Download original
        
        return {
            'provider_file_id': item['id'],
            'name': item.get('filename', 'Unknown'),
            'path': '/',  # Google Photos doesn't have traditional folder structure
            'size': None,  # Size info not provided in basic API
            'mime_type': mime_type,
            'file_extension': self.get_file_extension(item.get('filename', ''), mime_type),
            'created_at': created_at,
            'modified_at': created_at,  # Google Photos uses creation time
            'preview_link': preview_url,
            'download_link': download_url,
            'web_view_link': item.get('productUrl'),
            'thumbnail_link': thumbnail_url,
            'content_hash': None,  # Not provided by Google Photos API
            'is_video': is_video,
            'is_image': not is_video,
            'width': metadata.get('width'),
            'height': metadata.get('height'),
            'photo_metadata': metadata.get('photo', {}),
            'video_metadata': metadata.get('video', {}) if is_video else None
        }
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a photo/video from Google Photos"""
        # Note: Google Photos API doesn't support deletion through the API
        # This would require the user to delete manually through the web interface
        raise NotImplementedError("Google Photos API doesn't support deletion through the API")
    
    async def upload_file(self, file_name: str, file_content: bytes, folder_path: str = "/", mime_type: str = None) -> Dict[str, Any]:
        """Upload a file to Google Photos"""
        try:
            # Step 1: Upload the raw bytes
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/uploads",
                    headers={
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/octet-stream',
                        'X-Goog-Upload-File-Name': file_name,
                        'X-Goog-Upload-Protocol': 'raw'
                    },
                    data=file_content
                ) as upload_response:
                    if upload_response.status != 200:
                        raise Exception(f"Upload failed with status {upload_response.status}")
                    
                    upload_token = await upload_response.text()
            
            # Step 2: Create media item
            create_request = {
                "newMediaItems": [
                    {
                        "description": f"Uploaded via Unified Cloud Storage",
                        "simpleMediaItem": {
                            "fileName": file_name,
                            "uploadToken": upload_token
                        }
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/mediaItems:batchCreate",
                    headers={
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json'
                    },
                    json=create_request
                ) as create_response:
                    if create_response.status == 200:
                        data = await create_response.json()
                        if data.get('newMediaItemResults'):
                            result = data['newMediaItemResults'][0]
                            if result.get('status', {}).get('code') == 0:  # Success
                                media_item = result['mediaItem']
                                return self.normalize_google_photos_metadata(media_item)
                            else:
                                raise Exception(f"Create media item failed: {result.get('status', {}).get('message')}")
                    else:
                        raise Exception(f"Create media item failed with status {create_response.status}")
        
        except Exception as e:
            print(f"Failed to upload to Google Photos: {e}")
            raise
    
    async def get_preview_link(self, file_id: str) -> Optional[str]:
        """Get preview link for a Google Photos item"""
        try:
            file_metadata = await self.get_file_metadata(file_id)
            return file_metadata.get('preview_link')
        except Exception as e:
            print(f"Failed to get Google Photos preview link: {e}")
            return None
    
    @classmethod
    async def exchange_code_for_token(cls, code: str, client_id: str, client_secret: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://oauth2.googleapis.com/token',
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
            print(f"Failed to exchange code for Google Photos token: {e}")
            raise
    
    @classmethod
    def get_authorization_url(cls, client_id: str, redirect_uri: str, state: str) -> str:
        """Get OAuth authorization URL for Google Photos"""
        scopes = [
            'https://www.googleapis.com/auth/photoslibrary.readonly',
            'https://www.googleapis.com/auth/photoslibrary.appendonly',  # For uploads
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        
        scope_str = ' '.join(scopes)
        
        return (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope_str}&"
            f"response_type=code&"
            f"access_type=offline&"
            f"prompt=consent&"
            f"state={state}"
        )
