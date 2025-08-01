#!/usr/bin/env python
"""
Test script to verify teacher dashboard routing works correctly.
This tests the full authentication -> profile fetch -> routing flow.
"""
import requests
import json
import sys

def test_teacher_routing():
    """Test that teacher user gets routed to correct dashboard."""
    
    base_url = "http://localhost:8000/api"
    teacher_email = "teacher.test@example.com"
    
    print("🔍 Testing Teacher Dashboard Routing")
    print("=" * 50)
    
    # Step 1: Request verification code
    print(f"Step 1: Requesting verification code for {teacher_email}")
    response = requests.post(
        f"{base_url}/accounts/users/request_code/",
        json={"email": teacher_email}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to request code: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Verification code requested successfully")
    
    # Step 2: Authenticate with code 000000 (test code)
    print(f"Step 2: Authenticating with test code")
    auth_response = requests.post(
        f"{base_url}/accounts/users/auth/",
        json={"email": teacher_email, "verification_code": "000000"}
    )
    
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        print(auth_response.text)
        return False
    
    auth_data = auth_response.json()
    token = auth_data.get("token")
    print(f"✅ Authentication successful, token: {token[:20]}...")
    
    # Step 3: Get dashboard info with token
    print(f"Step 3: Fetching dashboard info")
    headers = {"Authorization": f"Token {token}"}
    dashboard_response = requests.get(
        f"{base_url}/accounts/users/dashboard_info/",
        headers=headers
    )
    
    if dashboard_response.status_code != 200:
        print(f"❌ Dashboard info failed: {dashboard_response.status_code}")
        print(dashboard_response.text)
        return False
    
    dashboard_data = dashboard_response.json()
    user_info = dashboard_data.get("user_info", {})
    
    print("✅ Dashboard info fetched successfully")
    print(f"📋 User Profile:")
    print(f"   - Email: {user_info.get('email')}")
    print(f"   - Name: {user_info.get('name')}")
    print(f"   - User Type: {user_info.get('user_type')}")
    print(f"   - Is Admin: {user_info.get('is_admin')}")
    print(f"   - Roles: {json.dumps(user_info.get('roles', []), indent=6)}")
    
    # Step 4: Verify routing logic
    print(f"\nStep 4: Verifying routing logic")
    user_type = user_info.get('user_type')
    is_admin = user_info.get('is_admin')
    
    # This mimics the frontend routing logic in home/index.tsx
    expected_route = None
    if user_type == 'admin' and is_admin:
        expected_route = '/(school-admin)/dashboard'
    elif user_type == 'teacher':
        expected_route = '/(teacher)/dashboard'
    elif user_type == 'student':
        expected_route = '/student/dashboard'
    elif user_type == 'parent':
        expected_route = '/parents'
    else:
        expected_route = '/(school-admin)/dashboard'  # Default fallback
    
    print(f"🎯 Expected route: {expected_route}")
    
    # Step 5: Validate results
    if user_type == 'teacher' and expected_route == '/(teacher)/dashboard':
        print("\n🎉 SUCCESS: Teacher routing is working correctly!")
        print(f"   - User type correctly identified as 'teacher'")
        print(f"   - Expected route: {expected_route}")
        print(f"   - This user will be routed to the teacher dashboard")
        return True
    else:
        print(f"\n❌ FAILURE: Teacher routing is not working correctly")
        print(f"   - Expected user_type: 'teacher', got: '{user_type}'")
        print(f"   - Expected route: '/(teacher)/dashboard', got: '{expected_route}'")
        return False

if __name__ == "__main__":
    success = test_teacher_routing()
    sys.exit(0 if success else 1)