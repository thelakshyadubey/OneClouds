import requests
import json

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
    print(f"Login successful! Token: {token[:50]}...")
    
    # Trigger sync
    sync_response = requests.post(
        "http://127.0.0.1:8000/api/storage-accounts/sync-all",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"\nSync response status: {sync_response.status_code}")
    print(f"Sync response: {sync_response.text}")
else:
    print(f"Login failed: {login_response.status_code}")
    print(f"Response: {login_response.text}")
