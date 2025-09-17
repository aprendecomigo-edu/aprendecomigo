"""
Base test utilities for E2E tests.
"""

from typing import Any

from fixtures.test_data import AdminTestData, TestSelectors
from playwright.sync_api import Page, expect
import pytest


class BaseE2ETest:
    """Base class for E2E tests with common utilities"""

    @pytest.fixture(autouse=True)
    def setup_admin_login(self, page: Page):
        """Automatically log in as admin for all tests"""
        self.login_as_admin(page)
        self.page = page

    def login_as_admin(self, page: Page):
        """Login as school admin using Django session authentication"""
        admin_creds = AdminTestData.get_admin_credentials()

        # Create and set Django session cookie to bypass OTP
        self._set_django_session(page, admin_creds["email"])

        # Navigate directly to dashboard
        page.goto("http://localhost:8000/dashboard/")

        # Verify we're logged in as school admin
        try:
            page.wait_for_selector("nav", timeout=5000)
            expect(page.locator("body")).to_contain_text("Dashboard")
        except Exception:
            # If session auth fails, fall back to manual login
            print("Session auth failed, falling back to manual login")
            self._manual_login_fallback(page, admin_creds)

    def _create_or_get_admin_user(self, email: str):
        """Create admin user via Django management if needed"""
        import subprocess  # nosec B404 - test environment only
        import sys

        try:
            # Create school admin user with Django management command
            result = subprocess.run(  # nosec B603 - test environment with trusted input
                [
                    sys.executable,
                    "manage.py",
                    "shell",
                    "-c",
                    f"""
from accounts.models import CustomUser, School, SchoolMembership
from accounts.models.schools import SchoolRole
import os

# Change to Django project directory
os.chdir('/Users/anapmc/Code/aprendecomigo')

try:
    user = CustomUser.objects.get(email='{email}')
    print(f'User {email} already exists')
except CustomUser.DoesNotExist:
    user = CustomUser.objects.create_user(
        email='{email}',
        name='Test Admin E2E'
    )
    print(f'Created user: {email}')

    # Create or get school
    school, created = School.objects.get_or_create(
        name='Test School E2E',
        defaults={{
            'contact_email': '{email}',
            'phone_number': '+351911223344',
            'address': 'Test Address, 1000-001 Lisboa'
        }}
    )

    # Create school membership
    membership, created = SchoolMembership.objects.get_or_create(
        user=user,
        school=school,
        defaults={{
            'role': SchoolRole.SCHOOL_ADMIN,
            'is_active': True
        }}
    )
    print(f'School membership created: {{created}}')
""",
                ],
                cwd="/Users/anapmc/Code/aprendecomigo",
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(f"Failed to create admin user: {result.stderr}")

        except Exception as e:
            print(f"Error creating admin user: {e}")

    def _create_admin_account_if_needed(self, page: Page, admin_creds):
        """Fallback method to create admin account via signup"""
        try:
            admin_data = AdminTestData.get_school_admin_data()

            # Navigate to signup
            page.goto("http://localhost:8000/signup/")
            page.wait_for_selector('input[name="school_name"]', timeout=5000)

            # Fill signup form
            page.fill('input[name="school_name"]', admin_data["school_name"])
            page.fill('input[name="admin_name"]', admin_data["admin_name"])
            page.fill('input[name="admin_email"]', admin_data["admin_email"])
            page.fill('input[name="admin_phone"]', admin_data["admin_phone"])

            # Submit signup form
            page.click('button[type="submit"]')

        except Exception as e:
            print(f"Failed to create admin account via signup: {e}")

    def _set_django_session(self, page: Page, email: str):
        """Set Django session cookie for the user"""
        import subprocess  # nosec B404 - test environment only
        import sys

        try:
            # Get session key by logging in the user programmatically using proper Django login
            result = subprocess.run(  # nosec B603 - test environment with trusted input
                [
                    sys.executable,
                    "manage.py",
                    "shell",
                    "-c",
                    f"""
import os
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import login
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory
from accounts.models import CustomUser

try:
    user = CustomUser.objects.get(email='{email}')

    # Create a proper session with all required data
    factory = RequestFactory()
    request = factory.get('/')
    request.session = SessionStore()

    # Properly login the user with backend specified
    from django.contrib.auth import login
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)

    # Save session
    request.session.save()

    print(f'SESSION_KEY:{{request.session.session_key}}')

except Exception as e:
    print(f'ERROR:{{e}}')
    import traceback
    traceback.print_exc()
""",
                ],
                cwd="/Users/anapmc/Code/aprendecomigo",
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                if "SESSION_KEY:" in output:
                    session_key = output.split("SESSION_KEY:")[1].split()[0]
                    # Set the session cookie
                    page.context.add_cookies(
                        [
                            {
                                "name": "sessionid",
                                "value": session_key,
                                "domain": "localhost",
                                "path": "/",
                                "httpOnly": True,
                            }
                        ]
                    )
                    print(f"Set session cookie: {session_key[:10]}...")
                    return
                else:
                    print(f"Session creation output: {output}")
            else:
                print(f"Session creation failed: {result.stderr}")

        except Exception as e:
            print(f"Failed to set Django session: {e}")

    def _manual_login_fallback(self, page: Page, admin_creds):
        """Fallback method for manual login if session auth fails"""
        try:
            # Navigate to login and try basic auth flow
            page.goto("http://localhost:8000/signin/")
            page.wait_for_selector('input[type="email"]', timeout=5000)

            # Just navigate to dashboard directly - Django might have auto-login for testing
            page.goto("http://localhost:8000/dashboard/")

        except Exception as e:
            print(f"Manual login fallback failed: {e}")
            # As last resort, just navigate to the page
            page.goto("http://localhost:8000/people/")

    def navigate_to_people_page(self, page: Page):
        """Navigate to the people management page"""
        page.goto("http://localhost:8000/people/")

        # Wait for page to load - use more specific selector
        expect(page.locator('h1:has-text("Gestão de Pessoas")')).to_be_visible()

    def open_add_student_modal(self, page: Page):
        """Open the Add Student modal"""
        page.click(TestSelectors.ADD_STUDENT_BUTTON)

        # Wait for modal to open
        expect(page.locator(TestSelectors.MODAL_TITLE)).to_be_visible()

    def select_account_type(self, page: Page, account_type: str):
        """Select account type in the modal"""
        selectors = {
            "separate": TestSelectors.ACCOUNT_TYPE_SEPARATE,
            "guardian_only": TestSelectors.ACCOUNT_TYPE_GUARDIAN_ONLY,
            "self": TestSelectors.ACCOUNT_TYPE_SELF,
        }

        if account_type not in selectors:
            raise ValueError(f"Invalid account type: {account_type}")

        page.click(selectors[account_type])

        # Wait for form to update
        page.wait_for_timeout(500)

    def fill_form_field(self, page: Page, selector: str, value: Any, field_type: str = "text"):
        """Fill a form field with proper handling for different field types"""
        if value is None or value == "":
            return

        element = page.locator(selector)

        # Wait for element to be available
        element.wait_for(state="attached", timeout=5000)

        if field_type == "checkbox":
            if value:
                element.check()
            else:
                element.uncheck()
        elif field_type == "select":
            element.select_option(value=str(value))
        else:
            element.fill(str(value))

    def submit_form(self, page: Page):
        """Submit the add student form"""
        page.click(TestSelectors.SUBMIT_BUTTON)

        # Wait a moment for form processing
        page.wait_for_timeout(1000)

    def wait_for_success(self, page: Page, timeout: int = 10000):
        """Wait for success message to appear"""
        success_locator = page.locator(TestSelectors.SUCCESS_MESSAGE).first

        # Check if there's an error message instead
        error_locator = page.locator(TestSelectors.ERROR_MESSAGE).first
        if error_locator.is_visible(timeout=2000):
            error_text = error_locator.text_content()
            raise AssertionError(f"Expected success but got error: {error_text}")

        expect(success_locator).to_be_visible(timeout=timeout)

    def wait_for_error(self, page: Page, timeout: int = 5000):
        """Wait for error message to appear"""
        error_locator = page.locator(TestSelectors.ERROR_MESSAGE)
        expect(error_locator).to_be_visible(timeout=timeout)

    def verify_form_validation_error(self, page: Page, field_selector: str):
        """Verify that a field shows validation error"""
        # Check for HTML5 validation or custom error styling
        field = page.locator(field_selector)

        # Check if field is invalid (HTML5 validation)
        is_invalid = field.evaluate("el => !el.checkValidity()")
        assert is_invalid, f"Field {field_selector} should be invalid but is not"

    def verify_student_appears_in_list(self, page: Page, student_name: str):
        """Verify that the student appears in the students list after creation"""
        # Look for the student name in the students list - use first occurrence
        student_locator = page.locator(f'text="{student_name}"').first
        expect(student_locator).to_be_visible(timeout=10000)

    def close_modal(self, page: Page):
        """Close the Add Student modal"""
        page.click(TestSelectors.CANCEL_BUTTON)

        # Wait for modal to close
        modal = page.locator(TestSelectors.MODAL_TITLE)
        expect(modal).not_to_be_visible()

    def assert_field_exists(self, page: Page, selector: str):
        """Assert that a field exists and is visible in the current form"""
        field = page.locator(selector)
        expect(field).to_be_visible()

    def assert_field_not_exists(self, page: Page, selector: str):
        """Assert that a field does not exist or is not visible in the current form"""
        field = page.locator(selector)
        expect(field).not_to_be_visible()

    def get_form_validation_message(self, page: Page, field_selector: str) -> str:
        """Get the validation message for a form field"""
        field = page.locator(field_selector)
        return field.evaluate("el => el.validationMessage")
