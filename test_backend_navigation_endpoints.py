#!/usr/bin/env python3
"""
Test script for backend navigation endpoints - GitHub Issues #66/#67
Tests the three critical endpoints identified in QA:
1. Global Search API
2. Notification Counts API  
3. School Settings API

This script creates test data and verifies endpoints work with proper authentication.
"""
import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aprendecomigo.settings.development')
django.setup()

import json
import requests
from django.contrib.auth import get_user_model
from django.test import Client
from knox.models import AuthToken
from accounts.models import (
    School, SchoolMembership, SchoolRole, 
    TeacherProfile, StudentProfile, 
    EducationalSystem, Course
)

User = get_user_model()

def setup_test_data():
    """Create test data for API testing"""
    print("Setting up test data...")
    
    # Get or create educational system
    educational_system, _ = EducationalSystem.objects.get_or_create(
        code="pt",
        defaults={
            "name": "Portugal",
            "description": "Portuguese educational system"
        }
    )
    
    # Create test school
    school, _ = School.objects.get_or_create(
        name="Test Navigation School",
        defaults={
            "description": "School for testing navigation endpoints"
        }
    )
    
    # Create school admin user
    admin_user, created = User.objects.get_or_create(
        email="admin@navtest.com",
        defaults={
            "name": "Navigation Test Admin",
            "is_verified": True,
            "first_login_completed": True
        }
    )
    
    # Create school membership for admin
    admin_membership, _ = SchoolMembership.objects.get_or_create(
        user=admin_user,
        school=school,
        defaults={
            "role": SchoolRole.SCHOOL_ADMIN,
            "is_active": True
        }
    )
    
    # Create teacher user
    teacher_user, _ = User.objects.get_or_create(
        email="teacher@navtest.com",
        defaults={
            "name": "Navigation Test Teacher",
            "is_verified": True,
            "first_login_completed": True
        }
    )
    
    # Create teacher profile
    teacher_profile, _ = TeacherProfile.objects.get_or_create(
        user=teacher_user,
        defaults={
            "bio": "Test teacher for navigation",
            "specialty": "Mathematics"
        }
    )
    
    # Create teacher membership
    teacher_membership, _ = SchoolMembership.objects.get_or_create(
        user=teacher_user,
        school=school,
        defaults={
            "role": SchoolRole.TEACHER,
            "is_active": True
        }
    )
    
    # Create student user
    student_user, _ = User.objects.get_or_create(
        email="student@navtest.com",
        defaults={
            "name": "Navigation Test Student",
            "is_verified": True,
            "first_login_completed": True
        }
    )
    
    # Create student profile
    student_profile, _ = StudentProfile.objects.get_or_create(
        user=student_user,
        defaults={
            "educational_system": educational_system,
            "school_year": "10",
            "birth_date": "2005-01-01"
        }
    )
    
    # Create student membership
    student_membership, _ = SchoolMembership.objects.get_or_create(
        user=student_user,
        school=school,
        defaults={
            "role": SchoolRole.STUDENT,
            "is_active": True
        }
    )
    
    # Create test course
    course, _ = Course.objects.get_or_create(
        name="Advanced Navigation Testing",
        defaults={
            "code": "NAV_TEST",
            "educational_system": educational_system,
            "education_level": "ensino_secundario",
            "description": "Course for testing navigation search"
        }
    )
    
    print("✅ Test data setup complete")
    return {
        'admin_user': admin_user,
        'teacher_user': teacher_user,
        'student_user': student_user,
        'school': school,
        'educational_system': educational_system,
        'course': course
    }

def get_auth_token(user):
    """Get authentication token for user"""
    token = AuthToken.objects.create(user)[1]
    return token

def test_global_search_api(token):
    """Test the global search API endpoint"""
    print("\n🔍 Testing Global Search API...")
    
    base_url = "http://localhost:8000"
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    # Test search for teacher
    print("Testing teacher search...")
    response = requests.get(
        f"{base_url}/api/accounts/search/global/",
        params={"q": "Navigation Test Teacher", "types": "teacher", "limit": 5},
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Results found: {data.get('total_count', 0)}")
        print(f"Categories: {data.get('categories', {})}")
        if data.get('results'):
            result = data['results'][0]
            print(f"First result: {result.get('title')} ({result.get('type')})")
            print(f"Route: {result.get('route')}")
            print("✅ Global Search API working correctly")
        else:
            print("⚠️  No results found")
    else:
        print(f"❌ Global Search API failed: {response.text}")
    
    return response.status_code == 200

def test_notification_counts_api(token):
    """Test the notification counts API endpoint"""
    print("\n📢 Testing Notification Counts API...")
    
    base_url = "http://localhost:8000"
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{base_url}/api/notifications/counts/",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Notification counts: {json.dumps(data, indent=2)}")
        
        # Verify expected fields
        expected_fields = [
            'pending_invitations', 'new_registrations', 
            'incomplete_profiles', 'overdue_tasks', 'total_unread'
        ]
        
        missing_fields = [field for field in expected_fields if field not in data]
        if not missing_fields:
            print("✅ Notification Counts API working correctly")
        else:
            print(f"⚠️  Missing fields: {missing_fields}")
    else:
        print(f"❌ Notification Counts API failed: {response.text}")
    
    return response.status_code == 200

def test_school_settings_api(token, school_id):
    """Test the school settings API endpoint"""
    print("\n⚙️  Testing School Settings API...")
    
    base_url = "http://localhost:8000"
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    # Test GET settings
    response = requests.get(
        f"{base_url}/api/accounts/schools/{school_id}/settings/",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Settings data structure:")
        print(f"- Has school_profile: {'school_profile' in data}")
        print(f"- Has settings: {'settings' in data}")
        
        if 'school_profile' in data and 'settings' in data:
            school_profile = data['school_profile']
            settings = data['settings']
            print(f"School name: {school_profile.get('name')}")
            print(f"Educational system: {settings.get('educational_system_name')}")
            print("✅ School Settings API working correctly")
        else:
            print("⚠️  Unexpected data structure")
    else:
        print(f"❌ School Settings API failed: {response.text}")
    
    return response.status_code == 200

def test_navigation_preferences_api(token):
    """Test the navigation preferences API endpoint"""
    print("\n🧭 Testing Navigation Preferences API...")
    
    base_url = "http://localhost:8000"
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    # Test GET preferences
    response = requests.get(
        f"{base_url}/api/accounts/users/navigation_preferences/",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Navigation preferences: {json.dumps(data, indent=2)}")
        print("✅ Navigation Preferences API working correctly")
    else:
        print(f"❌ Navigation Preferences API failed: {response.text}")
    
    return response.status_code == 200

def main():
    """Main test execution"""
    print("🚀 Starting Backend Navigation Endpoints Test")
    print("=" * 50)
    
    try:
        # Setup test data
        test_data = setup_test_data()
        
        # Get authentication token for admin user
        admin_token = get_auth_token(test_data['admin_user'])
        print(f"✅ Generated auth token for admin user")
        
        # Run tests
        results = {
            'global_search': test_global_search_api(admin_token),
            'notification_counts': test_notification_counts_api(admin_token),
            'school_settings': test_school_settings_api(admin_token, test_data['school'].id),
            'navigation_preferences': test_navigation_preferences_api(admin_token)
        }
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Backend navigation endpoints are working correctly!")
            print("\nThe authentication issues reported in QA are likely frontend-related.")
            print("Next steps: Check frontend authentication token handling.")
        else:
            print("⚠️  Some tests failed - see details above")
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)