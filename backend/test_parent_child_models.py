"""
Test suite for parent-child account management models.
Tests for Issues #111 and #112 - Parent-Child Account Infrastructure & Purchase Approval.
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import (
    School, 
    SchoolMembership, 
    SchoolRole,
    ParentProfile, 
    ParentChildRelationship,
    RelationshipType
)
from finances.models import (
    FamilyBudgetControl,
    PurchaseApprovalRequest,
    PurchaseApprovalStatus,
    PurchaseRequestType,
    PurchaseTransaction,
    TransactionPaymentStatus,
    PricingPlan,
    PlanType
)

User = get_user_model()


@pytest.mark.django_db
class TestParentChildModels:
    """Test cases for parent-child relationship models."""
    
    def setup_method(self):
        """Set up test data."""
        # Create a school
        self.school = School.objects.create(
            name="Test School",
            address="123 Test St",
            contact_email="admin@testschool.com"
        )
        
        # Create users
        self.parent_user = User.objects.create_user(
            email="parent@test.com",
            name="Parent Test"
        )
        
        self.child_user = User.objects.create_user(
            email="child@test.com", 
            name="Child Test"
        )
        
        # Create school memberships
        self.parent_membership = SchoolMembership.objects.create(
            user=self.parent_user,
            school=self.school,
            role=SchoolRole.PARENT,
            is_active=True
        )
        
        self.child_membership = SchoolMembership.objects.create(
            user=self.child_user,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
    
    def test_parent_profile_creation(self):
        """Test creating a parent profile."""
        parent_profile = ParentProfile.objects.create(
            user=self.parent_user,
            email_notifications_enabled=True,
            sms_notifications_enabled=False,
            notification_preferences={"email": True, "push": False},
            default_approval_settings={"auto_approve_under": 50.0}
        )
        
        assert parent_profile.user == self.parent_user
        assert parent_profile.email_notifications_enabled == True
        assert parent_profile.sms_notifications_enabled == False
        assert parent_profile.notification_preferences["email"] == True
        assert parent_profile.default_approval_settings["auto_approve_under"] == 50.0
        assert str(parent_profile) == "Parent Profile: Parent Test"
    
    def test_parent_child_relationship_creation(self):
        """Test creating a parent-child relationship."""
        relationship = ParentChildRelationship.objects.create(
            parent=self.parent_user,
            child=self.child_user,
            school=self.school,
            relationship_type=RelationshipType.PARENT,
            requires_purchase_approval=True,
            requires_session_approval=True
        )
        
        assert relationship.parent == self.parent_user
        assert relationship.child == self.child_user
        assert relationship.school == self.school
        assert relationship.relationship_type == RelationshipType.PARENT
        assert relationship.is_active == True
        assert relationship.requires_purchase_approval == True
        assert relationship.requires_session_approval == True
        assert str(relationship) == "Parent Test -> Child Test (Parent)"
    
    def test_parent_child_relationship_validation(self):
        """Test validation rules for parent-child relationships."""
        # Test that parent and child cannot be the same user
        with pytest.raises(ValidationError) as exc_info:
            relationship = ParentChildRelationship(
                parent=self.parent_user,
                child=self.parent_user,  # Same as parent
                school=self.school,
                relationship_type=RelationshipType.PARENT
            )
            relationship.full_clean()
        
        assert "Parent and child cannot be the same user" in str(exc_info.value)
    
    def test_unique_parent_child_relationship_per_school(self):
        """Test that only one relationship per parent-child-school combination is allowed."""
        # Create first relationship
        ParentChildRelationship.objects.create(
            parent=self.parent_user,
            child=self.child_user,
            school=self.school,
            relationship_type=RelationshipType.PARENT
        )
        
        # Try to create duplicate relationship - should fail
        with pytest.raises(Exception):  # IntegrityError for unique_together constraint
            ParentChildRelationship.objects.create(
                parent=self.parent_user,
                child=self.child_user,
                school=self.school,
                relationship_type=RelationshipType.GUARDIAN
            )


@pytest.mark.django_db 
class TestFamilyBudgetControl:
    """Test cases for family budget control functionality."""
    
    def setup_method(self):
        """Set up test data."""
        # Create a school
        self.school = School.objects.create(
            name="Test School",
            address="123 Test St", 
            contact_email="admin@testschool.com"
        )
        
        # Create users
        self.parent_user = User.objects.create_user(
            email="parent@test.com",
            name="Parent Test"
        )
        
        self.child_user = User.objects.create_user(
            email="child@test.com",
            name="Child Test"
        )
        
        # Create school memberships
        SchoolMembership.objects.create(
            user=self.parent_user,
            school=self.school,
            role=SchoolRole.PARENT,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.child_user,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        # Create parent-child relationship
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent_user,
            child=self.child_user,
            school=self.school,
            relationship_type=RelationshipType.PARENT
        )
    
    def test_family_budget_control_creation(self):
        """Test creating family budget controls."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal('200.00'),
            weekly_budget_limit=Decimal('50.00'),
            auto_approval_threshold=Decimal('25.00'),
            require_approval_for_sessions=True,
            require_approval_for_packages=True
        )
        
        assert budget_control.parent_child_relationship == self.relationship
        assert budget_control.monthly_budget_limit == Decimal('200.00')
        assert budget_control.weekly_budget_limit == Decimal('50.00')
        assert budget_control.auto_approval_threshold == Decimal('25.00')
        assert budget_control.is_active == True
        assert str(budget_control) == "Budget Control: Parent Test -> Child Test"
    
    def test_budget_limits_validation(self):
        """Test budget limit validation logic."""
        budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal('200.00'),
            weekly_budget_limit=Decimal('50.00'),
            auto_approval_threshold=Decimal('25.00')
        )
        
        # Test amount under auto approval threshold
        result = budget_control.check_budget_limits(Decimal('20.00'))
        assert result['allowed'] == True
        assert result['can_auto_approve'] == True
        assert len(result['reasons']) == 0
        
        # Test amount over auto approval threshold but under budget limits
        result = budget_control.check_budget_limits(Decimal('30.00'))
        assert result['allowed'] == True
        assert result['can_auto_approve'] == False
        assert len(result['reasons']) == 0
    
    def test_budget_control_validation(self):
        """Test validation rules for budget controls."""
        # Test that auto approval threshold cannot exceed budget limits
        with pytest.raises(ValidationError) as exc_info:
            budget_control = FamilyBudgetControl(
                parent_child_relationship=self.relationship,
                monthly_budget_limit=Decimal('100.00'),
                auto_approval_threshold=Decimal('150.00')  # Higher than monthly limit
            )
            budget_control.full_clean()
        
        assert "Auto approval threshold cannot be greater than monthly budget limit" in str(exc_info.value)


@pytest.mark.django_db
class TestPurchaseApprovalRequest:
    """Test cases for purchase approval request functionality."""
    
    def setup_method(self):
        """Set up test data."""
        # Create a school
        self.school = School.objects.create(
            name="Test School",
            address="123 Test St",
            contact_email="admin@testschool.com"
        )
        
        # Create users
        self.parent_user = User.objects.create_user(
            email="parent@test.com",
            name="Parent Test"
        )
        
        self.child_user = User.objects.create_user(
            email="child@test.com",
            name="Child Test"
        )
        
        # Create school memberships
        SchoolMembership.objects.create(
            user=self.parent_user,
            school=self.school,
            role=SchoolRole.PARENT,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.child_user,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        # Create parent-child relationship
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent_user,
            child=self.child_user,
            school=self.school,
            relationship_type=RelationshipType.PARENT
        )
        
        # Create a pricing plan
        self.pricing_plan = PricingPlan.objects.create(
            name="Test Package",
            description="Test hour package",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('10.00'),
            price_eur=Decimal('100.00'),
            validity_days=30,
            is_active=True
        )
    
    def test_purchase_approval_request_creation(self):
        """Test creating a purchase approval request."""
        expires_at = timezone.now() + timedelta(hours=24)
        
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child_user,
            parent=self.parent_user,
            parent_child_relationship=self.relationship,
            amount=Decimal('100.00'),
            description="Test hour package purchase",
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=self.pricing_plan,
            expires_at=expires_at
        )
        
        assert approval_request.student == self.child_user
        assert approval_request.parent == self.parent_user
        assert approval_request.parent_child_relationship == self.relationship
        assert approval_request.amount == Decimal('100.00')
        assert approval_request.description == "Test hour package purchase"
        assert approval_request.request_type == PurchaseRequestType.HOURS
        assert approval_request.status == PurchaseApprovalStatus.PENDING
        assert approval_request.pricing_plan == self.pricing_plan
        assert str(approval_request) == "Purchase Request: Child Test -> Parent Test (€100.00)"
    
    def test_purchase_approval_request_validation(self):
        """Test validation rules for approval requests."""
        # Test that student and parent cannot be the same user
        with pytest.raises(ValidationError) as exc_info:
            approval_request = PurchaseApprovalRequest(
                student=self.parent_user,
                parent=self.parent_user,  # Same as student
                parent_child_relationship=self.relationship,
                amount=Decimal('100.00'),
                description="Test purchase",
                request_type=PurchaseRequestType.HOURS
            )
            approval_request.full_clean()
        
        assert "Student and parent cannot be the same user" in str(exc_info.value)
    
    def test_approval_request_actions(self):
        """Test approval and denial actions."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child_user,
            parent=self.parent_user,
            parent_child_relationship=self.relationship,
            amount=Decimal('100.00'),
            description="Test purchase",
            request_type=PurchaseRequestType.HOURS,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Test approval
        approval_request.approve(parent_notes="Approved for good grades")
        approval_request.refresh_from_db()
        
        assert approval_request.status == PurchaseApprovalStatus.APPROVED
        assert approval_request.parent_notes == "Approved for good grades"
        assert approval_request.responded_at is not None
        
        # Create another request to test denial
        denial_request = PurchaseApprovalRequest.objects.create(
            student=self.child_user,
            parent=self.parent_user,
            parent_child_relationship=self.relationship,
            amount=Decimal('50.00'),
            description="Another test purchase",
            request_type=PurchaseRequestType.HOURS,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Test denial
        denial_request.deny(parent_notes="Too much spending this month")
        denial_request.refresh_from_db()
        
        assert denial_request.status == PurchaseApprovalStatus.DENIED
        assert denial_request.parent_notes == "Too much spending this month"
        assert denial_request.responded_at is not None
    
    def test_approval_request_expiration(self):
        """Test approval request expiration functionality."""
        # Create an expired request
        expired_request = PurchaseApprovalRequest.objects.create(
            student=self.child_user,
            parent=self.parent_user,
            parent_child_relationship=self.relationship,
            amount=Decimal('100.00'),
            description="Expired request",
            request_type=PurchaseRequestType.HOURS,
            expires_at=timezone.now() - timedelta(hours=1)  # Already expired
        )
        
        assert expired_request.is_expired == True
        
        # Test marking as expired
        expired_request.mark_expired()
        expired_request.refresh_from_db()
        
        assert expired_request.status == PurchaseApprovalStatus.EXPIRED
        assert expired_request.responded_at is not None
    
    def test_approval_request_automatic_expiration_setting(self):
        """Test that approval requests automatically set expiration time."""
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child_user,
            parent=self.parent_user,
            parent_child_relationship=self.relationship,
            amount=Decimal('100.00'),
            description="Test purchase",
            request_type=PurchaseRequestType.HOURS
            # Note: not setting expires_at explicitly
        )
        
        # Should automatically set expires_at to 24 hours from now
        assert approval_request.expires_at is not None
        time_diff = approval_request.expires_at - approval_request.created_at
        # Should be approximately 24 hours (allowing for small time differences)
        assert abs(time_diff.total_seconds() - 24 * 3600) < 60  # Within 1 minute tolerance


@pytest.mark.django_db
class TestModelIntegration:
    """Test integration between all parent-child models."""
    
    def setup_method(self):
        """Set up comprehensive test data."""
        # Create a school
        self.school = School.objects.create(
            name="Test School",
            address="123 Test St",
            contact_email="admin@testschool.com"
        )
        
        # Create users
        self.parent_user = User.objects.create_user(
            email="parent@test.com",
            name="Parent Test"
        )
        
        self.child_user = User.objects.create_user(
            email="child@test.com",
            name="Child Test"
        )
        
        # Create school memberships
        SchoolMembership.objects.create(
            user=self.parent_user,
            school=self.school,
            role=SchoolRole.PARENT,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.child_user,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        # Create parent profile
        self.parent_profile = ParentProfile.objects.create(
            user=self.parent_user,
            email_notifications_enabled=True,
            default_approval_settings={"auto_approve_under": 30.0}
        )
        
        # Create parent-child relationship
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent_user,
            child=self.child_user,
            school=self.school,
            relationship_type=RelationshipType.PARENT
        )
        
        # Create budget control
        self.budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal('300.00'),
            weekly_budget_limit=Decimal('75.00'),
            auto_approval_threshold=Decimal('30.00')
        )
    
    def test_complete_approval_workflow(self):
        """Test a complete purchase approval workflow."""
        # Create approval request
        approval_request = PurchaseApprovalRequest.objects.create(
            student=self.child_user,
            parent=self.parent_user,
            parent_child_relationship=self.relationship,
            amount=Decimal('50.00'),  # Over auto-approval threshold
            description="Math tutoring package",
            request_type=PurchaseRequestType.HOURS,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Check budget limits
        budget_check = self.budget_control.check_budget_limits(approval_request.amount)
        assert budget_check['allowed'] == True
        assert budget_check['can_auto_approve'] == False  # Over threshold
        
        # Parent approves the request
        approval_request.approve(parent_notes="Approved for math improvement")
        
        # Create a purchase transaction linked to the approval
        transaction = PurchaseTransaction.objects.create(
            student=self.child_user,
            transaction_type="package",
            amount=approval_request.amount,
            payment_status=TransactionPaymentStatus.COMPLETED,
            approval_request=approval_request
        )
        
        # Verify the complete workflow
        approval_request.refresh_from_db()
        assert approval_request.status == PurchaseApprovalStatus.APPROVED
        assert transaction.approval_request == approval_request
        assert transaction.amount == approval_request.amount
        
        # Verify relationships are maintained
        assert approval_request.parent_child_relationship == self.relationship
        assert self.relationship.budget_control == self.budget_control
    
    def test_parent_profile_children_count(self):
        """Test that parent profile correctly counts children."""
        # Should have 1 child from setup
        assert self.parent_profile.user.children_relationships.filter(is_active=True).count() == 1
        
        # Create another child
        child2_user = User.objects.create_user(
            email="child2@test.com",
            name="Second Child"
        )
        
        SchoolMembership.objects.create(
            user=child2_user,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        ParentChildRelationship.objects.create(
            parent=self.parent_user,
            child=child2_user,
            school=self.school,
            relationship_type=RelationshipType.PARENT
        )
        
        # Should now have 2 children
        assert self.parent_profile.user.children_relationships.filter(is_active=True).count() == 2


if __name__ == "__main__":
    pytest.main([__file__])