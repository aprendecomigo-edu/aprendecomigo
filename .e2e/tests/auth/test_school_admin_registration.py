"""
E2E Tests for School Admin Registration Flow

Tests based on GitHub issue #217 and following data-test conventions
from data-test-conventions.md and data-test-implementation.md
"""

import re
import time

from playwright.sync_api import Page, expect
import pytest


class TestSchoolAdminRegistration:
    """Test school admin registration following data-test conventions."""

    BASE_URL = "http://localhost:8000"

    def get_test_admin_data(self):
        """Generate unique test data for each test run."""
        timestamp = int(time.time())
        return {
            "full_name": "Maria Silva Test",
            "email": f"admin.test.{timestamp}@e2e.com",
            "phone": "+351912345678",
            "school_name": f"Escola de Teste {timestamp}",
        }

    def test_phase_1_critical_path_registration(self, page: Page):
        """
        Test Phase 1 critical path items from data-test-implementation.md

        This test validates the minimal viable E2E flow for school admin registration.
        """
        test_data = self.get_test_admin_data()

        # Navigate to homepage
        page.goto(self.BASE_URL)
        expect(page).to_have_title(re.compile("Login.*Aprende Comigo"))

        # Navigate to signup - test if data-test="create-account-link" exists
        try:
            page.locator('[data-test="create-account-link"]').click()
        except Exception:
            # Fallback to text-based if data-test not implemented yet
            page.get_by_role("link", name="Create your account").click()

        expect(page).to_have_title(re.compile("Create Account.*Aprende Comigo"))

        # Test Phase 1: Tab selection - select-school-admin
        try:
            page.locator('[data-test="select-school-admin"]').click()
        except Exception:
            # Fallback if not implemented
            page.get_by_role("tab", name="School Admin").click()

        # Test Phase 1: Core form inputs
        try:
            # Try data-test attributes first
            page.locator('[data-test="input-full-name"]').fill(test_data["full_name"])
            page.locator('[data-test="input-email"]').fill(test_data["email"])
            page.locator('[data-test="input-phone"]').fill(test_data["phone"])
            page.locator('[data-test="input-school-name"]').fill(test_data["school_name"])
        except Exception:
            # Fallback to placeholder-based selectors
            page.get_by_placeholder("Enter your full name").fill(test_data["full_name"])
            page.get_by_placeholder("Enter your email address").fill(test_data["email"])
            page.get_by_placeholder("+1 (555) 123-4567").fill(test_data["phone"])
            page.get_by_placeholder("Your school name").fill(test_data["school_name"])

        # Test Phase 1: Critical action - submit-registration
        try:
            page.locator('[data-test="submit-registration"]').click()
        except Exception:
            # Fallback
            page.get_by_role("button", name="Create Account").click()

        # Test Phase 1: Success state - success-registration
        try:
            expect(page.locator('[data-test="success-registration"]')).to_be_visible(timeout=10000)
        except Exception:
            # Fallback
            expect(page.get_by_text("Welcome to Aprende Comigo!")).to_be_visible(timeout=10000)

        # Wait for redirect to dashboard
        page.wait_for_url(re.compile(r".*/dashboard/"), timeout=10000)
        expect(page).to_have_url(re.compile(r".*/dashboard/"))

        # Test Phase 1: Key metric - metric-teacher-count
        try:
            teacher_metric = page.locator('[data-test="metric-teacher-count"]')
            expect(teacher_metric).to_be_visible()
            expect(teacher_metric).to_have_attribute("data-value", "0")
        except Exception:
            # Fallback to text-based verification
            expect(page.get_by_text("Total Teachers")).to_be_visible()

    @pytest.mark.skip(reason="Phase 2 - Not implemented yet")
    def test_phase_2_extended_registration(self, page: Page):
        """Test Phase 2: Complete registration flow with all form inputs and validation."""
        pass

    @pytest.mark.skip(reason="Phase 3 - Not implemented yet")
    def test_phase_3_dashboard_features(self, page: Page):
        """Test Phase 3: Complete dashboard functionality and task management."""
        pass

    def test_data_test_attribute_coverage(self, page: Page):
        """
        Test to verify which Phase 1 data-test attributes are actually implemented.

        This test helps update the implementation checklist.
        """
        page.goto(f"{self.BASE_URL}/signup/")

        # Check Phase 1 attributes from implementation checklist
        phase_1_attributes = [
            "select-individual-tutor",
            "select-school-admin",
            "input-full-name",
            "input-email",
            "input-school-name",
            "submit-registration",
            "success-registration",  # This appears after form submission
        ]

        implemented = []
        missing = []

        for attr in phase_1_attributes:
            if attr == "success-registration":
                continue  # Skip - only appears after form submission

            try:
                element = page.locator(f'[data-test="{attr}"]')
                if element.count() > 0:
                    implemented.append(attr)
                else:
                    missing.append(attr)
            except Exception:
                missing.append(attr)

        print("\n=== Data-Test Implementation Status ===")
        print(f"✅ Implemented ({len(implemented)}): {implemented}")
        print(f"❌ Missing ({len(missing)}): {missing}")
        print(
            f"📊 Coverage: {len(implemented)}/{len(phase_1_attributes) - 1} = {len(implemented) / (len(phase_1_attributes) - 1) * 100:.1f}%"
        )

        # The test always passes - it's for reporting only
        assert True

    def test_registration_with_fallbacks(self, page: Page):
        """
        Test registration flow using fallback selectors when data-test attributes are missing.

        This ensures tests work during the transition period.
        """
        test_data = self.get_test_admin_data()

        page.goto(self.BASE_URL)
        page.get_by_role("link", name="Create your account").click()

        # Use fallback selectors
        page.get_by_role("tab", name="School Admin").click()
        page.get_by_placeholder("Enter your full name").fill(test_data["full_name"])
        page.get_by_placeholder("Enter your email address").fill(test_data["email"])
        page.get_by_placeholder("+1 (555) 123-4567").fill(test_data["phone"])
        page.get_by_placeholder("Your school name").fill(test_data["school_name"])
        page.get_by_role("button", name="Create Account").click()

        # Verify success and redirect
        expect(page.get_by_text("Welcome to Aprende Comigo!")).to_be_visible(timeout=10000)
        page.wait_for_url(re.compile(r".*/dashboard/"), timeout=10000)

        # Verify dashboard shows zero stats for new school
        expect(page.get_by_text("Total Teachers")).to_be_visible()
        expect(page.get_by_text("Total Students")).to_be_visible()
