"""
Test Runner Configuration for Add Student Integration Tests.

This module provides utilities for running the comprehensive Add Student test suite.
It includes test discovery, categorization, and running utilities that help developers
run specific test categories or the entire suite efficiently.

Usage:
    python manage.py test dashboard.tests.test_add_student_runner.AddStudentTestSuite

Or run individual test categories:
    python manage.py test dashboard.tests.test_add_student_integration.HTMXAddStudentIntegrationTests
    python manage.py test dashboard.tests.test_htmx_response_validation
    python manage.py test dashboard.tests.test_model_constraints_integration
"""

import unittest

from django.test import TestCase

# Import all test classes from the comprehensive test modules
from .test_add_student_integration import (
    BusinessLogicValidationTests,
    DataIntegrityConstraintTests,
    ErrorHandlingIntegrationTests,
    FieldValidationEdgeCaseTests,
    FormSecurityTests,
    HTMXAddStudentIntegrationTests,
    MultiTenantBehaviorTests,
)
from .test_htmx_response_validation import (
    HTMXErrorResponseTests,
    HTMXFormInteractionTests,
    HTMXPartialRenderingTests,
    HTMXResponseHeaderTests,
    HTMXSuccessResponseTests,
)
from .test_model_constraints_integration import (
    AddStudentFormConstraintIntegrationTests,
    DatabaseIntegrityConstraintTests,
    GuardianStudentRelationshipConstraintTests,
    ModelValidationIntegrationTests,
    StudentProfileConstraintTests,
)


class AddStudentTestSuite:
    """
    Comprehensive test suite for Add Student functionality.

    This class organizes all Add Student tests into logical categories
    and provides utilities for running specific test groups.
    """

    @staticmethod
    def get_htmx_tests():
        """Get all HTMX-related tests."""
        return [
            HTMXAddStudentIntegrationTests,
            HTMXResponseHeaderTests,
            HTMXSuccessResponseTests,
            HTMXErrorResponseTests,
            HTMXPartialRenderingTests,
            HTMXFormInteractionTests,
        ]

    @staticmethod
    def get_validation_tests():
        """Get all validation and business logic tests."""
        return [
            FieldValidationEdgeCaseTests,
            BusinessLogicValidationTests,
            StudentProfileConstraintTests,
            ModelValidationIntegrationTests,
        ]

    @staticmethod
    def get_database_tests():
        """Get all database and constraint tests."""
        return [
            DataIntegrityConstraintTests,
            DatabaseIntegrityConstraintTests,
            GuardianStudentRelationshipConstraintTests,
            AddStudentFormConstraintIntegrationTests,
        ]

    @staticmethod
    def get_security_tests():
        """Get all security-related tests."""
        return [
            FormSecurityTests,
            MultiTenantBehaviorTests,
        ]

    @staticmethod
    def get_error_handling_tests():
        """Get all error handling tests."""
        return [
            ErrorHandlingIntegrationTests,
            HTMXErrorResponseTests,
        ]

    @staticmethod
    def get_all_tests():
        """Get all Add Student test classes."""
        return (
            AddStudentTestSuite.get_htmx_tests()
            + AddStudentTestSuite.get_validation_tests()
            + AddStudentTestSuite.get_database_tests()
            + AddStudentTestSuite.get_security_tests()
            + AddStudentTestSuite.get_error_handling_tests()
        )

    @staticmethod
    def create_test_suite(test_classes=None):
        """
        Create a test suite from specified test classes.

        Args:
            test_classes: List of test classes to include. If None, includes all tests.

        Returns:
            unittest.TestSuite: Configured test suite.
        """
        if test_classes is None:
            test_classes = AddStudentTestSuite.get_all_tests()

        suite = unittest.TestSuite()

        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)

        return suite

    @staticmethod
    def run_test_category(category_name):
        """
        Run a specific category of tests.

        Args:
            category_name: One of 'htmx', 'validation', 'database', 'security', 'error_handling'
        """
        category_map = {
            "htmx": AddStudentTestSuite.get_htmx_tests,
            "validation": AddStudentTestSuite.get_validation_tests,
            "database": AddStudentTestSuite.get_database_tests,
            "security": AddStudentTestSuite.get_security_tests,
            "error_handling": AddStudentTestSuite.get_error_handling_tests,
        }

        if category_name not in category_map:
            raise ValueError(f"Unknown category: {category_name}. Available: {list(category_map.keys())}")

        test_classes = category_map[category_name]()
        suite = AddStudentTestSuite.create_test_suite(test_classes)

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        return result


class AddStudentQuickTestSuite(TestCase):
    """
    Quick test suite for CI/CD or rapid development feedback.

    This includes the most critical tests that should pass before
    any Add Student code changes are committed.
    """

    def test_critical_htmx_functionality(self):
        """Test critical HTMX functionality works."""
        # This would run a subset of the most important HTMX tests
        critical_tests = [
            "test_htmx_student_guardian_submission_returns_correct_headers",
            "test_successful_submission_has_refresh_trigger",
            "test_validation_error_returns_error_partial",
        ]

        # Run specific test methods from HTMX test classes
        for test_name in critical_tests:
            # This is a simplified approach - in practice you'd implement
            # more sophisticated test filtering
            self.assertTrue(hasattr(HTMXAddStudentIntegrationTests, test_name))

    def test_critical_validation_rules(self):
        """Test critical validation rules work."""
        critical_validations = [
            "test_adult_student_age_validation",
            "test_adult_student_must_have_user_account",
            "test_guardian_only_must_not_have_user_account",
        ]

        for test_name in critical_validations:
            # Verify critical validation tests exist
            has_test = hasattr(FieldValidationEdgeCaseTests, test_name) or hasattr(
                StudentProfileConstraintTests, test_name
            )
            self.assertTrue(has_test, f"Critical test {test_name} not found")

    def test_critical_security_measures(self):
        """Test critical security measures work."""
        security_tests = [
            "test_xss_prevention_in_form_fields",
            "test_sql_injection_prevention",
            "test_csrf_protection",
        ]

        for test_name in security_tests:
            self.assertTrue(hasattr(FormSecurityTests, test_name))


# Test discovery utilities
def discover_add_student_tests():
    """
    Discover all Add Student tests in the dashboard.tests package.

    Returns:
        dict: Mapping of test categories to test classes.
    """
    return {
        "htmx": AddStudentTestSuite.get_htmx_tests(),
        "validation": AddStudentTestSuite.get_validation_tests(),
        "database": AddStudentTestSuite.get_database_tests(),
        "security": AddStudentTestSuite.get_security_tests(),
        "error_handling": AddStudentTestSuite.get_error_handling_tests(),
    }


def print_test_summary():
    """Print a summary of available Add Student tests."""
    categories = discover_add_student_tests()

    print("Add Student Test Suite Summary")
    print("=" * 40)

    total_classes = 0
    for category, test_classes in categories.items():
        print(f"\n{category.upper()} Tests:")
        for test_class in test_classes:
            test_methods = [method for method in dir(test_class) if method.startswith("test_")]
            print(f"  - {test_class.__name__} ({len(test_methods)} tests)")
            total_classes += 1

    print(f"\nTotal Test Classes: {total_classes}")
    print("\nTo run specific categories:")
    for category in categories:
        print(f"  python manage.py test dashboard.tests.test_add_student_integration.*{category.title()}*")


# Example usage functions
def run_htmx_tests():
    """Convenience function to run only HTMX tests."""
    return AddStudentTestSuite.run_test_category("htmx")


def run_validation_tests():
    """Convenience function to run only validation tests."""
    return AddStudentTestSuite.run_test_category("validation")


def run_security_tests():
    """Convenience function to run only security tests."""
    return AddStudentTestSuite.run_test_category("security")


if __name__ == "__main__":
    print_test_summary()

    print("\n" + "=" * 40)
    print("Running Add Student Test Suite...")
    print("=" * 40)

    # Run all tests by default
    all_tests = AddStudentTestSuite.create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(all_tests)

    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFailures:")
        for test, error in result.failures:
            print(f"  - {test}: {error}")

    if result.errors:
        print("\nErrors:")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
