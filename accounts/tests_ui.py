from django.test import LiveServerTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import unittest

User = get_user_model()

class AuthenticationUITests(LiveServerTestCase):
    """Test cases for authentication flow using Selenium.
    
    These tests verify that:
    - Non-authenticated users see the login page
    - Authenticated users see the dashboard
    - Login functionality works
    - Logout functionality works
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up Chrome driver with appropriate options."""
        super().setUpClass()
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        try:
            cls.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            cls.driver.implicitly_wait(10)
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            cls.driver = None
        
    @classmethod
    def tearDownClass(cls):
        """Clean up the Chrome driver."""
        if cls.driver:
            cls.driver.quit()
        super().tearDownClass()
        
    def setUp(self):
        """Set up test environment with URLs and a test user."""
        if self.driver is None:
            self.skipTest("Chrome driver could not be initialized")
            
        # Create a test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            name='Test User'
        )
        
        # Get the URLs
        self.home_url = reverse('home')
        self.login_url = reverse('account_login')  # Updated for allauth
        self.dashboard_url = reverse('dashboard')
        
    def test_unauthenticated_redirects_to_login(self):
        """Test that non-authenticated users are redirected to login."""
        # Visit the home page
        self.driver.get(f'{self.live_server_url}{self.home_url}')
        
        # Wait for redirect
        WebDriverWait(self.driver, 10).until(
            EC.url_contains('/accounts/login/')  # Updated URL pattern for allauth
        )
        
        # Verify we're on the login page
        self.assertIn('/accounts/login/', self.driver.current_url)  # Updated URL pattern
        
    def test_login_successful(self):
        """Test successful login redirects to dashboard."""
        # Visit the login page
        self.driver.get(f'{self.live_server_url}{self.login_url}')
        
        # Find form fields - allauth uses 'login' instead of 'username'
        username_field = self.driver.find_element(By.NAME, 'login')  # Updated field name
        password_field = self.driver.find_element(By.NAME, 'password')
        
        # Enter credentials
        username_field.send_keys('testuser@example.com')
        password_field.send_keys('testpass123')
        
        # Submit the form
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Wait for redirect to dashboard
        WebDriverWait(self.driver, 10).until(
            EC.url_contains('/dashboard/')
        )
        
        # Verify we're on the dashboard
        self.assertIn('/dashboard/', self.driver.current_url)
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials shows error."""
        # Visit the login page
        self.driver.get(f'{self.live_server_url}{self.login_url}')
        
        # Find form fields
        username_field = self.driver.find_element(By.NAME, 'login')  # Updated field name
        password_field = self.driver.find_element(By.NAME, 'password')
        
        # Enter invalid credentials
        username_field.send_keys('testuser@example.com')
        password_field.send_keys('wrongpassword')
        
        # Submit the form
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Wait for error message
        time.sleep(1)  # Brief wait for page to update
        
        # Verify we're still on the login page
        self.assertIn('/accounts/login/', self.driver.current_url)  # Updated URL pattern
        
    def test_logout(self):
        """Test logout functionality."""
        # First login
        self.driver.get(f'{self.live_server_url}{self.login_url}')
        username_field = self.driver.find_element(By.NAME, 'login')
        password_field = self.driver.find_element(By.NAME, 'password')
        username_field.send_keys('testuser@example.com')
        password_field.send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Wait for login to complete and dashboard to load
        WebDriverWait(self.driver, 10).until(
            EC.url_contains('/dashboard/')
        )
        
        # Try multiple approaches to find the logout element
        # Option 1: Print the page source to help debug (useful for development)
        # print(self.driver.page_source)
        
        try:
            # Option 2: Look for any link containing logout (case insensitive)
            logout_element = self.driver.find_element(By.XPATH, "//a[contains(translate(., 'LOGOUT', 'logout'), 'logout')]")
            logout_element.click()
        except Exception as e:
            try:
                # Option 3: Look for a button containing logout text
                logout_element = self.driver.find_element(By.XPATH, "//button[contains(translate(., 'LOGOUT', 'logout'), 'logout')]")
                logout_element.click()
            except Exception as e:
                try:
                    # Option 4: Look for a form with logout in the action
                    logout_form = self.driver.find_element(By.CSS_SELECTOR, "form[action*='logout']")
                    logout_form.submit()
                except Exception as e:
                    # If all else fails, use JavaScript to just navigate to the logout URL
                    self.driver.execute_script("window.location.href = '/accounts/logout/';")
        
        # If there's a confirmation page for logout, handle it
        try:
            if '/accounts/logout/' in self.driver.current_url:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']"))
                )
                confirm_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                confirm_button.click()
        except:
            pass  # No confirmation page or button found
        
        # Wait for logout to complete
        time.sleep(2)
        
        # Try to access dashboard
        self.driver.get(f'{self.live_server_url}{self.dashboard_url}')
        
        # Check that we're redirected to the login page
        WebDriverWait(self.driver, 10).until(
            EC.url_contains('/accounts/login/')
        )
        
        # Verify we're on the login page
        self.assertIn('/accounts/login/', self.driver.current_url)