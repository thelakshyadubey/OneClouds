import asyncio
from backend.database import SessionLocal
from backend.models import StorageAccount
from backend.storage_providers import get_provider_class
from backend.config import PROVIDER_CONFIGS
from backend.utils import SecurityUtils

async def test_list_files():
    db = SessionLocal()
    security_utils = SecurityUtils()
    
    # Get the full_access account
    account = db.query(StorageAccount).filter(StorageAccount.mode == "full_access").first()
    
    if not account:
        print("No full_access account found")
        return
    
    print(f"Testing account: {account.account_email} ({account.provider} - {account.mode})")
    
    # Get provider class
    provider_class = get_provider_class(account.provider)
    
    # Get config
    config_key = f"{account.provider}_{account.mode}"
    print(f"Config key: {config_key}")
    
    if config_key not in PROVIDER_CONFIGS:
        print(f"ERROR: Config not found for {config_key}")
        print(f"Available configs: {list(PROVIDER_CONFIGS.keys())}")
        return
    
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
    
    print("Fetching files...")
    result = await provider.list_files()
    
    if result and "files" in result:
        print(f"\nFound {len(result['files'])} files")
        for file in result['files'][:3]:  # Show first 3 files
            print(f"\nFile: {file['name']}")
            print(f"  web_view_link: {file.get('web_view_link', 'NOT PRESENT')}")
            print(f"  preview_link: {file.get('preview_link', 'NOT PRESENT')}")
    else:
        print(f"ERROR: Unexpected result: {result}")

if __name__ == "__main__":
    asyncio.run(test_list_files())
