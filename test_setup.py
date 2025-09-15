#!/usr/bin/env python3
"""
Test script to validate backend setup
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from app.core.config import settings
        print("✅ Configuration loaded")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    try:
        from app.core.database import Base, engine
        print("✅ Database models loaded")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    try:
        from app.core.security import create_access_token, verify_password
        print("✅ Security functions loaded")
    except Exception as e:
        print(f"❌ Security error: {e}")
        return False
    
    try:
        from app.models.user import User
        from app.models.verification import EmailVerification, PasswordReset
        print("✅ Database models loaded")
    except Exception as e:
        print(f"❌ Models error: {e}")
        return False
    
    try:
        from app.api.v1.auth import router as auth_router
        from app.api.v1.users import router as users_router
        print("✅ API routes loaded")
    except Exception as e:
        print(f"❌ API routes error: {e}")
        return False
    
    try:
        from app.tasks.celery_app import celery_app
        print("✅ Celery app loaded")
    except Exception as e:
        print(f"❌ Celery error: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🗄️  Testing database connection...")
    
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure PostgreSQL is running and database exists")
        return False

def test_redis_connection():
    """Test Redis connection"""
    print("\n🔴 Testing Redis connection...")
    
    try:
        import redis
        from app.core.config import settings
        
        r = redis.from_url(settings.redis_url)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Make sure Redis is running")
        return False

def main():
    """Main test function"""
    print("🚀 Furu AI Backend Setup Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        sys.exit(1)
    
    # Test database connection
    if not test_database_connection():
        print("\n❌ Database connection failed!")
        print("   Please set up PostgreSQL and update DATABASE_URL in .env")
        sys.exit(1)
    
    # Test Redis connection
    if not test_redis_connection():
        print("\n❌ Redis connection failed!")
        print("   Please set up Redis and update REDIS_URL in .env")
        sys.exit(1)
    
    print("\n🎉 All tests passed! Backend is ready to run.")
    print("\nNext steps:")
    print("1. Run: alembic upgrade head")
    print("2. Start FastAPI: uvicorn app.main:app --reload")
    print("3. Start Celery: celery -A app.tasks.celery_app worker --loglevel=info")

if __name__ == "__main__":
    main()