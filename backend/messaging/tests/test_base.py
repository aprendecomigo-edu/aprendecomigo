"""
Shared base classes and utilities for messaging app business logic tests.

Provides common setup patterns and utility methods to reduce code duplication
and ensure consistent test data creation across all messaging tests.
"""

from datetime import timedelta
from decimal import Decimal
import uuid

from django.test import TestCase
from django.utils import timezone

from accounts.models import CustomUser, InvitationStatus, School, SchoolMembership, SchoolRole, TeacherInvitation
from finances.models import PurchaseTransaction, StudentAccountBalance, TransactionPaymentStatus, TransactionType
from messaging.models import Notification, NotificationType


class MessagingTestBase(TestCase):
    """
    Base test class for messaging app business logic tests.

    Provides common setup methods and utilities for creating consistent
    test data across different test modules.
    """

    def setUp(self):
        """Set up common test data used across messaging tests."""
        super().setUp()
        self._create_school_and_users()

    def _create_school_and_users(self):
        """Create standard school and user setup."""
        # Create test school
        self.school = School.objects.create(
            name="Test School", description="A test school for messaging tests", contact_email="support@testschool.com"
        )

        # Create admin user
        self.admin_user = CustomUser.objects.create_user(
            email="admin@testschool.com", name="Test Admin", first_login_completed=True
        )

        # Create admin membership
        SchoolMembership.objects.create(user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN)

        # Create test student
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student",
            first_login_completed=True,  # Base test student has completed onboarding
        )

        # Create student membership
        SchoolMembership.objects.create(user=self.student, school=self.school, role=SchoolRole.STUDENT, is_active=True)

    def create_student_balance(self, student=None, hours_purchased=10.0, hours_consumed=0.0, balance_amount=100.0):
        """
        Create a student account balance for testing.

        Args:
            student: Student user (defaults to self.student)
            hours_purchased: Hours purchased (default: 10.0)
            hours_consumed: Hours consumed (default: 0.0)
            balance_amount: Balance amount (default: 100.0)

        Returns:
            StudentAccountBalance instance
        """
        if student is None:
            student = self.student

        return StudentAccountBalance.objects.create(
            student=student,
            hours_purchased=Decimal(str(hours_purchased)),
            hours_consumed=Decimal(str(hours_consumed)),
            balance_amount=Decimal(str(balance_amount)),
        )

    def create_purchase_transaction(
        self, student=None, transaction_type=TransactionType.PACKAGE, amount=50.0, expires_at_days=7
    ):
        """
        Create a purchase transaction for testing.

        Args:
            student: Student user (defaults to self.student)
            transaction_type: Type of transaction (default: PACKAGE)
            amount: Transaction amount (default: 50.0)
            expires_at_days: Days until expiration (default: 7)

        Returns:
            PurchaseTransaction instance
        """
        if student is None:
            student = self.student

        return PurchaseTransaction.objects.create(
            student=student,
            transaction_type=transaction_type,
            amount=Decimal(str(amount)),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timedelta(days=expires_at_days),
        )

    def create_notification(
        self,
        user=None,
        notification_type=NotificationType.LOW_BALANCE,
        title="Test Notification",
        message="Test message",
        is_read=False,
        metadata=None,
    ):
        """
        Create a notification for testing.

        Args:
            user: User to receive notification (defaults to self.student)
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            is_read: Whether notification is read
            metadata: Optional metadata dictionary

        Returns:
            Notification instance
        """
        if user is None:
            user = self.student

        if metadata is None:
            metadata = {}

        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            is_read=is_read,
            metadata=metadata,
        )

    def create_teacher_invitation(
        self,
        email="teacher@test.com",
        role=SchoolRole.TEACHER,
        status=InvitationStatus.PENDING,
        expires_in_days=7,
        custom_message=None,
    ):
        """
        Create a teacher invitation for testing.

        Args:
            email: Email address for invitation
            role: School role for invitation
            status: Invitation status
            expires_in_days: Days until invitation expires
            custom_message: Optional custom message

        Returns:
            TeacherInvitation instance
        """
        return TeacherInvitation.objects.create(
            school=self.school,
            email=email,
            invited_by=self.admin_user,
            role=role,
            status=status,
            custom_message=custom_message,
            batch_id=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=expires_in_days),
        )

    def create_school_user(self, email, name, role=SchoolRole.STUDENT, first_login_completed=True):
        """
        Create a user with school membership.

        Args:
            email: User email
            name: User name
            role: School role (default: STUDENT)
            first_login_completed: Whether first login is completed

        Returns:
            CustomUser instance
        """
        user = CustomUser.objects.create_user(email=email, name=name, first_login_completed=first_login_completed)

        SchoolMembership.objects.create(user=user, school=self.school, role=role)

        return user

    def create_student_user(self, email, name, first_login_completed=True):
        """Create a student user with school membership."""
        return self.create_school_user(email, name, SchoolRole.STUDENT, first_login_completed)

    def create_teacher_user(self, email, name, first_login_completed=True):
        """Create a teacher user with school membership."""
        return self.create_school_user(email, name, SchoolRole.TEACHER, first_login_completed)

    def create_other_school(self, name="Other School", description="Another test school"):
        """
        Create another school for multi-tenancy testing.

        Args:
            name: School name
            description: School description

        Returns:
            Tuple of (School, admin_user)
        """
        other_school = School.objects.create(name=name, description=description)

        other_admin = CustomUser.objects.create_user(
            email=f"admin@{name.lower().replace(' ', '')}.com", name=f"{name} Admin"
        )

        SchoolMembership.objects.create(user=other_admin, school=other_school, role=SchoolRole.SCHOOL_ADMIN)

        return other_school, other_admin


class SecurityTestMixin:
    """
    Mixin providing common security test utilities.

    Used for testing XSS prevention, template injection, and other security concerns.
    """

    # Common XSS attack vectors for parameterized testing
    XSS_ATTACK_VECTORS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert('xss')",
        "<svg onload=alert(1)>",
        "<%2Fscript><script>alert(1)</script>",
        "<iframe src=javascript:alert(1)></iframe>",
    ]

    # Template injection attack vectors
    TEMPLATE_INJECTION_VECTORS = [
        "{{ ''.__class__.__mro__[1].__subclasses__() }}",
        "{% load os %}{{ os.system('ls') }}",
        "{{ request.META }}",
        "{{ settings.SECRET_KEY }}",
        "{% import os %}",
        '{{ eval(\'__import__("os").system("ls")\') }}',
        "{{ __import__('os').system('whoami') }}",
    ]

    # Dangerous template tags and filters
    DANGEROUS_TEMPLATE_PATTERNS = [
        "{% load subprocess %}",
        "{% load os %}",
        "{% include '/etc/passwd' %}",
        "{% extends '/etc/hosts' %}",
        "{% ssi '/etc/passwd' %}",
        "{{ name|exec }}",
        "{{ name|eval }}",
        "{{ name|import }}",
        "{{ name|subprocess }}",
    ]

    def assert_content_escaped(self, content, original_dangerous_content):
        """
        Assert that dangerous content has been properly escaped.

        Args:
            content: The processed content to check
            original_dangerous_content: The original dangerous input
        """
        # Common XSS patterns should be escaped
        self.assertNotIn("<script>", content.lower())
        self.assertNotIn("javascript:", content.lower())
        self.assertNotIn("onerror=", content.lower())
        self.assertNotIn("onload=", content.lower())

        # Should contain escaped versions
        if "<script>" in original_dangerous_content.lower():
            self.assertIn("&lt;script&gt;", content.lower())
