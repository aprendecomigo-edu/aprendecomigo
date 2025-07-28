"""
Tests for the TeacherInvitation model and related functionality.
Following TDD methodology - tests written first, then implementation.
"""
import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from accounts.models import (
    CustomUser, 
    School, 
    SchoolMembership, 
    SchoolRole,
    TeacherInvitation,  # This will be created
    EmailDeliveryStatus,  # This will be created
    InvitationStatus  # This will be created
)


class TeacherInvitationModelTest(TestCase):
    """Test suite for the TeacherInvitation model."""
    
    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School",
            description="School for testing invitations"
        )
        
        self.school_owner = CustomUser.objects.create_user(
            email="owner@testschool.com",
            name="School Owner",
            phone_number="+351912000001"
        )
        
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )
        
        self.batch_id = uuid.uuid4()
    
    def test_teacher_invitation_creation(self):
        """Test creating a basic teacher invitation."""
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="newteacher@example.com",
            invited_by=self.school_owner,
            custom_message="Welcome to our school!",
            batch_id=self.batch_id
        )
        
        self.assertEqual(invitation.school, self.school)
        self.assertEqual(invitation.email, "newteacher@example.com")
        self.assertEqual(invitation.invited_by, self.school_owner)
        self.assertEqual(invitation.custom_message, "Welcome to our school!")
        self.assertEqual(invitation.batch_id, self.batch_id)
        self.assertEqual(invitation.role, SchoolRole.TEACHER)  # Default role
        self.assertEqual(invitation.status, InvitationStatus.PENDING)
        self.assertEqual(invitation.email_delivery_status, EmailDeliveryStatus.NOT_SENT)
        self.assertEqual(invitation.retry_count, 0)
        self.assertIsNotNone(invitation.token)
        self.assertIsNotNone(invitation.expires_at)
        self.assertFalse(invitation.is_accepted)
    
    def test_teacher_invitation_token_uniqueness(self):
        """Test that invitation tokens are unique."""
        invitation1 = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher1@example.com",
            invited_by=self.school_owner,
            batch_id=self.batch_id
        )
        
        invitation2 = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher2@example.com",
            invited_by=self.school_owner,
            batch_id=self.batch_id
        )
        
        self.assertNotEqual(invitation1.token, invitation2.token)
    
    def test_teacher_invitation_default_values(self):
        """Test default values for invitation fields."""
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@example.com",
            invited_by=self.school_owner,
            batch_id=self.batch_id
        )
        
        # Check default values
        self.assertEqual(invitation.role, SchoolRole.TEACHER)
        self.assertEqual(invitation.status, InvitationStatus.PENDING)
        self.assertEqual(invitation.email_delivery_status, EmailDeliveryStatus.NOT_SENT)
        self.assertEqual(invitation.retry_count, 0)
        self.assertFalse(invitation.is_accepted)
        self.assertIsNone(invitation.accepted_at)
        self.assertIsNone(invitation.custom_message)
        
        # Check auto-generated fields
        self.assertIsNotNone(invitation.token)
        self.assertEqual(len(invitation.token), 64)  # UUID4 hex string
        self.assertIsNotNone(invitation.expires_at)
        # Should expire in 7 days by default
        expected_expiry = timezone.now() + timedelta(days=7)
        self.assertAlmostEqual(
            invitation.expires_at, 
            expected_expiry, 
            delta=timedelta(seconds=1)
        )
    
    def test_teacher_invitation_validation(self):
        """Test invitation field validation."""
        # Test valid email
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="valid@example.com",
            invited_by=self.school_owner,
            batch_id=self.batch_id
        )
        invitation.full_clean()  # Should not raise
        
        # Test custom message length validation
        long_message = "x" * 1001  # Assuming max length is 1000
        with self.assertRaises(ValidationError):
            invitation = TeacherInvitation(
                school=self.school,
                email="test@example.com",
                invited_by=self.school_owner,
                custom_message=long_message,
                batch_id=self.batch_id
            )
            invitation.full_clean()
    
    def test_teacher_invitation_duplicate_prevention(self):
        """Test prevention of duplicate active invitations."""
        # Create first invitation
        TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@example.com",
            invited_by=self.school_owner,
            batch_id=self.batch_id
        )
        
        # Try to create duplicate - should fail
        with self.assertRaises(ValidationError):
            invitation = TeacherInvitation(
                school=self.school,
                email="teacher@example.com",
                invited_by=self.school_owner,
                batch_id=uuid.uuid4()  # Different batch
            )
            invitation.full_clean()
    
    def test_teacher_invitation_is_valid_method(self):
        """Test the is_valid() method."""
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@example.com",
            invited_by=self.school_owner,
            batch_id=self.batch_id
        )
        
        # Fresh invitation should be valid
        self.assertTrue(invitation.is_valid())
        
        # Accepted invitation should not be valid
        invitation.is_accepted = True
        invitation.save()
        self.assertFalse(invitation.is_valid())
        
        # Reset and test expired invitation
        invitation.is_accepted = False
        invitation.expires_at = timezone.now() - timedelta(hours=1)
        invitation.save()
        self.assertFalse(invitation.is_valid())
        
        # Test cancelled invitation
        invitation.expires_at = timezone.now() + timedelta(hours=1)
        invitation.status = InvitationStatus.CANCELLED
        invitation.save()
        self.assertFalse(invitation.is_valid())
    
    def test_teacher_invitation_accept_method(self):
        """Test the accept() method."""
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@example.com",
            invited_by=self.school_owner,
            batch_id=self.batch_id
        )
        
        # Accept invitation
        invitation.accept()
        
        self.assertTrue(invitation.is_accepted)
        self.assertEqual(invitation.status, InvitationStatus.ACCEPTED)
        self.assertIsNotNone(invitation.accepted_at)
        
        # Accepting again should be idempotent
        old_accepted_at = invitation.accepted_at
        invitation.accept()
        self.assertEqual(invitation.accepted_at, old_accepted_at)
    
    def test_teacher_invitation_cancel_method(self):
        """Test the cancel() method."""
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@example.com",
            invited_by=self.school_owner,
            batch_id=self.batch_id
        )
        
        # Cancel invitation
        invitation.cancel()
        
        self.assertEqual(invitation.status, InvitationStatus.CANCELLED)
        self.assertFalse(invitation.is_valid())
        
        # Cannot cancel already accepted invitation
        invitation.status = InvitationStatus.PENDING
        invitation.is_accepted = True
        invitation.save()
        
        with self.assertRaises(ValidationError):
            invitation.cancel()
    
    def test_teacher_invitation_email_delivery_tracking(self):
        """Test email delivery status tracking."""
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@example.com",
            invited_by=self.school_owner,
            batch_id=self.batch_id
        )
        
        # Mark as sent
        invitation.mark_email_sent()
        self.assertEqual(invitation.email_delivery_status, EmailDeliveryStatus.SENT)
        self.assertIsNotNone(invitation.email_sent_at)
        
        # Mark as delivered
        invitation.mark_email_delivered()
        self.assertEqual(invitation.email_delivery_status, EmailDeliveryStatus.DELIVERED)
        self.assertIsNotNone(invitation.email_delivered_at)
        
        # Mark as failed
        invitation.mark_email_failed("SMTP error")
        self.assertEqual(invitation.email_delivery_status, EmailDeliveryStatus.FAILED)
        self.assertEqual(invitation.email_failure_reason, "SMTP error")
        self.assertEqual(invitation.retry_count, 1)
    
    def test_teacher_invitation_retry_logic(self):
        """Test email retry logic."""
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@example.com",
            invited_by=self.school_owner,
            batch_id=self.batch_id
        )
        
        # Test retry limits
        self.assertTrue(invitation.can_retry())
        
        # Simulate multiple failures
        for i in range(3):  # Assuming max 3 retries
            invitation.mark_email_failed(f"Error {i+1}")
        
        self.assertFalse(invitation.can_retry())
        self.assertEqual(invitation.retry_count, 3)
    
    def test_teacher_invitation_batch_operations(self):
        """Test batch-related operations."""
        # Create multiple invitations in same batch
        batch_id = uuid.uuid4()
        emails = ["teacher1@example.com", "teacher2@example.com", "teacher3@example.com"]
        
        invitations = []
        for email in emails:
            invitation = TeacherInvitation.objects.create(
                school=self.school,
                email=email,
                invited_by=self.school_owner,
                batch_id=batch_id,
                custom_message="Welcome to our team!"
            )
            invitations.append(invitation)
        
        # Test batch querying
        batch_invitations = TeacherInvitation.objects.filter(batch_id=batch_id)
        self.assertEqual(batch_invitations.count(), 3)
        
        # Test batch status tracking
        for invitation in invitations:
            self.assertEqual(invitation.batch_id, batch_id)
            self.assertEqual(invitation.custom_message, "Welcome to our team!")
    
    def test_teacher_invitation_str_method(self):
        """Test string representation of invitation."""
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@example.com",
            invited_by=self.school_owner,
            batch_id=self.batch_id
        )
        
        expected_str = f"Teacher invitation to teacher@example.com for {self.school.name}"
        self.assertEqual(str(invitation), expected_str)
    
    def test_teacher_invitation_meta_options(self):
        """Test model Meta options."""
        # Test ordering
        invitation1 = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher1@example.com",
            invited_by=self.school_owner,
            batch_id=self.batch_id
        )
        
        # Create second invitation slightly later
        import time
        time.sleep(0.1)
        invitation2 = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher2@example.com",
            invited_by=self.school_owner,
            batch_id=self.batch_id
        )
        
        # Should be ordered by created_at desc (newest first)
        invitations = list(TeacherInvitation.objects.all())
        self.assertEqual(invitations[0], invitation2)
        self.assertEqual(invitations[1], invitation1)


class TeacherInvitationEnumTest(TestCase):
    """Test suite for invitation-related enums."""
    
    def test_invitation_status_choices(self):
        """Test InvitationStatus enum choices."""
        expected_choices = [
            ("pending", "Pending"),
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("viewed", "Viewed"),
            ("accepted", "Accepted"),
            ("declined", "Declined"),
            ("expired", "Expired"),
            ("cancelled", "Cancelled"),
        ]
        
        self.assertEqual(InvitationStatus.choices, expected_choices)
    
    def test_email_delivery_status_choices(self):
        """Test EmailDeliveryStatus enum choices."""
        expected_choices = [
            ("not_sent", "Not Sent"),
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("failed", "Failed"),
            ("bounced", "Bounced"),
        ]
        
        self.assertEqual(EmailDeliveryStatus.choices, expected_choices)


class TeacherInvitationManagerTest(TestCase):
    """Test suite for TeacherInvitation model manager."""
    
    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School",
            description="School for testing invitations"
        )
        
        self.school_owner = CustomUser.objects.create_user(
            email="owner@testschool.com",
            name="School Owner"
        )
    
    def test_active_invitations_queryset(self):
        """Test active_invitations() manager method."""
        batch_id = uuid.uuid4()
        
        # Create various invitations
        active_invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="active@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id
        )
        
        expired_invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="expired@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id,
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        accepted_invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="accepted@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id,
            is_accepted=True,
            status=InvitationStatus.ACCEPTED
        )
        
        cancelled_invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="cancelled@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id,
            status=InvitationStatus.CANCELLED
        )
        
        # Test active invitations query
        active_invitations = TeacherInvitation.objects.active_invitations()
        self.assertIn(active_invitation, active_invitations)
        self.assertNotIn(expired_invitation, active_invitations)
        self.assertNotIn(accepted_invitation, active_invitations)
        self.assertNotIn(cancelled_invitation, active_invitations)
    
    def test_for_school_queryset(self):
        """Test for_school() manager method."""
        school2 = School.objects.create(name="Other School")
        batch_id = uuid.uuid4()
        
        invitation1 = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher1@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id
        )
        
        invitation2 = TeacherInvitation.objects.create(
            school=school2,
            email="teacher2@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id
        )
        
        school_invitations = TeacherInvitation.objects.for_school(self.school)
        self.assertIn(invitation1, school_invitations)
        self.assertNotIn(invitation2, school_invitations)
    
    def test_for_batch_queryset(self):
        """Test for_batch() manager method."""
        batch_id1 = uuid.uuid4()
        batch_id2 = uuid.uuid4()
        
        invitation1 = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher1@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id1
        )
        
        invitation2 = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher2@example.com",
            invited_by=self.school_owner,
            batch_id=batch_id2
        )
        
        batch_invitations = TeacherInvitation.objects.for_batch(batch_id1)
        self.assertIn(invitation1, batch_invitations)
        self.assertNotIn(invitation2, batch_invitations)