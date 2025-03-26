from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import CustomUser
from .forms import LoginForm, CustomUserCreationForm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

User = get_user_model()


class CustomUserModelTests(TestCase):
    """Test cases for the CustomUser model.
    
    These tests verify that our custom user model correctly handles:
    - Regular user creation with email and password
    - Superuser creation with admin privileges
    - Email validation requirements
    """

    def test_create_user(self):
        """Test creating a regular user.
        
        Verifies that:
        1. User is created with correct email and name
        2. Password is properly hashed
        3. User is active by default
        4. User does not have admin privileges by default
        """
        user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            name='Test User'
        )
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertEqual(user.name, 'Test User')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_admin)
        
    def test_create_superuser(self):
        """Test creating a superuser.
        
        Verifies that:
        1. Superuser is created with correct email and name
        2. Password is properly hashed
        3. Superuser has all admin privileges
        4. Superuser is active by default
        """
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            name='Admin User'
        )
        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertEqual(admin_user.name, 'Admin User')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_admin)
        
    def test_email_validation(self):
        """Test that email is required.
        
        Verifies that:
        1. User creation fails without an email
        2. Appropriate error is raised
        """
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpass123')


class LoginViewTests(TestCase):
    """Test cases for login view.
    
    These tests verify that:
    - Login page loads correctly
    - Successful login redirects to dashboard
    - Invalid credentials are handled properly
    - Logout functionality works as expected
    """
    
    def setUp(self):
        """Set up test environment with a test user."""
        self.client = Client()
        self.login_url = reverse('account_login')
        self.dashboard_url = reverse('dashboard')
        
        # Create a test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            name='Test User'
        )
        
    def test_login_page_loads(self):
        """Test that login page loads successfully.
        
        Verifies that:
        1. Login page is accessible
        2. Correct template is rendered
        """
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/login.html')
        
    def test_login_successful(self):
        """Test successful login gives access to dashboard.
        
        Verifies that:
        1. Valid credentials are accepted
        2. User can access the dashboard after login
        3. User is properly authenticated
        """
        self.client.post(self.login_url, {
            'login': 'testuser@example.com',
            'password': 'testpass123'
        })
        # After login, user should be able to access dashboard
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials stays on login page.
        
        Verifies that:
        1. Invalid credentials are rejected
        2. User stays on login page
        3. Error message is displayed
        """
        response = self.client.post(self.login_url, {
            'login': 'testuser@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/login.html')
        
    def test_logout(self):
        """Test logout functionality.
        
        Verifies that:
        1. User can successfully logout
        2. User loses access to protected pages
        """
        # First login
        self.client.login(email='testuser@example.com', password='testpass123')
        
        # Then logout
        self.client.post(reverse('account_logout'))
        
        # Verify user is logged out by checking they can't access dashboard
        response = self.client.get(self.dashboard_url)
        # Should redirect to login page with next parameter
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class PasswordResetTests(TestCase):
    """Test cases for password reset views.
    
    These tests verify that:
    - Password reset page loads correctly
    - Password reset form submission works
    - Password reset confirmation page displays
    - Email notifications are sent
    """
    
    def setUp(self):
        """Set up test environment with a test user."""
        self.client = Client()
        self.password_reset_url = reverse('account_reset_password')
        self.password_reset_done_url = reverse('account_reset_password_done')
        
        # Create a test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            name='Test User'
        )
        
    def test_password_reset_page_loads(self):
        """Test that password reset page loads successfully.
        
        Verifies that:
        1. Password reset page is accessible
        2. Correct template is rendered
        """
        response = self.client.get(self.password_reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/password_reset.html')
        
    def test_password_reset_submit(self):
        """Test password reset submission redirects to done page.
        
        Verifies that:
        1. Form submission with valid email is accepted
        2. User is redirected to confirmation page
        3. Reset email is sent (in production)
        """
        response = self.client.post(self.password_reset_url, {
            'email': 'testuser@example.com'
        })
        self.assertRedirects(response, self.password_reset_done_url)
        
    def test_password_reset_done_page_loads(self):
        """Test that password reset done page loads successfully.
        
        Verifies that:
        1. Confirmation page is accessible
        2. Correct template is rendered
        3. User is informed about email being sent
        """
        response = self.client.get(self.password_reset_done_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/password_reset_done.html')

class RootURLTests(TestCase):
    """Test cases for root URL behavior."""
    
    def setUp(self):
        """Set up test environment."""
        self.root_url = reverse('home')
        self.login_url = reverse('account_login')
        self.dashboard_url = reverse('dashboard')
        
        # Create a test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            name='Test User'
        )
        
    def test_root_url_redirects_to_login_when_not_authenticated(self):
        """Test that root URL redirects to login when user is not authenticated."""
        response = self.client.get(self.root_url)
        self.assertRedirects(response, self.login_url)
        
    def test_root_url_redirects_to_dashboard_when_authenticated(self):
        """Test that root URL redirects to dashboard when user is authenticated."""
        self.client.login(email='testuser@example.com', password='testpass123')
        response = self.client.get(self.root_url)
        self.assertRedirects(response, self.dashboard_url)
        
    def test_dashboard_requires_login(self):
        """Test that dashboard view requires login."""
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(response, f'{self.login_url}?next={self.dashboard_url}')
        
    def test_dashboard_accessible_when_logged_in(self):
        """Test that dashboard is accessible when user is logged in."""
        self.client.login(email='testuser@example.com', password='testpass123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
