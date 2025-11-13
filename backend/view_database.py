"""
Database Viewer - Show what data is stored in OneClouds database
Run this script to see the contents of your database tables
"""

import sys
import os
from datetime import datetime

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Base, get_db
from backend.models import User, StorageAccount, FileMetadata, SyncLog, UserSession, TrustedDevice, Job, UserPreferences
from backend.config import Settings

settings = Settings()

def mask_sensitive_data(value, field_name):
    """Mask sensitive data for display"""
    sensitive_fields = ['password', 'token', 'secret', 'otp']
    if any(field in field_name.lower() for field in sensitive_fields):
        if value and len(str(value)) > 8:
            return f"{str(value)[:4]}...{str(value)[-4:]}"
        return "***MASKED***"
    return value

def format_value(value):
    """Format values for display"""
    if value is None:
        return "NULL"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        return str(value)
    return str(value)

def view_table(db, model, table_name, limit=10):
    """View contents of a specific table"""
    print(f"\n{'='*100}")
    print(f"TABLE: {table_name}")
    print(f"{'='*100}")
    
    # Get column names
    columns = [column.name for column in model.__table__.columns]
    
    # Get records
    records = db.query(model).limit(limit).all()
    
    if not records:
        print("No records found.")
        return
    
    print(f"\nTotal records (showing first {limit}): {db.query(model).count()}")
    print(f"\nColumns: {', '.join(columns)}")
    print("-" * 100)
    
    # Display records
    for i, record in enumerate(records, 1):
        print(f"\nRecord {i}:")
        for col in columns:
            value = getattr(record, col)
            masked_value = mask_sensitive_data(value, col)
            formatted_value = format_value(masked_value)
            print(f"  {col:25s}: {formatted_value}")

def show_database_summary(db):
    """Show summary statistics for all tables"""
    print("\n" + "="*100)
    print("DATABASE SUMMARY - OneClouds")
    print("="*100)
    
    tables = [
        (User, "users", "Registered Users"),
        (StorageAccount, "storage_accounts", "Connected Cloud Accounts"),
        (FileMetadata, "file_metadata", "Synced Files"),
        (SyncLog, "sync_logs", "Sync Operations"),
        (UserSession, "user_sessions", "Active Sessions"),
        (TrustedDevice, "trusted_devices", "Trusted Devices"),
        (Job, "jobs", "Background Jobs"),
        (UserPreferences, "user_preferences", "User Preferences"),
    ]
    
    print(f"\n{'Table':<30} {'Description':<35} {'Record Count':<15}")
    print("-" * 100)
    
    for model, table_name, description in tables:
        count = db.query(model).count()
        print(f"{table_name:<30} {description:<35} {count:<15}")

def main():
    """Main function to display database contents"""
    print("\n" + "="*100)
    print(" OneClouds Database Viewer ".center(100, "="))
    print("="*100)
    print(f"\nDatabase: {settings.DATABASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create database session
    db = next(get_db())
    
    try:
        # Show summary
        show_database_summary(db)
        
        # Show detailed data for each table
        print("\n\n" + "="*100)
        print(" DETAILED TABLE DATA ".center(100, "="))
        print("="*100)
        
        view_table(db, User, "Users", limit=5)
        view_table(db, StorageAccount, "Storage Accounts", limit=5)
        view_table(db, FileMetadata, "File Metadata", limit=10)
        view_table(db, SyncLog, "Sync Logs", limit=5)
        view_table(db, UserSession, "User Sessions", limit=5)
        view_table(db, TrustedDevice, "Trusted Devices", limit=5)
        view_table(db, Job, "Background Jobs", limit=5)
        view_table(db, UserPreferences, "User Preferences", limit=5)
        
        # Show what data we store and why
        print("\n\n" + "="*100)
        print(" DATA STORAGE EXPLANATION ".center(100, "="))
        print("="*100)
        
        print("""
DATA WE STORE:

1. USER DATA (users table):
   - Email, Name, Password (hashed)
   - Account mode preference (metadata/full_access)
   - Login security (failed attempts, lockout time)
   - 2FA settings (if enabled)
   - Timestamps (registration, last login)
   
   WHY: To authenticate users and manage their accounts securely

2. STORAGE ACCOUNTS (storage_accounts table):
   - Connected cloud providers (Google Drive, Dropbox, OneDrive)
   - Access tokens (ENCRYPTED) for API access
   - Account email and name
   - Storage usage statistics
   - Last sync timestamp
   
   WHY: To connect to your cloud storage accounts and sync files

3. FILE METADATA (file_metadata table):
   - File names, paths, sizes
   - File types and extensions
   - Timestamps (created, modified)
   - Web view links (for preview)
   - Content hashes (for duplicate detection)
   
   WHY: To show your files, find duplicates, and provide search
   NOTE: We DO NOT store actual file contents, only metadata

4. SYNC LOGS (sync_logs table):
   - Sync operation history
   - Files processed, added, updated, deleted
   - Error logs
   
   WHY: To track sync operations and troubleshoot issues

5. USER SESSIONS (user_sessions table):
   - Active login sessions
   - Session tokens and expiry
   - IP address and user agent
   
   WHY: To maintain secure login sessions

6. TRUSTED DEVICES (trusted_devices table):
   - Device fingerprints for 2FA
   - Device names and last used time
   
   WHY: To remember trusted devices for 2FA

7. BACKGROUND JOBS (jobs table):
   - Async tasks (migrations, syncs)
   - Job status and progress
   
   WHY: To manage long-running operations

8. USER PREFERENCES (user_preferences table):
   - User settings and preferences (JSON)
   
   WHY: To save user customization

SECURITY NOTES:
- All passwords are hashed (not stored in plain text)
- All access tokens are encrypted
- No actual file contents are stored
- Only metadata is kept for file management
""")
        
    finally:
        db.close()
    
    print("\n" + "="*100)
    print(" END OF DATABASE REPORT ".center(100, "="))
    print("="*100 + "\n")

if __name__ == "__main__":
    main()
