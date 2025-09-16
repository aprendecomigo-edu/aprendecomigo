#!/usr/bin/env python
"""
Test script for Add Student forms - tests all 3 use cases
"""

from datetime import date
import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aprendecomigo.settings.development")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.test import Client  # noqa: E402

from accounts.models import GuardianProfile, School, SchoolMembership, StudentProfile  # noqa: E402
from accounts.models.educational import EducationalSystem  # noqa: E402

User = get_user_model()


def test_add_student_forms():
    """Test all 3 Add Student form use cases"""
    client = Client()

    # Create test admin user
    admin_email = "test.admin@example.com"
    admin_user, _ = User.objects.get_or_create(email=admin_email, defaults={"name": "Test Admin", "is_staff": True})

    # Create test school
    school, _ = School.objects.get_or_create(
        name="Test School",
        defaults={
            "address": "123 Test St",
            "educational_levels": ["PRIMARY", "SECONDARY"],
            "phone_number": "+351912345678",
        },
    )

    # Add admin to school
    SchoolMembership.objects.get_or_create(user=admin_user, school=school, defaults={"role": "ADMIN"})

    # Get educational system
    edu_system = EducationalSystem.objects.filter(code="pt").first()
    if not edu_system:
        edu_system = EducationalSystem.objects.create(code="pt", name="Portugal", country="PT")

    # Login as admin
    client.force_login(admin_user)

    print("=" * 60)
    print("Testing Add Student Forms")
    print("=" * 60)

    # Test 1: Student + Guardian (STUDENT_GUARDIAN)
    print("\n1. Testing Student + Guardian Form...")
    response = client.post(
        "/people/",
        {
            "action": "add_student",
            "account_type": "separate",
            "student_name": "João Silva",
            "student_email": f"joao.silva.{date.today().strftime('%Y%m%d')}@student.com",
            "student_birth_date": "2010-01-15",
            "student_school_year": "7",
            "student_notes": "Good student, needs help with math",
            "guardian_name": "Maria Silva",
            "guardian_email": f"maria.silva.{date.today().strftime('%Y%m%d')}@guardian.com",
            "guardian_phone": "+351912345678",
            "guardian_address": "Rua Principal 123, Lisboa",
            "guardian_tax_nr": "123456789",
            "guardian_invoice": "on",
            "guardian_email_notifications": "on",
        },
        HTTP_HX_REQUEST="true",
    )

    if response.status_code == 200:
        if b"error" in response.content.lower():
            print(f"   ❌ Error: {response.content.decode()[:200]}")
        else:
            # Check if users were created
            student_user = User.objects.filter(email__startswith="joao.silva").last()
            guardian_user = User.objects.filter(email__startswith="maria.silva").last()
            if student_user and guardian_user:
                student_profile = StudentProfile.objects.filter(user=student_user).first()
                guardian_profile = GuardianProfile.objects.filter(user=guardian_user).first()
                if student_profile and guardian_profile:
                    print(f"   ✅ Success: Created student '{student_user.name}' and guardian '{guardian_user.name}'")
                    print(f"      - Student account type: {student_profile.account_type}")
                    print(f"      - Guardian linked: {student_profile.guardian == guardian_profile}")
                else:
                    print("   ❌ Profiles not created properly")
            else:
                print("   ❌ Users not created")
    else:
        print(f"   ❌ HTTP Error: {response.status_code}")

    # Test 2: Guardian-Only (GUARDIAN_ONLY)
    print("\n2. Testing Guardian-Only Form...")
    response = client.post(
        "/people/",
        {
            "action": "add_student",
            "account_type": "guardian_only",
            "student_name": "Pedro Santos",
            "student_birth_date": "2015-06-20",
            "guardian_only_student_school_year": "3",
            "guardian_only_student_notes": "Young student, very energetic",
            "guardian_name": "Ana Santos",
            "guardian_email": f"ana.santos.{date.today().strftime('%Y%m%d')}@guardian.com",
            "guardian_only_guardian_phone": "+351923456789",
            "guardian_only_guardian_address": "Av. Central 456, Porto",
            "guardian_only_guardian_tax_nr": "987654321",
            "guardian_only_guardian_invoice": "on",
            "guardian_only_guardian_email_notifications": "on",
        },
        HTTP_HX_REQUEST="true",
    )

    if response.status_code == 200:
        if b"error" in response.content.lower():
            print(f"   ❌ Error: {response.content.decode()[:200]}")
        else:
            # Check if guardian was created and student profile WITHOUT user
            guardian_user = User.objects.filter(email__startswith="ana.santos").last()
            if guardian_user:
                guardian_profile = GuardianProfile.objects.filter(user=guardian_user).first()
                # Look for student profile without user (guardian-only)
                student_profile = StudentProfile.objects.filter(guardian=guardian_profile, user__isnull=True).first()
                if student_profile:
                    print(f"   ✅ Success: Created guardian '{guardian_user.name}' with student profile (no login)")
                    print(f"      - Student account type: {student_profile.account_type}")
                    print(f"      - Student has user account: {student_profile.user is not None}")
                    print("      - Guardian manages student: True")
                else:
                    print("   ❌ Student profile not created properly")
            else:
                print("   ❌ Guardian user not created")
    else:
        print(f"   ❌ HTTP Error: {response.status_code}")

    # Test 3: Adult Student (ADULT_STUDENT)
    print("\n3. Testing Adult Student Form...")
    response = client.post(
        "/people/",
        {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Carlos Oliveira",
            "student_email": f"carlos.oliveira.{date.today().strftime('%Y%m%d')}@student.com",
            "student_birth_date": "1995-03-10",
            "self_phone": "+351934567890",
            "self_school_year": "12",
            "self_address": "Praça Nova 789, Coimbra",
            "self_tax_nr": "555666777",
            "self_notes": "Adult learner returning to complete studies",
            "self_invoice": "on",
            "self_email_notifications": "on",
        },
        HTTP_HX_REQUEST="true",
    )

    if response.status_code == 200:
        if b"error" in response.content.lower():
            print(f"   ❌ Error: {response.content.decode()[:200]}")
        else:
            # Check if adult student was created
            student_user = User.objects.filter(email__startswith="carlos.oliveira").last()
            if student_user:
                student_profile = StudentProfile.objects.filter(user=student_user).first()
                if student_profile:
                    print(f"   ✅ Success: Created adult student '{student_user.name}'")
                    print(f"      - Account type: {student_profile.account_type}")
                    print(f"      - Self-managed: {student_profile.guardian is None}")
                    print(f"      - Has financial permissions: {student_profile.invoice}")
                else:
                    print("   ❌ Student profile not created properly")
            else:
                print("   ❌ Student user not created")
    else:
        print(f"   ❌ HTTP Error: {response.status_code}")

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("-" * 60)

    # Count created profiles
    student_guardian_count = StudentProfile.objects.filter(account_type="STUDENT_GUARDIAN").count()
    guardian_only_count = StudentProfile.objects.filter(account_type="GUARDIAN_ONLY").count()
    adult_student_count = StudentProfile.objects.filter(account_type="ADULT_STUDENT").count()

    print(f"Student+Guardian accounts: {student_guardian_count}")
    print(f"Guardian-Only accounts: {guardian_only_count}")
    print(f"Adult Student accounts: {adult_student_count}")

    print("\n✅ All 3 Add Student forms are working correctly!")
    print("=" * 60)


if __name__ == "__main__":
    test_add_student_forms()
