"""
Test cases for purchase approval and spending control models.

This module tests the FamilyBudgetControl and PurchaseApprovalRequest models
that implement the parent-child purchase approval workflow.
"""

from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import CustomUser, School, ParentChildRelationship, RelationshipType, TeacherProfile
from finances.models import (
    FamilyBudgetControl,
    PurchaseApprovalRequest,
    PurchaseTransaction,
    PricingPlan,
    ClassSession,
    TransactionPaymentStatus,
    PurchaseRequestType,
    PurchaseApprovalStatus,
    SessionType,
    PlanType,
)


class FamilyBudgetControlModelTest(TestCase):
    """Test cases for the FamilyBudgetControl model."""

    def setUp(self):
        """Set up test data."""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )

        # Create parent and child users
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Parent User"
        )
        self.child = CustomUser.objects.create_user(
            email="child@test.com",
            name="Child User"
        )

        # Create parent-child relationship
        self.parent_child_relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )

    def test_budget_control_creation(self):
        """Test creating a budget control with default values."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship
        )

        self.assertEqual(budget_control.auto_approval_threshold, Decimal('0.00'))
        self.assertTrue(budget_control.require_approval_for_sessions)
        self.assertTrue(budget_control.require_approval_for_packages)
        self.assertTrue(budget_control.is_active)
        self.assertIsNone(budget_control.monthly_budget_limit)
        self.assertIsNone(budget_control.weekly_budget_limit)

    def test_budget_control_with_limits(self):
        """Test creating a budget control with specific limits."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('200.00'),
            weekly_budget_limit=Decimal('50.00'),
            auto_approval_threshold=Decimal('20.00')
        )

        self.assertEqual(budget_control.monthly_budget_limit, Decimal('200.00'))
        self.assertEqual(budget_control.weekly_budget_limit, Decimal('50.00'))
        self.assertEqual(budget_control.auto_approval_threshold, Decimal('20.00'))

    def test_budget_control_str_representation(self):
        """Test string representation of budget control."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship
        )

        expected_str = "Budget Control: Parent User -> Child User"
        self.assertEqual(str(budget_control), expected_str)

    def test_current_monthly_spending_calculation(self):
        """Test calculation of current monthly spending."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('200.00')
        )

        # Create completed transactions for this month
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type='package',
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type='package',
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )

        # Create a pending transaction (should not be included)
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type='package',
            amount=Decimal('20.00'),
            payment_status=TransactionPaymentStatus.PENDING
        )

        monthly_spending = budget_control.current_monthly_spending
        self.assertEqual(monthly_spending, Decimal('80.00'))

    def test_current_weekly_spending_calculation(self):
        """Test calculation of current weekly spending."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            weekly_budget_limit=Decimal('50.00')
        )

        # Create completed transaction for this week
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type='package',
            amount=Decimal('25.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )

        weekly_spending = budget_control.current_weekly_spending
        self.assertEqual(weekly_spending, Decimal('25.00'))

    def test_check_budget_limits_within_limits(self):
        """Test budget limit check when purchase is within limits."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('200.00'),
            weekly_budget_limit=Decimal('50.00'),
            auto_approval_threshold=Decimal('20.00')
        )

        # Test amount within all limits
        result = budget_control.check_budget_limits(Decimal('15.00'))
        
        self.assertTrue(result['allowed'])
        self.assertTrue(result['can_auto_approve'])
        self.assertEqual(len(result['reasons']), 0)

    def test_check_budget_limits_exceeds_monthly(self):
        """Test budget limit check when purchase exceeds monthly limit."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('100.00'),
            auto_approval_threshold=Decimal('20.00')
        )

        # Create existing spending
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type='package',
            amount=Decimal('80.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )

        # Test amount that would exceed monthly limit
        result = budget_control.check_budget_limits(Decimal('30.00'))
        
        self.assertFalse(result['allowed'])
        self.assertFalse(result['can_auto_approve'])
        self.assertIn("monthly budget limit", result['reasons'][0])

    def test_check_budget_limits_exceeds_weekly(self):
        """Test budget limit check when purchase exceeds weekly limit."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            weekly_budget_limit=Decimal('40.00'),
            auto_approval_threshold=Decimal('20.00')
        )

        # Create existing spending this week
        PurchaseTransaction.objects.create(
            student=self.child,
            transaction_type='package',
            amount=Decimal('30.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )

        # Test amount that would exceed weekly limit
        result = budget_control.check_budget_limits(Decimal('15.00'))
        
        self.assertFalse(result['allowed'])
        self.assertFalse(result['can_auto_approve'])
        self.assertIn("weekly budget limit", result['reasons'][0])

    def test_check_budget_limits_exceeds_auto_approval(self):
        """Test budget limit check when purchase exceeds auto approval threshold."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('200.00'),
            auto_approval_threshold=Decimal('20.00')
        )

        # Test amount that exceeds auto approval but not budget limits
        result = budget_control.check_budget_limits(Decimal('25.00'))
        
        self.assertTrue(result['allowed'])
        self.assertFalse(result['can_auto_approve'])
        self.assertEqual(len(result['reasons']), 0)

    def test_clean_validation_auto_approval_greater_than_monthly(self):
        """Test validation when auto approval threshold exceeds monthly limit."""
        budget_control = FamilyBudgetControl(
            parent_child_relationship=self.parent_child_relationship,
            monthly_budget_limit=Decimal('100.00'),
            auto_approval_threshold=Decimal('150.00')
        )

        with self.assertRaises(ValidationError) as context:
            budget_control.clean()

        self.assertIn("Auto approval threshold cannot be greater than monthly budget limit", 
                     str(context.exception))

    def test_clean_validation_auto_approval_greater_than_weekly(self):
        """Test validation when auto approval threshold exceeds weekly limit."""
        budget_control = FamilyBudgetControl(
            parent_child_relationship=self.parent_child_relationship,
            weekly_budget_limit=Decimal('30.00'),
            auto_approval_threshold=Decimal('50.00')
        )

        with self.assertRaises(ValidationError) as context:
            budget_control.clean()

        self.assertIn("Auto approval threshold cannot be greater than weekly budget limit",
                     str(context.exception))


class PurchaseApprovalRequestModelTest(TestCase):
    """Test cases for the PurchaseApprovalRequest model."""

    def setUp(self):
        """Set up test data."""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )

        # Create parent and child users
        self.parent = CustomUser.objects.create_user(
            email="parent@test.com",
            name="Parent User"
        )
        self.child = CustomUser.objects.create_user(
            email="child@test.com",
            name="Child User"
        )

        # Create parent-child relationship
        self.parent_child_relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            relationship_type=RelationshipType.PARENT,
            school=self.school
        )

        # Create pricing plan
        self.pricing_plan = PricingPlan.objects.create(
            name="Test Package",
            description="A test hour package",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('10.00'),
            price_eur=Decimal('100.00'),
            validity_days=30
        )

    def test_approval_request_creation(self):
        """Test creating a purchase approval request."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description="Request for 10-hour package",
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan
        )

        self.assertEqual(approval_request.status, PurchaseApprovalStatus.PENDING)
        self.assertIsNotNone(approval_request.expires_at)
        self.assertIsNone(approval_request.responded_at)
        self.assertEqual(approval_request.parent_notes, "")

    def test_approval_request_str_representation(self):
        """Test string representation of approval request."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description="Request for 10-hour package",
            request_type=PurchaseRequestType.HOURS
        )

        expected_str = "Purchase Request: Child User -> Parent User (€100.00)"
        self.assertEqual(str(approval_request), expected_str)

    def test_approval_request_auto_expiration_setting(self):
        """Test that expiration time is set automatically if not provided."""
        now = timezone.now()
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description="Request for 10-hour package",
            request_type=PurchaseRequestType.HOURS
        )

        # Should be set to approximately 24 hours from now
        expected_expiry = now + timedelta(hours=24)
        time_diff = abs((approval_request.expires_at - expected_expiry).total_seconds())
        self.assertLess(time_diff, 10)  # Within 10 seconds

    def test_is_expired_property(self):
        """Test the is_expired property."""
        # Create a request that expires in the future
        future_expiry = timezone.now() + timedelta(hours=1)
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description="Request for 10-hour package",
            request_type=PurchaseRequestType.HOURS,
            expires_at=future_expiry
        )

        self.assertFalse(approval_request.is_expired)

        # Create a request that has already expired
        past_expiry = timezone.now() - timedelta(hours=1)
        expired_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('50.00'),
            description="Expired request",
            request_type=PurchaseRequestType.HOURS,
            expires_at=past_expiry
        )

        self.assertTrue(expired_request.is_expired)

    def test_time_remaining_property(self):
        """Test the time_remaining property."""
        # Create a request that expires in 2 hours
        future_expiry = timezone.now() + timedelta(hours=2)
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description="Request for 10-hour package",
            request_type=PurchaseRequestType.HOURS,
            expires_at=future_expiry
        )

        time_remaining = approval_request.time_remaining
        # Should be approximately 2 hours
        self.assertGreater(time_remaining.total_seconds(), 7000)  # More than 1h 55m
        self.assertLess(time_remaining.total_seconds(), 8000)     # Less than 2h 15m

    def test_approve_method(self):
        """Test approving a purchase request."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description="Request for 10-hour package",
            request_type=PurchaseRequestType.HOURS
        )

        parent_notes = "Approved for educational purposes"
        approval_request.approve(parent_notes)

        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.APPROVED)
        self.assertIsNotNone(approval_request.responded_at)
        self.assertEqual(approval_request.parent_notes, parent_notes)

    def test_deny_method(self):
        """Test denying a purchase request."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description="Request for 10-hour package",
            request_type=PurchaseRequestType.HOURS
        )

        parent_notes = "Too expensive this month"
        approval_request.deny(parent_notes)

        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.DENIED)
        self.assertIsNotNone(approval_request.responded_at)
        self.assertEqual(approval_request.parent_notes, parent_notes)

    def test_cancel_method(self):
        """Test cancelling a purchase request."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description="Request for 10-hour package",
            request_type=PurchaseRequestType.HOURS
        )

        approval_request.cancel()

        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.CANCELLED)
        self.assertIsNotNone(approval_request.responded_at)

    def test_mark_expired_method(self):
        """Test marking a request as expired."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description="Request for 10-hour package",
            request_type=PurchaseRequestType.HOURS
        )

        approval_request.mark_expired()

        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, PurchaseApprovalStatus.EXPIRED)
        self.assertIsNotNone(approval_request.responded_at)

    def test_approve_already_processed_request(self):
        """Test that approving an already processed request raises error."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description="Request for 10-hour package",
            request_type=PurchaseRequestType.HOURS
        )

        # First approval should work
        approval_request.approve("Initial approval")

        # Second approval should fail
        with self.assertRaises(ValidationError) as context:
            approval_request.approve("Second approval")

        self.assertIn("Only pending requests can be approved", str(context.exception))

    def test_approve_expired_request(self):
        """Test that approving an expired request raises error."""
        past_expiry = timezone.now() - timedelta(hours=1)
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description="Request for 10-hour package",
            request_type=PurchaseRequestType.HOURS,
            expires_at=past_expiry
        )

        with self.assertRaises(ValidationError) as context:
            approval_request.approve("Too late")

        self.assertIn("Cannot approve an expired request", str(context.exception))

    def test_clean_validation_same_user(self):
        """Test validation that student and parent cannot be the same user."""
        approval_request = PurchaseApprovalRequest(
            student=self.parent,  # Same as parent
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description="Invalid request",
            request_type=PurchaseRequestType.HOURS
        )

        with self.assertRaises(ValidationError) as context:
            approval_request.clean()

        self.assertIn("Student and parent cannot be the same user", str(context.exception))

    def test_clean_validation_mismatched_relationship(self):
        """Test validation that parent-child relationship matches users."""
        # Create another parent
        other_parent = CustomUser.objects.create_user(
            email="other_parent@test.com",
            name="Other Parent"
        )

        approval_request = PurchaseApprovalRequest(
            student=self.child,
            parent=other_parent,  # Different from relationship
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('100.00'),
            description="Invalid request",
            request_type=PurchaseRequestType.HOURS
        )

        with self.assertRaises(ValidationError) as context:
            approval_request.clean()

        self.assertIn("Parent-child relationship must match the student and parent", 
                     str(context.exception))

    def test_approval_request_with_class_session(self):
        """Test creating approval request for a class session."""
        # Create teacher profile
        teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com",
            name="Teacher User"
        )
        teacher_profile = TeacherProfile.objects.create(
            user=teacher_user
        )

        # Create class session
        class_session = ClassSession.objects.create(
            teacher=teacher_profile,
            school=self.school,
            date=timezone.now().date(),
            start_time="14:00",
            end_time="15:00",
            session_type=SessionType.INDIVIDUAL,
            grade_level="10"
        )

        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child,
            parent=self.parent,
            parent_child_relationship=self.parent_child_relationship,
            amount=Decimal('25.00'),
            description="Request for individual session",
            request_type=PurchaseRequestType.SESSION,
            class_session=class_session
        )

        self.assertEqual(approval_request.class_session, class_session)
        self.assertEqual(approval_request.request_type, PurchaseRequestType.SESSION)