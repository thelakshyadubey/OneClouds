#!/usr/bin/env python3
"""
Test script to validate backend setup and functionality
"""

import sys
import os
from datetime import datetime

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from config import settings
        print("✅ Config module imported successfully")
        
        from database import engine, Base, get_db
        print("✅ Database module imported successfully")
        
        from models import User, StorageAccount, FileMetadata, SyncLog, UserSession
        print("✅ Models imported successfully")
        
        from auth import create_access_token, verify_token
        print("✅ Auth module imported successfully")
        
        from utils import SecurityUtils, FileUtils
        print("✅ Utils module imported successfully")
        
        from storage_providers import get_provider_class, SUPPORTED_PROVIDERS
        print("✅ Storage providers imported successfully")
        
        print(f"   Supported providers: {SUPPORTED_PROVIDERS}")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    """Test database connection and table creation"""
    print("\n🗄️ Testing database...")
    
    try:
        from database import engine, Base
        from models import User, StorageAccount, FileMetadata
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Test database connection
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_security():
    """Test security utilities"""
    print("\n🔒 Testing security...")
    
    try:
        from utils import SecurityUtils
        from auth import create_access_token, verify_token
        
        # Test token encryption
        security_utils = SecurityUtils()
        test_token = "test_access_token_12345"
        encrypted = security_utils.encrypt_token(test_token)
        decrypted = security_utils.decrypt_token(encrypted)
        
        if decrypted == test_token:
            print("✅ Token encryption/decryption working")
        else:
            print("❌ Token encryption/decryption failed")
            return False
        
        # Test JWT tokens
        jwt_token = create_access_token({"user_id": 1})
        payload = verify_token(jwt_token)
        
        if payload and payload.get("user_id") == 1:
            print("✅ JWT token creation/verification working")
        else:
            print("❌ JWT token creation/verification failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Security error: {e}")
        return False

def test_providers():
    """Test cloud provider classes"""
    print("\n☁️ Testing cloud providers...")
    
    try:
        from storage_providers import get_provider_class, SUPPORTED_PROVIDERS
        
        for provider in SUPPORTED_PROVIDERS:
            try:
                provider_class = get_provider_class(provider)
                print(f"✅ {provider}: {provider_class.__name__}")
            except Exception as e:
                print(f"❌ {provider}: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Provider error: {e}")
        return False

def test_configuration():
    """Test configuration settings"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from config import settings
        
        print(f"✅ Database URL: {settings.DATABASE_URL}")
        print(f"✅ Frontend URL: {settings.FRONTEND_URL}")
        print(f"✅ Backend URL: {settings.BACKEND_URL}")
        print(f"✅ Debug mode: {settings.DEBUG}")
        print(f"✅ Max requests per minute: {settings.MAX_REQUESTS_PER_MINUTE}")
        
        # Check if any provider credentials are configured
        providers_configured = []
        if settings.GOOGLE_DRIVE_CLIENT_ID:
            providers_configured.append("Google Drive")
        if settings.GOOGLE_PHOTOS_CLIENT_ID:
            providers_configured.append("Google Photos")
        if settings.DROPBOX_CLIENT_ID:
            providers_configured.append("Dropbox")
        if settings.ONEDRIVE_CLIENT_ID:
            providers_configured.append("OneDrive")
        if settings.TERABOX_CLIENT_ID:
            providers_configured.append("Terabox")
        
        if providers_configured:
            print(f"✅ Configured providers: {', '.join(providers_configured)}")
        else:
            print("⚠️ No cloud providers configured yet - add API credentials to .env file")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Unified Cloud Storage - Backend Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_database,
        test_security,
        test_providers
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Your backend is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Copy .env.example to .env and add your API credentials")
        print("2. Run: python main.py")
        print("3. Visit: http://localhost:8000/api/docs")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
