"""
Pytest configuration and fixtures for E2E tests.
"""

from playwright.sync_api import Page
import pytest


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for all tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "user_agent": "Aprende Comigo E2E Tests",
        "ignore_https_errors": True,
    }


@pytest.fixture
def authenticated_admin_page(page: Page):
    """
    Fixture that provides a page with an authenticated school admin.

    This fixture handles the login process so tests can focus on
    testing specific functionality rather than authentication setup.
    """
    # This would implement the authentication flow
    # For now, return the page as-is
    return page


@pytest.fixture
def test_school_data():
    """Fixture providing test data for school registration."""
    return {
        "school_name": "Test School E2E",
        "admin_name": "Admin Test User",
        "admin_email": "admin.test@e2e.example.com",
        "admin_phone": "+351987654321",
    }


@pytest.fixture(autouse=True)
def setup_test_environment(page: Page):
    """
    Auto-use fixture to set up test environment before each test.

    This ensures each test starts with a clean slate and cleans up test data.
    """
    # Clear browser state
    page.context.clear_cookies()
    page.context.clear_permissions()

    yield

    # Cleanup: Logout and clear any test sessions
    try:
        # Try to logout if user is logged in
        page.goto("http://localhost:8000/logout/", timeout=5000)
    except Exception:
        # If logout fails, just clear cookies
        page.context.clear_cookies()


@pytest.fixture
def cleanup_test_user():
    """
    Fixture to track and cleanup test users.

    Returns a function that can be called to register a user for cleanup.
    """
    test_emails = []

    def register_for_cleanup(email: str):
        """Register an email for cleanup after test."""
        test_emails.append(email)

    yield register_for_cleanup

    # Note: In a production test environment, you would implement
    # actual database cleanup here, such as:
    # - Calling a test cleanup API endpoint
    # - Running Django management commands
    # - Using database transactions that rollback

    # For now, we rely on test isolation and periodic manual cleanup
    if test_emails:
        print(f"\nTest emails created (manual cleanup may be needed): {test_emails}")
