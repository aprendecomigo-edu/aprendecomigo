#!/usr/bin/env python
"""
Manual test script for invite existing teacher functionality.
Run this with: python manage.py shell < test_invite_existing.py
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aprendecomigo.settings")
django.setup()

from accounts.db_queries import create_school_invitation
from accounts.models import CustomUser, School, SchoolMembership, SchoolRole


def test_invite_existing_flow():
    """Test the complete invite existing teacher flow."""
    print("\n🧪 Testing Invite Existing Teacher Flow")
    print("=" * 50)

    # Clean up any existing test data
    CustomUser.objects.filter(email__contains="test.invite").delete()
    School.objects.filter(name__contains="Test Invite").delete()

    # Create test users
    school_owner = CustomUser.objects.create_user(
        email="owner.test.invite@example.com",
        name="Test School Owner",
        phone_number="+351 912 000 001",
    )

    existing_user = CustomUser.objects.create_user(
        email="teacher.test.invite@example.com",
        name="Test Existing User",
        phone_number="+351 912 000 002",
    )

    # Create test school
    school = School.objects.create(
        name="Test Invite School", description="Test school for invitation flow"
    )

    # Make school_owner an owner of the school
    SchoolMembership.objects.create(
        user=school_owner, school=school, role=SchoolRole.SCHOOL_OWNER, is_active=True
    )

    print("✅ Created test data:")
    print(f"   - School Owner: {school_owner.email}")
    print(f"   - Existing User: {existing_user.email}")
    print(f"   - School: {school.name} (ID: {school.id})")

    # Test 1: Create invitation
    print("\n🔗 Creating invitation...")
    invitation = create_school_invitation(
        school_id=school.id,
        email=existing_user.email,
        invited_by=school_owner,
        role=SchoolRole.TEACHER,
    )

    print("✅ Invitation created:")
    print(f"   - Token: {invitation.token}")
    print(f"   - Expires: {invitation.expires_at}")
    print(f"   - Link: https://aprendecomigo.com/accept-invitation/{invitation.token}")

    # Test 2: Check invitation is valid
    print("\n✅ Invitation validation:")
    print(f"   - Is valid: {invitation.is_valid()}")
    print(f"   - Is accepted: {invitation.is_accepted}")

    # Test 3: Verify no teacher profile exists yet
    print("\n👨‍🏫 Teacher status before acceptance:")
    print(f"   - Has teacher profile: {hasattr(existing_user, 'teacher_profile')}")
    print(
        f"   - Teacher memberships: {SchoolMembership.objects.filter(user=existing_user, role=SchoolRole.TEACHER).count()}"
    )

    # Test 4: Simulate acceptance (without API call)
    print("\n✅ Simulating invitation acceptance...")
    from accounts.models import TeacherProfile

    # Create teacher profile
    teacher_profile = TeacherProfile.objects.create(
        user=existing_user, bio="Accepted invitation, excited to teach!", specialty="Mathematics"
    )

    # Create school membership
    membership = SchoolMembership.objects.create(
        user=existing_user, school=school, role=SchoolRole.TEACHER, is_active=True
    )

    # Mark invitation as accepted
    invitation.is_accepted = True
    invitation.save()

    print("✅ Acceptance complete:")
    print(f"   - Teacher profile created: {teacher_profile.id}")
    print(f"   - School membership created: {membership.id}")
    print(f"   - Invitation marked as accepted: {invitation.is_accepted}")

    # Test 5: Verify final state
    print("\n🎯 Final verification:")
    existing_user.refresh_from_db()
    print(f"   - Has teacher profile: {hasattr(existing_user, 'teacher_profile')}")
    teacher_memberships = SchoolMembership.objects.filter(
        user=existing_user, role=SchoolRole.TEACHER
    )
    print(f"   - Teacher memberships: {teacher_memberships.count()}")
    print(
        f"   - School: {teacher_memberships.first().school.name if teacher_memberships.exists() else 'None'}"
    )

    print("\n🎉 Test completed successfully!")
    return True


def test_api_endpoints():
    """Show the available API endpoints."""
    print("\n📡 Available API Endpoints")
    print("=" * 50)

    endpoints = [
        {
            "method": "POST",
            "url": "/api/accounts/teachers/invite-existing/",
            "description": "Create invitation for existing user",
            "auth": "Required (School Owner/Admin)",
        },
        {
            "method": "GET",
            "url": "/api/accounts/invitations/{token}/details/",
            "description": "Get invitation details (public)",
            "auth": "Not required",
        },
        {
            "method": "POST",
            "url": "/api/accounts/invitations/{token}/accept/",
            "description": "Accept invitation and become teacher",
            "auth": "Required (Invited User)",
        },
    ]

    for endpoint in endpoints:
        print(f"   {endpoint['method']:4} {endpoint['url']}")
        print(f"        {endpoint['description']}")
        print(f"        Auth: {endpoint['auth']}")
        print()

    print("📋 Frontend Implementation Steps:")
    print("   1. Admin creates invitation → get shareable link")
    print("   2. Share link via WhatsApp/email/SMS")
    print("   3. User clicks link → show invitation details")
    print("   4. User accepts → becomes teacher with custom profile")


if __name__ == "__main__":
    test_invite_existing_flow()
    test_api_endpoints()
