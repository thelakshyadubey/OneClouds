"""
Quick script to reset a user's password with the new bcrypt truncation logic
"""
from backend.database import SessionLocal
from backend.models import User
from backend.auth import AuthHandler

def reset_password(email: str, new_password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User {email} not found")
            return
        
        auth_handler = AuthHandler()
        user.hashed_password = auth_handler.hash_password(new_password)
        db.commit()
        print(f"✅ Password updated for {email}")
        print(f"   New password: {new_password}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Reset password for the user
    email = "lakshya.dubey10@gmail.com"
    new_password = "password123"  # Change this to your desired password
    
    print(f"Resetting password for {email}...")
    reset_password(email, new_password)
