"""
Test fixtures for the finances app.

This module provides comprehensive fixture builders to create test data with
proper relationships and database constraints for all finance-related models.

The fixtures resolve the following issues identified in #181:
- StudentProfile missing school associations (lines 142-148)
- GuardianStudentRelationship incomplete setup (lines 155-162)
- SchoolMembership not created for test users (lines 109-132)
- PricingPlan missing required fields (lines 179-189)
- StudentAccountBalance missing student relationships (lines 191-197)

Usage Examples:
    # For comprehensive test setup:
    fixtures = FinanceTestFixtures.create_complete_test_environment()

    # For minimal test setup:
    school_fixtures = FinanceTestFixtures.create_minimal_school_setup()

    # For specific entities:
    student_fixtures = FinanceTestFixtures.create_student_with_profile()

Created to resolve issue #181 - Test Setup and Fixture Issues.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid

from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import (
    Course,
    EducationalSystem,
    EducationalSystemType,
    GuardianStudentRelationship,
    GuardianProfile,
    RelationshipType,
    School,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
    TeacherCourse,
    TeacherProfile,
)
from finances.models import (
    ClassSession,
    CompensationRuleType,
    FamilyBudgetControl,
    HourConsumption,
    PaymentFrequency,
    PlanType,
    PricingPlan,
    PurchaseApprovalRequest,
    PurchaseRequestType,
    PurchaseTransaction,
    Receipt,
    SchoolBillingSettings,
    SessionStatus,
    SessionType,
    StoredPaymentMethod,
    StudentAccountBalance,
    TeacherCompensationRule,
    TransactionPaymentStatus,
    TransactionType,
    TrialCostAbsorption,
)

User = get_user_model()


class FinanceTestFixtures:
    """
    Comprehensive test fixture builder for the finances app.

    Creates all necessary models with proper relationships and complete
    database constraint satisfaction to resolve test setup failures.
    """

    @staticmethod
    def create_complete_test_environment():
        """
        Create a complete test environment with all necessary models and relationships.

        This method creates a full testing ecosystem with:
        - Educational system and school infrastructure
        - Multiple user types with proper profiles and memberships
        - Financial models with complete business relationships
        - Realistic test data that satisfies all database constraints

        Returns:
            dict: Dictionary with all created fixtures indexed by meaningful keys:
                - Infrastructure: educational_system, school, billing_settings
                - Users: teacher_user, student_user, parent_user, admin_user
                - Profiles: teacher_profile, student_profile, guardian_profile
                - Relationships: guardian_student_relationship, teacher_course
                - Financial: pricing_plan, student_account_balance, purchase_transaction

        Raises:
            ValidationError: If any model validation fails
            IntegrityError: If database constraints are violated
        """
        # Create Educational System first (required for StudentProfile)
        # Try to use existing EducationalSystem first (performance optimization)
        educational_system, created = EducationalSystem.objects.get_or_create(
            code=EducationalSystemType.PORTUGAL,
            defaults={"name": "Portuguese System", "description": "Portuguese educational system for testing"},
        )

        # Create School
        school = School.objects.create(
            name="Test School",
            description="Test School Description",
            address="123 Test Street",
            phone_number="+351912345678",
            contact_email="testschool@example.com",
        )

        # Create School Billing Settings
        billing_settings = SchoolBillingSettings.objects.create(
            school=school,
            trial_cost_absorption=TrialCostAbsorption.SCHOOL,
            teacher_payment_frequency=PaymentFrequency.MONTHLY,
            payment_day_of_month=15,
        )

        # Create Users
        teacher_user = User.objects.create_user(email="teacher@test.com", password="testpass123", name="Test Teacher")

        student_user = User.objects.create_user(email="student@test.com", password="testpass123", name="Test Student")

        parent_user = User.objects.create_user(email="parent@test.com", password="testpass123", name="Test Parent")

        admin_user = User.objects.create_user(
            email="admin@test.com", password="testpass123", name="Test Admin", is_staff=True
        )

        # Create School Memberships
        teacher_membership = SchoolMembership.objects.create(user=teacher_user, school=school, role=SchoolRole.TEACHER)

        student_membership = SchoolMembership.objects.create(user=student_user, school=school, role=SchoolRole.STUDENT)

        parent_membership = SchoolMembership.objects.create(user=parent_user, school=school, role=SchoolRole.GUARDIAN)

        admin_membership = SchoolMembership.objects.create(user=admin_user, school=school, role=SchoolRole.SCHOOL_OWNER)

        # Create Profiles
        teacher_profile = TeacherProfile.objects.create(
            user=teacher_user, bio="Test teacher bio", hourly_rate=Decimal("25.00")
        )

        student_profile = StudentProfile.objects.create(
            user=student_user,
            educational_system=educational_system,  # Required field
            school_year="7",
            birth_date=date(2008, 5, 15),
        )

        guardian_profile = GuardianProfile.objects.create(user=parent_user)

        # Create Guardian-Student Relationship
        guardian_student_relationship = GuardianStudentRelationship.objects.create(
            guardian=parent_user,
            student=student_user,
            school=school,
            relationship_type=RelationshipType.PARENT,
        )

        # Create Course
        course = Course.objects.create(
            name="Mathematics",
            description="Math course for grade 7",
            educational_system=educational_system,
            education_level="7",
        )

        # Create Teacher-Course association
        teacher_course = TeacherCourse.objects.create(teacher=teacher_profile, course=course, is_active=True)

        # Create Pricing Plan with ALL required fields
        pricing_plan = PricingPlan.objects.create(
            name="Test Package",
            description="Test package description",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.00"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1,
            is_active=True,
        )

        # Create Student Account Balance
        student_account_balance = StudentAccountBalance.objects.create(
            student=student_user,
            hours_purchased=Decimal("10.00"),
            hours_consumed=Decimal("2.00"),
            balance_amount=Decimal("80.00"),
        )

        # Create Purchase Transaction
        purchase_transaction = PurchaseTransaction.objects.create(
            student=student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id=f"pi_test_{uuid.uuid4().hex[:16]}",
            stripe_customer_id=f"cus_test_{uuid.uuid4().hex[:16]}",
        )

        # Create Teacher Compensation Rule
        teacher_compensation_rule = TeacherCompensationRule.objects.create(
            teacher=teacher_profile,
            school=school,
            rule_type=CompensationRuleType.GRADE_SPECIFIC,
            grade_level="7",
            rate_per_hour=Decimal("20.00"),
            is_active=True,
            effective_from=date.today(),
        )

        # Create Class Session
        session_date = timezone.now().date()
        class_session = ClassSession.objects.create(
            teacher=teacher_profile,
            school=school,
            date=session_date,
            start_time=datetime.strptime("14:00", "%H:%M").time(),
            end_time=datetime.strptime("15:00", "%H:%M").time(),
            session_type=SessionType.INDIVIDUAL,
            grade_level="7",
            student_count=1,
            is_trial=False,
            status=SessionStatus.SCHEDULED,
        )

        # Add student to session
        class_session.students.add(student_user)

        # Create Family Budget Control
        family_budget_control = FamilyBudgetControl.objects.create(
            guardian_student_relationship=guardian_student_relationship,
            monthly_budget_limit=Decimal("200.00"),
            weekly_budget_limit=Decimal("50.00"),
            auto_approval_threshold=Decimal("25.00"),
            require_approval_for_sessions=True,
            require_approval_for_packages=True,
            is_active=True,
        )

        # Create Purchase Approval Request
        approval_request = PurchaseApprovalRequest.objects.create(
            student=student_user,
            guardian=parent_user,
            guardian_student_relationship=guardian_student_relationship,
            amount=Decimal("50.00"),
            description="Test approval request",
            request_type=PurchaseRequestType.HOURS,
            pricing_plan=pricing_plan,
            expires_at=timezone.now() + timedelta(hours=24),
        )

        # Create Stored Payment Method
        stored_payment_method = StoredPaymentMethod.objects.create(
            student=student_user,
            stripe_payment_method_id=f"pm_test_{uuid.uuid4().hex[:16]}",
            stripe_customer_id=f"cus_test_{uuid.uuid4().hex[:16]}",
            card_brand="visa",
            card_last4="4242",
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True,
        )

        # Create Receipt
        receipt = Receipt.objects.create(
            student=student_user, transaction=purchase_transaction, amount=purchase_transaction.amount, is_valid=True
        )

        # Create Hour Consumption
        hour_consumption = HourConsumption.objects.create(
            student_account=student_account_balance,
            class_session=class_session,
            purchase_transaction=purchase_transaction,
            hours_consumed=Decimal("1.00"),
            hours_originally_reserved=Decimal("1.00"),
        )

        return {
            "educational_system": educational_system,
            "school": school,
            "billing_settings": billing_settings,
            "teacher_user": teacher_user,
            "student_user": student_user,
            "parent_user": parent_user,
            "admin_user": admin_user,
            "teacher_membership": teacher_membership,
            "student_membership": student_membership,
            "parent_membership": parent_membership,
            "admin_membership": admin_membership,
            "teacher_profile": teacher_profile,
            "student_profile": student_profile,
            "guardian_profile": guardian_profile,
            "parent_child_relationship": parent_child_relationship,
            "course": course,
            "teacher_course": teacher_course,
            "pricing_plan": pricing_plan,
            "student_account_balance": student_account_balance,
            "purchase_transaction": purchase_transaction,
            "teacher_compensation_rule": teacher_compensation_rule,
            "class_session": class_session,
            "family_budget_control": family_budget_control,
            "approval_request": approval_request,
            "stored_payment_method": stored_payment_method,
            "receipt": receipt,
            "hour_consumption": hour_consumption,
        }

    @staticmethod
    def create_minimal_school_setup():
        """
        Create minimal school setup with basic relationships.

        Returns:
            dict: Dictionary with basic fixtures
        """
        # Try to use existing EducationalSystem first
        educational_system = EducationalSystem.objects.filter(code=EducationalSystemType.PORTUGAL).first()

        if not educational_system:
            educational_system = EducationalSystem.objects.create(
                name="Test System", code=EducationalSystemType.PORTUGAL, description="Minimal test system"
            )

        school = School.objects.create(name="Minimal School", description="Minimal test school")

        return {
            "educational_system": educational_system,
            "school": school,
        }

    @staticmethod
    def create_teacher_with_profile(email="teacher@test.com", school=None):
        """
        Create a teacher with proper profile and school membership.

        Args:
            email: Email for the teacher
            school: School instance (will create one if None)

        Returns:
            dict: Dictionary with teacher fixtures
        """
        if school is None:
            school_fixtures = FinanceTestFixtures.create_minimal_school_setup()
            school = school_fixtures["school"]

        teacher_user = User.objects.create_user(
            email=email,
            password="testpass123",
            name="Teacher User",
        )

        teacher_membership = SchoolMembership.objects.create(user=teacher_user, school=school, role=SchoolRole.TEACHER)

        teacher_profile = TeacherProfile.objects.create(
            user=teacher_user, bio="Teacher bio", hourly_rate=Decimal("20.00")
        )

        return {
            "school": school,
            "teacher_user": teacher_user,
            "teacher_membership": teacher_membership,
            "teacher_profile": teacher_profile,
        }

    @staticmethod
    def create_student_with_profile(email="student@test.com", school=None):
        """
        Create a student with proper profile and school membership.

        Args:
            email: Email for the student
            school: School instance (will create one if None)

        Returns:
            dict: Dictionary with student fixtures
        """
        if school is None:
            school_fixtures = FinanceTestFixtures.create_minimal_school_setup()
            school = school_fixtures["school"]
            educational_system = school_fixtures["educational_system"]
        else:
            educational_system = EducationalSystem.objects.filter(code=EducationalSystemType.PORTUGAL).first()
            if not educational_system:
                educational_system = EducationalSystem.objects.create(
                    name="Test System", code=EducationalSystemType.PORTUGAL, description="Test system"
                )

        student_user = User.objects.create_user(
            email=email,
            password="testpass123",
            name="Student User",
        )

        student_membership = SchoolMembership.objects.create(user=student_user, school=school, role=SchoolRole.STUDENT)

        student_profile = StudentProfile.objects.create(
            user=student_user, educational_system=educational_system, school_year="7", birth_date=date(2008, 5, 15)
        )

        student_account_balance = StudentAccountBalance.objects.create(
            student=student_user,
            hours_purchased=Decimal("0.00"),
            hours_consumed=Decimal("0.00"),
            balance_amount=Decimal("0.00"),
        )

        return {
            "school": school,
            "educational_system": educational_system,
            "student_user": student_user,
            "student_membership": student_membership,
            "student_profile": student_profile,
            "student_account_balance": student_account_balance,
        }

    @staticmethod
    def create_complete_pricing_plan():
        """
        Create a pricing plan with all required fields.

        Returns:
            PricingPlan: Complete pricing plan instance
        """
        return PricingPlan.objects.create(
            name="Complete Plan",
            description="Complete plan description",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("5.00"),
            price_eur=Decimal("50.00"),
            validity_days=30,
            display_order=1,
            is_active=True,
        )

    @staticmethod
    def create_parent_child_setup(parent_email="parent@test.com", child_email="child@test.com", school=None):
        """
        Create a complete parent-child relationship with all required associations.

        Args:
            parent_email: Email for the parent
            child_email: Email for the child
            school: School instance (will create one if None)

        Returns:
            dict: Dictionary with parent-child fixtures
        """
        if school is None:
            school_fixtures = FinanceTestFixtures.create_minimal_school_setup()
            school = school_fixtures["school"]
            educational_system = school_fixtures["educational_system"]
        else:
            educational_system = EducationalSystem.objects.filter(code=EducationalSystemType.PORTUGAL).first()
            if not educational_system:
                educational_system = EducationalSystem.objects.create(
                    name="Test System", code=EducationalSystemType.PORTUGAL, description="Test system"
                )

        parent_user = User.objects.create_user(
            email=parent_email,
            password="testpass123",
            name="Parent User",
        )

        child_user = User.objects.create_user(
            email=child_email,
            password="testpass123",
            name="Child User",
        )

        parent_membership = SchoolMembership.objects.create(user=parent_user, school=school, role=SchoolRole.GUARDIAN)

        child_membership = SchoolMembership.objects.create(user=child_user, school=school, role=SchoolRole.STUDENT)

        guardian_profile = GuardianProfile.objects.create(user=parent_user)

        student_profile = StudentProfile.objects.create(
            user=child_user, educational_system=educational_system, school_year="7", birth_date=date(2008, 5, 15)
        )

        guardian_student_relationship = GuardianStudentRelationship.objects.create(
            guardian=parent_user,
            student=child_user,
            school=school,
            relationship_type=RelationshipType.PARENT,
        )

        return {
            "school": school,
            "educational_system": educational_system,
            "parent_user": parent_user,
            "child_user": child_user,
            "parent_membership": parent_membership,
            "child_membership": child_membership,
            "guardian_profile": guardian_profile,
            "student_profile": student_profile,
            "parent_child_relationship": parent_child_relationship,
        }

    @staticmethod
    def create_pricing_plan_variants():
        """
        Create multiple pricing plan variants for comprehensive testing.

        Returns:
            dict: Dictionary with different pricing plan types
        """
        plans = {}

        # Package plan
        plans["package"] = PricingPlan.objects.create(
            name="Test Package Plan",
            description="Package plan for testing",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.00"),
            price_eur=Decimal("100.00"),
            validity_days=30,
            display_order=1,
            is_active=True,
        )

        # Subscription plan
        plans["subscription"] = PricingPlan.objects.create(
            name="Test Subscription Plan",
            description="Subscription plan for testing",
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal("20.00"),
            price_eur=Decimal("150.00"),
            validity_days=30,
            display_order=2,
            is_active=True,
        )

        # Inactive plan for testing edge cases
        plans["inactive"] = PricingPlan.objects.create(
            name="Inactive Test Plan",
            description="Inactive plan for testing",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("5.00"),
            price_eur=Decimal("50.00"),
            validity_days=30,
            display_order=3,
            is_active=False,
        )

        return plans
