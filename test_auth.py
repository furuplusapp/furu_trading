#!/usr/bin/env python3
"""
Test script to verify authentication endpoints are working correctly
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/auth"

def test_register():
    """Test user registration"""
    print("Testing user registration...")
    
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=user_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ Registration successful!")
            print(f"User ID: {data.get('id')}")
            print(f"Email: {data.get('email')}")
            print(f"Full Name: {data.get('full_name')}")
            print(f"Plan: {data.get('plan')}")
            print(f"Verified: {data.get('is_verified')}")
            return data
        else:
            print(f"❌ Registration failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_login():
    """Test user login"""
    print("\nTesting user login...")
    
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"Access Token: {data.get('access_token')[:20]}...")
            print(f"Refresh Token: {data.get('refresh_token')[:20]}...")
            print(f"Token Type: {data.get('token_type')}")
            
            # Check user information
            user = data.get('user')
            if user:
                print(f"User ID: {user.get('id')}")
                print(f"Email: {user.get('email')}")
                print(f"Full Name: {user.get('full_name')}")
                print(f"Plan: {user.get('plan')}")
                print(f"Verified: {user.get('is_verified')}")
            else:
                print("❌ No user information in response")
            
            return data
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Testing Authentication Endpoints")
    print("=" * 50)
    
    # Test registration
    user = test_register()
    
    # Test login
    if user:
        test_login()
    
    print("\n✅ Test completed!")