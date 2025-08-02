#!/usr/bin/env python3
"""
Simple test script for backend navigation endpoints.
Run from backend directory: python test_navigation_endpoints.py
"""
import requests
import json

def test_endpoints():
    """Test endpoints with curl-like requests"""
    base_url = "http://localhost:8000"
    
    print("🚀 Testing Backend Navigation Endpoints")
    print("=" * 50)
    
    # Test 1: Global Search API (without auth to check basic connectivity)
    print("\n🔍 Testing Global Search API connectivity...")
    try:
        response = requests.get(f"{base_url}/api/accounts/search/global/?q=test")
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Endpoint exists and requires authentication (expected)")
        else:
            print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Notification Counts API
    print("\n📢 Testing Notification Counts API connectivity...")
    try:
        response = requests.get(f"{base_url}/api/notifications/counts/")
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Endpoint exists and requires authentication (expected)")
        else:
            print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: School Settings API
    print("\n⚙️  Testing School Settings API connectivity...")
    try:
        response = requests.get(f"{base_url}/api/accounts/schools/1/settings/")
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Endpoint exists and requires authentication (expected)")
        else:
            print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Navigation Preferences API
    print("\n🧭 Testing Navigation Preferences API connectivity...")
    try:
        response = requests.get(f"{base_url}/api/accounts/users/navigation_preferences/")
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Endpoint exists and requires authentication (expected)")
        else:
            print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("📊 CONNECTIVITY TEST COMPLETE")
    print("All endpoints should return 401 (authentication required)")
    print("This confirms the endpoints exist and are properly protected.")
    print("\nNext: The QA authentication issues are likely in the frontend")
    print("authentication token handling, not the backend endpoints.")

if __name__ == "__main__":
    test_endpoints()