#!/usr/bin/env python
"""Test script to verify serializer fixes for availability API"""
import os
import sys
import django

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aprendecomigo.settings.testing')
django.setup()

from datetime import time, timedelta, date
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from accounts.models import (
    CustomUser, School, SchoolMembership, TeacherProfile, SchoolRole,
    SchoolSettings, EducationalSystem
)
from scheduler.models import WeekDay, TeacherAvailability, TeacherUnavailability
from scheduler.serializers import TeacherAvailabilitySerializer, TeacherUnavailabilitySerializer

def setup_test_data():
    """Set up test data"""
    # Create educational system and school
    edu_system, _ = EducationalSystem.objects.get_or_create(
        code="custom", defaults={"name": "Test System", "description": "Test educational system"}
    )
    school, _ = School.objects.get_or_create(
        name="Test School", defaults={"description": "Test Description"}
    )
    school_settings, _ = SchoolSettings.objects.get_or_create(
        school=school, defaults={"timezone": "America/New_York", "educational_system": edu_system}
    )
    
    # Create users
    teacher_user, _ = CustomUser.objects.get_or_create(
        email="teacher_test@test.com", defaults={"name": "Test Teacher", "password": "testpass123"}
    )
    teacher_profile, _ = TeacherProfile.objects.get_or_create(
        user=teacher_user, defaults={"bio": "Test bio"}
    )
    
    admin_user, _ = CustomUser.objects.get_or_create(
        email="admin_test@test.com", defaults={"name": "Admin User", "password": "testpass123"}
    )
    
    # Create school memberships
    SchoolMembership.objects.get_or_create(
        user=teacher_user, school=school, defaults={"role": SchoolRole.TEACHER}
    )
    SchoolMembership.objects.get_or_create(
        user=admin_user, school=school, defaults={"role": SchoolRole.SCHOOL_OWNER}
    )
    
    return {
        'school': school,
        'teacher_user': teacher_user,
        'teacher_profile': teacher_profile,
        'admin_user': admin_user,
    }

def test_availability_serializer_create():
    """Test TeacherAvailability serializer for creation"""
    print("Testing TeacherAvailability creation...")
    
    data = setup_test_data()
    future_date = timezone.now().date() + timedelta(days=7)
    
    serializer_data = {
        'teacher': data['teacher_profile'].id,
        'school': data['school'].id,
        'day_of_week': WeekDay.TUESDAY,
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'is_recurring': True,
        'effective_from': future_date.isoformat(),
    }
    
    serializer = TeacherAvailabilitySerializer(data=serializer_data)
    try:
        if serializer.is_valid(raise_exception=True):
            print("✓ Creation serializer validation passed")
            return True
    except Exception as e:
        print(f"✗ Creation serializer validation failed: {e}")
        return False

def test_availability_serializer_update():
    """Test TeacherAvailability serializer for updates"""
    print("Testing TeacherAvailability updates...")
    
    data = setup_test_data()
    
    # First create an availability
    availability = TeacherAvailability.objects.create(
        teacher=data['teacher_profile'],
        school=data['school'],
        day_of_week=WeekDay.FRIDAY,
        start_time=time(9, 0),
        end_time=time(17, 0)
    )
    
    # Test partial update
    serializer_data = {
        'start_time': '08:00:00',
        'end_time': '18:00:00',
        'is_active': False
    }
    
    serializer = TeacherAvailabilitySerializer(availability, data=serializer_data, partial=True)
    try:
        if serializer.is_valid(raise_exception=True):
            print("✓ Partial update serializer validation passed")
            return True
    except Exception as e:
        print(f"✗ Partial update serializer validation failed: {e}")
        return False

def test_unavailability_serializer_create():
    """Test TeacherUnavailability serializer for creation"""
    print("Testing TeacherUnavailability creation...")
    
    data = setup_test_data()
    future_date = timezone.now().date() + timedelta(days=7)
    
    serializer_data = {
        'teacher': data['teacher_profile'].id,
        'school': data['school'].id,
        'date': future_date.isoformat(),
        'is_all_day': True,
        'reason': 'Public holiday',
    }
    
    serializer = TeacherUnavailabilitySerializer(data=serializer_data)
    try:
        if serializer.is_valid(raise_exception=True):
            print("✓ Unavailability creation serializer validation passed")
            return True
    except Exception as e:
        print(f"✗ Unavailability creation serializer validation failed: {e}")
        return False

def test_unavailability_serializer_update():
    """Test TeacherUnavailability serializer for updates"""
    print("Testing TeacherUnavailability updates...")
    
    data = setup_test_data()
    future_date = timezone.now().date() + timedelta(days=7)
    
    # First create an unavailability
    unavailability = TeacherUnavailability.objects.create(
        teacher=data['teacher_profile'],
        school=data['school'],
        date=future_date,
        start_time=time(10, 0),
        end_time=time(12, 0),
        is_all_day=False,
        reason='Meeting'
    )
    
    # Test partial update
    serializer_data = {
        'reason': 'Updated meeting',
        'start_time': '09:00:00',
        'end_time': '11:00:00'
    }
    
    serializer = TeacherUnavailabilitySerializer(unavailability, data=serializer_data, partial=True)
    try:
        if serializer.is_valid(raise_exception=True):
            print("✓ Unavailability partial update serializer validation passed")
            return True
    except Exception as e:
        print(f"✗ Unavailability partial update serializer validation failed: {e}")
        return False

def main():
    print("Testing serializer fixes for Teacher Availability API")
    print("=" * 55)
    
    # Clean up any existing test data
    TeacherAvailability.objects.filter(teacher__user__email__contains='test').delete()
    TeacherUnavailability.objects.filter(teacher__user__email__contains='test').delete()
    
    results = []
    
    results.append(test_availability_serializer_create())
    results.append(test_availability_serializer_update())
    results.append(test_unavailability_serializer_create())
    results.append(test_unavailability_serializer_update())
    
    print("\n" + "=" * 55)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All serializer tests passed! The fix looks good.")
    else:
        print("✗ Some tests failed. Check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    main()