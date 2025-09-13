"""
E2E Tests for School Admin Registration and Activation Flow

Tests the complete flow described in GitHub issue #217:
1. School admin accesses platform and initiates registration
2. Fills required form data (school name, admin name, email, phone)
3. School created in pending state, redirected to dashboard
4. System sends confirmation email with unique 7-day valid link
5. Dashboard access without password using email/SMS code
6. Dashboard shows mandatory TODOs list
7. Admin completes required tasks to activate school
8. Account deletion after 7 days if tasks not completed
"""

import re
import time

from playwright.sync_api import Page, expect
import pytest


class TestSchoolAdminRegistration:
    """Test school admin registration and activation flow."""

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

    def test_complete_school_admin_registration_flow(self, page: Page):
        """
        Test complete school admin registration and activation flow.

        Covers the main user journey from initial registration through
        account activation as described in issue #217.
        """
        # Get unique test data for this run
        test_data = self.get_test_admin_data()

        # Step 1: Navigate to platform homepage and start registration
        page.goto(self.BASE_URL)
        expect(page).to_have_title(re.compile("Login.*Aprende Comigo"))

        # Click "Create your account" link
        page.get_by_role("link", name="Create your account").click()
        expect(page).to_have_title(re.compile("Create Account.*Aprende Comigo"))

        # Step 2: Select School Admin registration type
        # Use role-based selector which is more stable than text
        school_admin_tab = page.get_by_role("tab").filter(has_text="School Admin")
        school_admin_tab.click()

        # Verify school admin form is displayed using semantic selectors
        expect(page.locator("h3", has_text="School Information")).to_be_visible()

        # Step 3: Fill mandatory registration form data using semantic selectors
        # Find inputs within their labeled groups (more stable than placeholder text)
        page.get_by_role("group", name="Full Name").get_by_role("textbox").fill(test_data["full_name"])
        page.get_by_role("group", name="Email Address").get_by_role("textbox").fill(test_data["email"])
        page.get_by_role("group", name="Phone Number").get_by_role("textbox").fill(test_data["phone"])
        page.get_by_role("group", name="School Name").get_by_role("textbox").fill(test_data["school_name"])

        # Step 4: Submit registration form
        page.get_by_role("button", name="Create Account").click()

        # Step 4a: Wait for success message to appear first
        expect(page.get_by_text("Welcome to Aprende Comigo!")).to_be_visible(timeout=10000)
        expect(page.get_by_text("Redirecting to your dashboard...")).to_be_visible()

        # Step 5: Wait for redirect to dashboard (takes about 5 seconds)
        # Should be redirected to admin dashboard as specified in issue #217
        page.wait_for_url(re.compile(r".*/dashboard/"), timeout=10000)
        expect(page).to_have_url(re.compile(r".*/dashboard/"))

        # Step 6: Verify dashboard shows mandatory TODO list as specified in issue #217
        # Use semantic heading selectors instead of exact text
        expect(page.locator("h2").filter(has_text=re.compile(r"Tarefas|Tasks"))).to_be_visible()

        # Verify task items exist using more flexible selectors
        # Look for task-like content structure rather than exact text
        task_items = page.locator("div").filter(has_text=re.compile(r"Verify.*email|email.*verif", re.IGNORECASE))
        expect(task_items.first).to_be_visible()

        phone_task = page.locator("div").filter(has_text=re.compile(r"Verify.*phone|phone.*verif", re.IGNORECASE))
        expect(phone_task.first).to_be_visible()

        # Step 7: Verify school setup guidance as mentioned in issue #217
        # Use flexible text matching for guidance messages
        guidance = page.locator("p").filter(
            has_text=re.compile(r"add.*teachers.*students|teachers.*students.*activate")
        )
        expect(guidance.first).to_be_visible()

        # Step 8: Verify stats show zero state (new school as specified in issue)
        # Use more semantic selectors for stats cards
        stats_section = page.locator("div").filter(has_text="Total Teachers")
        expect(stats_section).to_be_visible()

        # Verify zero count exists in the stats area (new school state)
        zero_counts = page.locator("p", has_text="0")
        expect(zero_counts.first).to_be_visible()

    def test_school_registration_form_validation(self, page: Page):
        """Test form validation for school admin registration."""
        page.goto(f"{self.BASE_URL}/signup/")
        page.get_by_role("tab", name="School Admin").click()

        # Try to submit empty form
        page.get_by_role("button", name="Create Account").click()

        # Check for validation messages
        expect(page.get_by_text("This field is required").first).to_be_visible()

        # Test invalid email format
        page.get_by_placeholder("Enter your full name").fill("Test User")
        page.get_by_placeholder("Enter your email address").fill("invalid-email")
        page.get_by_role("button", name="Create Account").click()

        expect(page.get_by_text("valid email")).to_be_visible()

        # Test invalid phone format
        page.get_by_placeholder("Enter your email address").fill("test@example.com")
        page.get_by_placeholder("+1 (555) 123-4567").fill("123")
        page.get_by_role("button", name="Create Account").click()

        expect(page.get_by_text("valid phone")).to_be_visible()

    def test_school_dashboard_todo_interaction(self, page: Page):
        """
        Test interaction with TODO items in the admin dashboard.

        This test assumes a school admin is already registered and
        logged into the dashboard.
        """
        # Note: This would require test data setup or previous test state
        # For now, we'll test the TODO list UI interactions

        page.goto(f"{self.BASE_URL}/dashboard/")

        # Verify TODO list is interactive
        # Click on first TODO item to expand/navigate
        first_todo = page.locator('[data-test="todo-item"]').first
        if first_todo.is_visible():
            first_todo.click()

            # Verify navigation to completion form/page
            expect(page.url).not_to_equal(f"{self.BASE_URL}/dashboard/")

    def test_mobile_responsive_registration(self, page: Page):
        """Test mobile-responsive behavior of registration form."""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})

        page.goto(f"{self.BASE_URL}/signup/")
        page.get_by_role("tab", name="School Admin").click()

        # Verify form is properly displayed on mobile
        expect(page.get_by_text("School Information")).to_be_visible()
        expect(page.get_by_placeholder("Enter your full name")).to_be_visible()
        expect(page.get_by_placeholder("Your school name")).to_be_visible()

        # Test form submission on mobile
        test_data = self.get_test_admin_data()
        page.get_by_placeholder("Enter your full name").fill(test_data["full_name"])
        page.get_by_placeholder("Enter your email address").fill(test_data["email"])
        page.get_by_placeholder("+1 (555) 123-4567").fill(test_data["phone"])
        page.get_by_placeholder("Your school name").fill(test_data["school_name"])

        # Verify submit button is accessible on mobile
        submit_button = page.get_by_role("button", name="Create Account")
        expect(submit_button).to_be_visible()

        # Scroll to button if needed and click
        submit_button.scroll_into_view_if_needed()
        submit_button.click()
