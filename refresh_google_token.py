"""
Script to manually refresh Google Drive tokens
"""
from backend.database import SessionLocal
from backend.models import StorageAccount
from backend.storage_providers import GoogleDriveProvider
from backend.utils import SecurityUtils
from backend.config import PROVIDER_CONFIGS
import asyncio

async def refresh_tokens(account_id: int):
    db = SessionLocal()
    security_utils = SecurityUtils()
    
    try:
        account = db.query(StorageAccount).filter(StorageAccount.id == account_id).first()
        if not account:
            print(f"❌ Account {account_id} not found")
            return
        
        print(f"📱 Refreshing tokens for: {account.provider} - {account.account_email}")
        
        # Get provider config
        mode_key = f"{account.provider}_{account.mode}"
        provider_config = PROVIDER_CONFIGS.get(mode_key)
        
        if not provider_config:
            print(f"❌ No config found for {mode_key}")
            return
        
        # Decrypt tokens
        access_token = security_utils.decrypt_token(account.access_token)
        refresh_token = security_utils.decrypt_token(account.refresh_token) if account.refresh_token else None
        
        if not refresh_token:
            print("❌ No refresh token available. Please reconnect the account.")
            return
        
        # Create provider instance
        provider = GoogleDriveProvider(
            access_token=access_token,
            refresh_token=refresh_token,
            client_id=provider_config['client_id'],
            client_secret=provider_config['client_secret'],
            mode=account.mode,
            db_session=db,
            storage_account_id=account.id
        )
        
        # Try to refresh
        print("🔄 Attempting token refresh...")
        success = await provider.refresh_access_token()
        
        if success:
            print("✅ Token refreshed successfully!")
            db.refresh(account)
            print(f"   New expiry: {account.token_expires_at}")
        else:
            print("❌ Token refresh failed. Please reconnect the account.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    # Refresh all Google Drive accounts for user 1
    db = SessionLocal()
    accounts = db.query(StorageAccount).filter(
        StorageAccount.user_id == 1,
        StorageAccount.provider == 'google_drive'
    ).all()
    db.close()
    
    for account in accounts:
        print(f"\n{'='*60}")
        asyncio.run(refresh_tokens(account.id))
