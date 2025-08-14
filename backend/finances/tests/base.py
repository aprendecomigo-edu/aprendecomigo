"""
Base test classes for the finances app with comprehensive fixture support.

This module provides base test classes that use the FinanceTestFixtures
to ensure all test classes have access to properly configured test data
with complete relationships and database constraints satisfied.

Created to resolve issue #181 - Test Setup and Fixture Issues.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from finances.fixtures import FinanceTestFixtures

User = get_user_model()


class FinanceBaseTestCase(TestCase):
    """
    Base test case for finance app tests with complete fixture setup.

    Provides a complete test environment with all necessary models and
    relationships created. Use this as the base class for most finance tests.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up test data with complete fixture environment."""
        cls.fixtures = FinanceTestFixtures.create_complete_test_environment()

        # Extract commonly used fixtures for easy access
        cls.educational_system = cls.fixtures["educational_system"]
        cls.school = cls.fixtures["school"]
        cls.billing_settings = cls.fixtures["billing_settings"]

        cls.teacher_user = cls.fixtures["teacher_user"]
        cls.student_user = cls.fixtures["student_user"]
        cls.parent_user = cls.fixtures["parent_user"]
        cls.admin_user = cls.fixtures["admin_user"]

        cls.teacher_membership = cls.fixtures["teacher_membership"]
        cls.student_membership = cls.fixtures["student_membership"]
        cls.parent_membership = cls.fixtures["parent_membership"]
        cls.admin_membership = cls.fixtures["admin_membership"]

        cls.teacher_profile = cls.fixtures["teacher_profile"]
        cls.student_profile = cls.fixtures["student_profile"]
        cls.parent_profile = cls.fixtures["parent_profile"]

        cls.parent_child_relationship = cls.fixtures["parent_child_relationship"]
        cls.course = cls.fixtures["course"]
        cls.teacher_course = cls.fixtures["teacher_course"]

        cls.pricing_plan = cls.fixtures["pricing_plan"]
        cls.student_account_balance = cls.fixtures["student_account_balance"]
        cls.purchase_transaction = cls.fixtures["purchase_transaction"]
        cls.teacher_compensation_rule = cls.fixtures["teacher_compensation_rule"]
        cls.class_session = cls.fixtures["class_session"]
        cls.family_budget_control = cls.fixtures["family_budget_control"]
        cls.approval_request = cls.fixtures["approval_request"]
        cls.stored_payment_method = cls.fixtures["stored_payment_method"]
        cls.receipt = cls.fixtures["receipt"]
        cls.hour_consumption = cls.fixtures["hour_consumption"]

    def validate_test_fixtures(self):
        """
        Validate that all fixtures meet database constraints.
        Call this method in setUp if you need to verify fixture integrity.
        """
        # Verify user relationships
        self.assertIsNotNone(self.student_profile.school, "StudentProfile must have school association")
        self.assertIsNotNone(self.student_profile.educational_system, "StudentProfile must have educational system")
        self.assertTrue(self.parent_child_relationship.is_verified, "Parent-child relationship must be verified")

        # Verify pricing plan completeness
        self.assertIsNotNone(self.pricing_plan.name, "PricingPlan must have name")
        self.assertIsNotNone(self.pricing_plan.description, "PricingPlan must have description")
        self.assertIsNotNone(self.pricing_plan.hours_included, "PricingPlan must have hours_included")
        self.assertIsNotNone(self.pricing_plan.price_eur, "PricingPlan must have price_eur")
        self.assertIsNotNone(self.pricing_plan.validity_days, "PricingPlan must have validity_days")

        # Verify student account balance has student association
        self.assertIsNotNone(self.student_account_balance.student, "StudentAccountBalance must have student")

        # Verify teacher compensation rule has required fields
        self.assertIsNotNone(self.teacher_compensation_rule.teacher, "TeacherCompensationRule must have teacher")
        self.assertIsNotNone(self.teacher_compensation_rule.school, "TeacherCompensationRule must have school")
        self.assertIsNotNone(
            self.teacher_compensation_rule.rate_per_hour, "TeacherCompensationRule must have rate_per_hour"
        )

        # Additional business logic validations
        self.assertGreater(self.pricing_plan.price_eur, 0, "Pricing plan price must be positive")
        self.assertGreater(self.pricing_plan.hours_included, 0, "Pricing plan hours must be positive")
        self.assertGreater(self.teacher_compensation_rule.rate_per_hour, 0, "Teacher rate must be positive")


class FinanceMinimalTestCase(TestCase):
    """
    Minimal test case for finance app tests that need basic setup only.

    Use this for tests that don't need the full fixture environment
    and prefer to create their own specific test data.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up minimal test data."""
        school_fixtures = FinanceTestFixtures.create_minimal_school_setup()
        cls.educational_system = school_fixtures["educational_system"]
        cls.school = school_fixtures["school"]

    def create_complete_pricing_plan(self):
        """Helper method to create a complete pricing plan."""
        return FinanceTestFixtures.create_complete_pricing_plan()

    def create_teacher_with_profile(self, email="teacher@test.com"):
        """Helper method to create a teacher with proper setup."""
        return FinanceTestFixtures.create_teacher_with_profile(email, self.school)

    def create_student_with_profile(self, email="student@test.com"):
        """Helper method to create a student with proper setup."""
        return FinanceTestFixtures.create_student_with_profile(email, self.school)

    def create_parent_child_setup(self, parent_email="parent@test.com", child_email="child@test.com"):
        """Helper method to create parent-child relationship."""
        return FinanceTestFixtures.create_parent_child_setup(parent_email, child_email, self.school)


class FixtureValidationMixin:
    """
    Mixin that provides fixture validation helpers.

    Can be used with any test class to add validation methods
    for common fixture requirements.
    """

    def assert_student_has_school_association(self, student_user):
        """Assert that a student user has proper school association."""
        self.assertTrue(
            hasattr(student_user, "student_profile"), f"Student {student_user.email} must have a student profile"
        )
        self.assertIsNotNone(
            student_user.student_profile.school,
            f"Student profile for {student_user.email} must have a school association",
        )

    def assert_teacher_has_profile(self, teacher_user):
        """Assert that a teacher user has a proper teacher profile."""
        self.assertTrue(
            hasattr(teacher_user, "teacher_profile"), f"Teacher {teacher_user.email} must have a teacher profile"
        )
        self.assertIsNotNone(
            teacher_user.teacher_profile.hourly_rate,
            f"Teacher profile for {teacher_user.email} must have an hourly rate",
        )

    def assert_parent_child_relationship_exists(self, parent_user, child_user, school):
        """Assert that a proper parent-child relationship exists."""
        from accounts.models import ParentChildRelationship

        relationship = ParentChildRelationship.objects.filter(
            parent=parent_user, child=child_user, school=school
        ).first()

        self.assertIsNotNone(
            relationship,
            f"Parent-child relationship must exist between {parent_user.email} and {child_user.email} in school {school.name}",
        )
        self.assertTrue(
            relationship.is_verified,
            f"Parent-child relationship between {parent_user.email} and {child_user.email} must be verified",
        )

    def assert_pricing_plan_complete(self, pricing_plan):
        """Assert that a pricing plan has all required fields."""
        required_fields = ["name", "description", "hours_included", "price_eur"]

        for field in required_fields:
            value = getattr(pricing_plan, field)
            self.assertIsNotNone(value, f"PricingPlan must have {field} field populated, got {value}")

        if pricing_plan.plan_type == "package":
            self.assertIsNotNone(pricing_plan.validity_days, "Package pricing plans must have validity_days specified")

    def assert_student_account_balance_valid(self, student_account_balance):
        """Assert that a student account balance is properly configured."""
        self.assertIsNotNone(student_account_balance.student, "StudentAccountBalance must have a student association")
        self.assert_student_has_school_association(student_account_balance.student)
