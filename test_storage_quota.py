import asyncio
from backend.database import SessionLocal
from backend.models import StorageAccount
from backend.storage_providers import get_provider_class
from backend.config import PROVIDER_CONFIGS
from backend.utils import SecurityUtils

async def test_storage_quota():
    db = SessionLocal()
    security_utils = SecurityUtils()
    
    # Test both accounts
    accounts = db.query(StorageAccount).all()
    
    for account in accounts:
        print(f"\n{'='*60}")
        print(f"Testing: {account.account_email} ({account.provider} - {account.mode})")
        print(f"Current DB values: limit={account.storage_limit}, used={account.storage_used}")
        
        # Get provider class
        provider_class = get_provider_class(account.provider)
        
        # Get config
        config_key = f"{account.provider}_{account.mode}"
        
        if config_key not in PROVIDER_CONFIGS:
            print(f"ERROR: Config not found for {config_key}")
            continue
        
        # Create provider instance
        provider = provider_class(
            access_token=security_utils.decrypt_token(account.access_token),
            refresh_token=security_utils.decrypt_token(account.refresh_token) if account.refresh_token else None,
            mode=account.mode,
            client_id=PROVIDER_CONFIGS[config_key]["client_id"],
            client_secret=PROVIDER_CONFIGS[config_key]["client_secret"],
            db_session=db,
            storage_account_id=account.id
        )
        
        print("\nFetching storage quota from API...")
        try:
            quota = await provider.get_storage_quota()
            print(f"API Response: {quota}")
            
            # Convert to GB for readability
            if quota:
                total_gb = quota.get('total', 0) / (1024**3)
                used_gb = quota.get('used', 0) / (1024**3)
                remaining_gb = quota.get('remaining', 0) / (1024**3)
                print(f"Total: {total_gb:.2f} GB")
                print(f"Used: {used_gb:.2f} GB")
                print(f"Remaining: {remaining_gb:.2f} GB")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_storage_quota())
