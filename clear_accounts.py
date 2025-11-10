"""
Script to remove all linked storage accounts from the database
"""
import sys
sys.path.append('backend')

from backend.database import SessionLocal
from backend.models import StorageAccount, FileMetadata

def clear_all_accounts():
    db = SessionLocal()
    try:
        # First, delete all file metadata
        file_count = db.query(FileMetadata).count()
        db.query(FileMetadata).delete()
        print(f"✅ Deleted {file_count} file metadata records")
        
        # Then, delete all storage accounts
        account_count = db.query(StorageAccount).count()
        db.query(StorageAccount).delete()
        print(f"✅ Deleted {account_count} storage accounts")
        
        db.commit()
        print("\n🎉 Successfully cleared all linked accounts from the database!")
        print("You can now connect fresh accounts from the Accounts page.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing accounts: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    confirm = input("⚠️  This will remove ALL linked storage accounts and their file metadata. Continue? (yes/no): ")
    if confirm.lower() == 'yes':
        clear_all_accounts()
    else:
        print("Operation cancelled.")
