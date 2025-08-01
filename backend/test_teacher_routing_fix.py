#!/usr/bin/env python3

"""
Test script to verify the teacher routing fix.
Run this script to create a test teacher and verify the authentication response.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aprendecomigo.settings')
django.setup()

from accounts.models import CustomUser, School, SchoolMembership, SchoolRole, TeacherProfile
from accounts.serializers import AuthenticationResponseSerializer
from django.test import RequestFactory


def create_test_teacher():
    """Create a test teacher for verification."""
    
    print("🔧 Creating test teacher...")
    
    # Create or get test school
    school, created = School.objects.get_or_create(
        name="Test School for Routing",
        defaults={
            "description": "Test school for teacher routing verification",
            "contact_email": "admin@testschool.com"
        }
    )
    if created:
        print(f"✅ Created test school: {school.name}")
    else:
        print(f"✅ Using existing test school: {school.name}")
    
    # Create or get test teacher
    teacher_email = "test.teacher@example.com"
    teacher, created = CustomUser.objects.get_or_create(
        email=teacher_email,
        defaults={
            "name": "Test Teacher",
            "email_verified": True
        }
    )
    if created:
        print(f"✅ Created test teacher: {teacher.email}")
    else:
        print(f"✅ Using existing test teacher: {teacher.email}")
    
    # Create or get teacher profile
    profile, created = TeacherProfile.objects.get_or_create(
        user=teacher,
        defaults={
            "bio": "Test teacher for routing verification",
            "specialty": "Mathematics"
        }
    )
    
    # Create or get teacher membership
    membership, created = SchoolMembership.objects.get_or_create(
        user=teacher,
        school=school,
        defaults={
            "role": SchoolRole.TEACHER,
            "is_active": True
        }
    )
    if created:
        print(f"✅ Created teacher membership")
    else:
        print(f"✅ Using existing teacher membership")
    
    return teacher, school, membership


def test_authentication_serializer(teacher):
    """Test the AuthenticationResponseSerializer."""
    
    print("\n📝 Testing AuthenticationResponseSerializer...")
    
    # Create a mock request for the serializer context
    factory = RequestFactory()
    request = factory.get('/')
    
    # Test the serializer
    serializer = AuthenticationResponseSerializer(teacher, context={'request': request})
    data = serializer.data
    
    print(f"Serialized data keys: {list(data.keys())}")
    
    # Check required fields
    required_fields = ['user_type', 'is_admin', 'roles']
    missing_fields = []
    
    for field in required_fields:
        if field in data:
            print(f"✅ {field}: {data[field]}")
        else:
            missing_fields.append(field)
            print(f"❌ Missing field: {field}")
    
    # Test the specific values
    user_type = data.get('user_type')
    is_admin = data.get('is_admin')
    roles = data.get('roles', [])
    
    success = True
    
    if user_type != 'teacher':
        print(f"❌ Expected user_type='teacher', got '{user_type}'")
        success = False
    else:
        print(f"✅ user_type is correct: '{user_type}'")
    
    if is_admin != False:
        print(f"❌ Expected is_admin=False, got {is_admin}")
        success = False
    else:
        print(f"✅ is_admin is correct: {is_admin}")
    
    if not roles:
        print(f"❌ Expected roles list, got empty: {roles}")
        success = False
    else:
        print(f"✅ roles list has {len(roles)} item(s)")
        
        # Check first role
        if roles:
            first_role = roles[0]
            if first_role.get('role') == SchoolRole.TEACHER:
                print(f"✅ First role is teacher: {first_role['role']}")
            else:
                print(f"❌ Expected first role to be teacher, got: {first_role.get('role')}")
                success = False
    
    return success, data


def verify_routing_logic():
    """Verify the routing logic works correctly."""
    
    print("\n🧪 Testing Routing Logic...")
    
    # Test 1: Create teacher and verify routing
    teacher, school, membership = create_test_teacher()
    success, data = test_authentication_serializer(teacher)
    
    if not success:
        print("❌ Teacher authentication serializer test failed")
        return False
    
    # Test 2: Create school owner and verify routing
    print("\n🔧 Creating test school owner...")
    owner_email = "test.owner@example.com"
    owner, created = CustomUser.objects.get_or_create(
        email=owner_email,
        defaults={
            "name": "Test School Owner",
            "email_verified": True
        }
    )
    
    # Create school owner membership
    owner_membership, created = SchoolMembership.objects.get_or_create(
        user=owner,
        school=school,
        defaults={
            "role": SchoolRole.SCHOOL_OWNER,
            "is_active": True
        }
    )
    
    print("📝 Testing school owner serializer...")
    owner_success, owner_data = test_authentication_serializer(owner)
    
    if not owner_success:
        print("❌ School owner authentication serializer test failed")
        return False
    
    # Verify owner gets admin type
    if owner_data.get('user_type') != 'admin':
        print(f"❌ Expected school owner to have user_type='admin', got '{owner_data.get('user_type')}'")
        return False
    else:
        print(f"✅ School owner correctly has user_type='admin'")
    
    if owner_data.get('is_admin') != True:
        print(f"❌ Expected school owner to have is_admin=True, got {owner_data.get('is_admin')}")
        return False
    else:
        print(f"✅ School owner correctly has is_admin=True")
    
    return True


def main():
    """Main test function."""
    
    print("🚀 Testing Teacher Routing Fix")
    print("=" * 50)
    
    try:
        success = verify_routing_logic()
        
        print("\n📊 Test Summary")
        print("=" * 30)
        
        if success:
            print("🎉 All tests passed!")
            print("\n✅ The fix is working correctly:")
            print("   - Teachers get user_type='teacher' (routed to /(teacher)/dashboard)")
            print("   - School owners get user_type='admin' (routed to /dashboard)")
            print("   - Authentication response includes role information")
            print("\n🔄 Next steps:")
            print("   1. Test with real authentication flow")
            print("   2. Verify frontend routing works correctly")
            print("   3. Test with QA test suite")
            return True
        else:
            print("❌ Some tests failed!")
            print("\n🔧 Please check the implementation and try again.")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)