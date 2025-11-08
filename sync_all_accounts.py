import requests

# Login
login_response = requests.post(
    "http://127.0.0.1:8000/api/auth/login",
    json={
        "email": "lakshya.dubey10@gmail.com",
        "password": "password123"
    }
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"Login successful!")
    
    # Get accounts
    accounts_response = requests.get(
        "http://127.0.0.1:8000/api/storage-accounts",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if accounts_response.status_code == 200:
        accounts = accounts_response.json()
        print(f"\nFound {len(accounts)} accounts")
        
        # Sync each account
        for account in accounts:
            print(f"\nSyncing {account['account_email']} (ID: {account['id']})...")
            sync_response = requests.post(
                f"http://127.0.0.1:8000/api/storage-accounts/{account['id']}/sync",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"  Status: {sync_response.status_code}")
            if sync_response.status_code == 200:
                print(f"  {sync_response.json()['message']}")
            else:
                print(f"  Error: {sync_response.text}")
    else:
        print(f"Failed to get accounts: {accounts_response.status_code}")
        print(accounts_response.text)
else:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
