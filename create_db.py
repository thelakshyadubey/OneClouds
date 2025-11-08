# create_db.py
import os
from sqlalchemy import create_engine, text
from backend.database import Base, engine
from backend.models import User, StorageAccount, FileMetadata, SyncLog, UserSession, TrustedDevice, Job, UserPreferences # Import all models here


def create_db_tables():
    print("Attempting to drop all existing database tables...")
    Base.metadata.drop_all(engine) # Explicitly drop all tables
    print("Existing database tables dropped.")

    print("Attempting to create all database tables...")
    Base.metadata.create_all(engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    # Ensure the database directory exists if using relative path
    db_path = "./unified_storage.db"
    if os.path.exists(db_path):
        print(f"Note: Database file '{db_path}' exists. It will be dropped and recreated.")
    
    create_db_tables()