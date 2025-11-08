from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config
from models import db, User, StorageAccount, FileMetadata, SyncLog
from storage_providers import get_storage_provider
from datetime import datetime, timedelta
import os
import hashlib
from typing import List, Dict, Any
import requests
from requests_oauthlib import OAuth2Session
import secrets

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    CORS(app, supports_credentials=True)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

# Utility functions
def get_current_user():
    """Get current user from session"""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if not get_current_user():
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Authentication routes
@app.route('/api/auth/google')
def google_auth():
    """Initiate Google OAuth flow"""
    google = OAuth2Session(
        app.config['GOOGLE_CLIENT_ID'],
        scope=['openid', 'email', 'profile', 'https://www.googleapis.com/auth/drive.readonly'],
        redirect_uri=app.config['GOOGLE_REDIRECT_URI']
    )
    authorization_url, state = google.authorization_url(
        'https://accounts.google.com/o/oauth2/auth',
        access_type="offline", prompt="consent"
    )
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/api/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        google = OAuth2Session(
            app.config['GOOGLE_CLIENT_ID'],
            state=session['oauth_state'],
            redirect_uri=app.config['GOOGLE_REDIRECT_URI']
        )
        
        token = google.fetch_token(
            'https://oauth2.googleapis.com/token',
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            authorization_response=request.url
        )
        
        # Get user info
        user_info_response = google.get('https://www.googleapis.com/oauth2/v1/userinfo')
        user_info = user_info_response.json()
        
        # Find or create user
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            user = User(email=user_info['email'])
            db.session.add(user)
            db.session.commit()
        
        # Store or update storage account
        storage_account = StorageAccount.query.filter_by(
            user_id=user.id,
            provider='google_drive',
            account_email=user_info['email']
        ).first()
        
        if not storage_account:
            storage_account = StorageAccount(
                user_id=user.id,
                provider='google_drive',
                account_email=user_info['email'],
                access_token=token['access_token'],
                refresh_token=token.get('refresh_token'),
                token_expires_at=datetime.utcnow() + timedelta(seconds=token.get('expires_in', 3600))
            )
            db.session.add(storage_account)
        else:
            storage_account.access_token = token['access_token']
            if token.get('refresh_token'):
                storage_account.refresh_token = token['refresh_token']
            storage_account.token_expires_at = datetime.utcnow() + timedelta(seconds=token.get('expires_in', 3600))
            storage_account.is_active = True
        
        db.session.commit()
        session['user_id'] = user.id
        
        # Redirect to frontend
        return redirect('http://localhost:3000/dashboard?auth=success')
    
    except Exception as e:
        print(f"Google auth error: {e}")
        return redirect('http://localhost:3000/dashboard?auth=error')

@app.route('/api/auth/dropbox')
def dropbox_auth():
    """Initiate Dropbox OAuth flow"""
    dropbox_oauth = OAuth2Session(
        app.config['DROPBOX_CLIENT_ID'],
        redirect_uri=app.config['DROPBOX_REDIRECT_URI']
    )
    authorization_url, state = dropbox_oauth.authorization_url(
        'https://www.dropbox.com/oauth2/authorize'
    )
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/api/auth/dropbox/callback')
def dropbox_callback():
    """Handle Dropbox OAuth callback"""
    try:
        token_response = requests.post(
            'https://api.dropboxapi.com/oauth2/token',
            data={
                'code': request.args.get('code'),
                'grant_type': 'authorization_code',
                'client_id': app.config['DROPBOX_CLIENT_ID'],
                'client_secret': app.config['DROPBOX_CLIENT_SECRET'],
                'redirect_uri': app.config['DROPBOX_REDIRECT_URI']
            }
        )
        
        if token_response.status_code == 200:
            token = token_response.json()
            
            # Get user info using the token
            provider = get_storage_provider(
                'dropbox',
                token['access_token'],
                token.get('refresh_token'),
                client_id=app.config['DROPBOX_CLIENT_ID'],
                client_secret=app.config['DROPBOX_CLIENT_SECRET']
            )
            
            user_info = provider.get_user_info()
            
            # Find or create user
            user = User.query.filter_by(email=user_info['email']).first()
            if not user:
                user = User(email=user_info['email'])
                db.session.add(user)
                db.session.commit()
            
            # Store storage account
            storage_account = StorageAccount.query.filter_by(
                user_id=user.id,
                provider='dropbox',
                account_email=user_info['email']
            ).first()
            
            if not storage_account:
                storage_account = StorageAccount(
                    user_id=user.id,
                    provider='dropbox',
                    account_email=user_info['email'],
                    access_token=token['access_token'],
                    refresh_token=token.get('refresh_token'),
                    token_expires_at=datetime.utcnow() + timedelta(seconds=token.get('expires_in', 3600))
                )
                db.session.add(storage_account)
            else:
                storage_account.access_token = token['access_token']
                if token.get('refresh_token'):
                    storage_account.refresh_token = token['refresh_token']
                storage_account.is_active = True
            
            db.session.commit()
            session['user_id'] = user.id
            
            return redirect('http://localhost:3000/dashboard?auth=success')
    
    except Exception as e:
        print(f"Dropbox auth error: {e}")
    
    return redirect('http://localhost:3000/dashboard?auth=error')

# API Routes
@app.route('/api/user')
@require_auth
def get_user():
    """Get current user information"""
    user = get_current_user()
    return jsonify(user.to_dict())

@app.route('/api/storage-accounts')
@require_auth
def get_storage_accounts():
    """Get user's connected storage accounts"""
    user = get_current_user()
    accounts = [account.to_dict() for account in user.storage_accounts]
    return jsonify(accounts)

@app.route('/api/storage-accounts/<int:account_id>/sync', methods=['POST'])
@require_auth
def sync_storage_account(account_id):
    """Sync files from a specific storage account"""
    user = get_current_user()
    
    # Get the storage account
    storage_account = StorageAccount.query.filter_by(
        id=account_id,
        user_id=user.id
    ).first()
    
    if not storage_account:
        return jsonify({'error': 'Storage account not found'}), 404
    
    try:
        # Create provider instance
        provider = get_storage_provider(
            storage_account.provider,
            storage_account.access_token,
            storage_account.refresh_token,
            client_id=get_client_id(storage_account.provider),
            client_secret=get_client_secret(storage_account.provider)
        )
        
        # Create sync log
        sync_log = SyncLog(
            user_id=user.id,
            storage_account_id=storage_account.id
        )
        db.session.add(sync_log)
        db.session.commit()
        
        # Sync files
        files_added = 0
        files_updated = 0
        page_token = None
        
        while True:
            result = provider.list_files(
                page_token=page_token,
                max_results=100
            )
            
            files = result.get('files', [])
            page_token = result.get('next_page_token')
            
            for file_data in files:
                existing_file = FileMetadata.query.filter_by(
                    user_id=user.id,
                    storage_account_id=storage_account.id,
                    provider_file_id=file_data['provider_file_id']
                ).first()
                
                if existing_file:
                    # Update existing file
                    update_file_metadata(existing_file, file_data)
                    files_updated += 1
                else:
                    # Create new file
                    new_file = create_file_metadata(user.id, storage_account.id, file_data)
                    db.session.add(new_file)
                    files_added += 1
            
            sync_log.files_processed += len(files)
            db.session.commit()
            
            if not page_token:
                break
        
        # Update sync log
        sync_log.sync_completed_at = datetime.utcnow()
        sync_log.files_added = files_added
        sync_log.files_updated = files_updated
        sync_log.status = 'completed'
        
        # Update storage account sync time
        storage_account.last_sync = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Sync completed successfully',
            'files_added': files_added,
            'files_updated': files_updated,
            'files_processed': sync_log.files_processed
        })
    
    except Exception as e:
        sync_log.status = 'failed'
        sync_log.error_details = str(e)
        sync_log.sync_completed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'error': f'Sync failed: {str(e)}'}), 500

@app.route('/api/files')
@require_auth
def get_files():
    """Get user's files with filtering and sorting"""
    user = get_current_user()
    
    # Get query parameters
    provider = request.args.get('provider')
    sort_by = request.args.get('sort_by', 'modified_at_source')
    sort_order = request.args.get('sort_order', 'desc')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    search = request.args.get('search', '')
    
    # Build query
    query = FileMetadata.query.filter_by(user_id=user.id)
    
    if provider:
        query = query.join(StorageAccount).filter(StorageAccount.provider == provider)
    
    if search:
        query = query.filter(FileMetadata.name.contains(search))
    
    # Apply sorting
    if sort_by in ['name', 'size', 'created_at_source', 'modified_at_source']:
        order_column = getattr(FileMetadata, sort_by)
        if sort_order == 'desc':
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
    
    # Paginate
    files = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'files': [file.to_dict() for file in files.items],
        'total': files.total,
        'pages': files.pages,
        'current_page': page,
        'has_next': files.has_next,
        'has_prev': files.has_prev
    })

@app.route('/api/duplicates')
@require_auth
def get_duplicates():
    """Get duplicate files"""
    user = get_current_user()
    
    # Find files with same size_hash that have duplicates
    duplicates = db.session.query(FileMetadata.size_hash, db.func.count(FileMetadata.id).label('count'))\
        .filter_by(user_id=user.id)\
        .group_by(FileMetadata.size_hash)\
        .having(db.func.count(FileMetadata.id) > 1)\
        .all()
    
    duplicate_groups = []
    for size_hash, count in duplicates:
        if size_hash:  # Only include files that have a hash
            files = FileMetadata.query.filter_by(
                user_id=user.id,
                size_hash=size_hash
            ).all()
            
            duplicate_groups.append({
                'size_hash': size_hash,
                'count': count,
                'files': [file.to_dict() for file in files]
            })
    
    return jsonify(duplicate_groups)

@app.route('/api/duplicates/remove', methods=['POST'])
@require_auth
def remove_duplicates():
    """Remove duplicate files (keep only one copy)"""
    user = get_current_user()
    data = request.get_json()
    
    file_ids_to_remove = data.get('file_ids', [])
    
    if not file_ids_to_remove:
        return jsonify({'error': 'No file IDs provided'}), 400
    
    try:
        removed_count = 0
        for file_id in file_ids_to_remove:
            file_to_remove = FileMetadata.query.filter_by(
                id=file_id,
                user_id=user.id
            ).first()
            
            if file_to_remove:
                db.session.delete(file_to_remove)
                removed_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Removed {removed_count} duplicate files',
            'removed_count': removed_count
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to remove duplicates: {str(e)}'}), 500

# Helper functions
def get_client_id(provider):
    """Get client ID for provider"""
    mapping = {
        'google_drive': app.config.get('GOOGLE_CLIENT_ID'),
        'dropbox': app.config.get('DROPBOX_CLIENT_ID'),
        'onedrive': app.config.get('MICROSOFT_CLIENT_ID')
    }
    return mapping.get(provider)

def get_client_secret(provider):
    """Get client secret for provider"""
    mapping = {
        'google_drive': app.config.get('GOOGLE_CLIENT_SECRET'),
        'dropbox': app.config.get('DROPBOX_CLIENT_SECRET'),
        'onedrive': app.config.get('MICROSOFT_CLIENT_SECRET')
    }
    return mapping.get(provider)

def create_file_metadata(user_id, storage_account_id, file_data):
    """Create FileMetadata instance from provider data"""
    file_metadata = FileMetadata(
        user_id=user_id,
        storage_account_id=storage_account_id,
        provider_file_id=file_data['provider_file_id'],
        name=file_data['name'],
        path=file_data.get('path'),
        size=file_data.get('size'),
        mime_type=file_data.get('mime_type'),
        file_extension=file_data.get('file_extension'),
        created_at_source=file_data.get('created_at'),
        modified_at_source=file_data.get('modified_at'),
        preview_link=file_data.get('preview_link'),
        download_link=file_data.get('download_link'),
        web_view_link=file_data.get('web_view_link'),
        content_hash=file_data.get('content_hash')
    )
    return file_metadata

def update_file_metadata(existing_file, file_data):
    """Update existing FileMetadata with new data"""
    existing_file.name = file_data['name']
    existing_file.path = file_data.get('path')
    existing_file.size = file_data.get('size')
    existing_file.mime_type = file_data.get('mime_type')
    existing_file.file_extension = file_data.get('file_extension')
    existing_file.modified_at_source = file_data.get('modified_at')
    existing_file.preview_link = file_data.get('preview_link')
    existing_file.download_link = file_data.get('download_link')
    existing_file.web_view_link = file_data.get('web_view_link')
    existing_file.content_hash = file_data.get('content_hash')
    existing_file.updated_at = datetime.utcnow()
    
    # Update size hash if size or name changed
    if existing_file.name and existing_file.size:
        existing_file.size_hash = existing_file.generate_size_hash()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
