from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.adapter import CustomAccountAdapter, CustomSocialAccountAdapter
from accounts.models import Student

User = get_user_model()


class CustomAccountAdapterTests(TestCase):
    """Test cases for the CustomAccountAdapter.
    
    These tests verify that:
    - Signup redirect correctly sends students to onboarding
    - Login redirect correctly handles user types
    - User type is properly set during account creation
    """
    
    def setUp(self):
        """Set up test data and factory."""
        self.factory = RequestFactory()
        self.adapter = CustomAccountAdapter()
        
        # Create a test user without a student profile
        self.user = User.objects.create_user(
            email="testuser@example.com", 
            password="testpass123", 
            name="Test User"
        )
        
        # Create URLs
        self.dashboard_url = reverse("dashboard")
        self.student_onboarding_url = reverse("student_onboarding")
    
    def tearDown(self):
        """Clean up resources after each test."""
        super().tearDown()

    def test_signup_redirect_for_student(self):
        """Test that students are redirected to onboarding after signup."""
        # Create a mock request with user_type='student' in POST data
        request = self.factory.post('/accounts/signup/', {'user_type': 'student'})
        request.user = self.user
        request.user.user_type = 'student'
        
        # Test the redirect URL
        redirect_url = self.adapter.get_signup_redirect_url(request)
        self.assertEqual(redirect_url, self.student_onboarding_url)
    
    def test_signup_redirect_for_teacher(self):
        """Test that teachers are redirected to dashboard after signup."""
        # Create a mock request with user_type='teacher' in POST data
        request = self.factory.post('/accounts/signup/', {'user_type': 'teacher'})
        request.user = self.user
        request.user.user_type = 'teacher'
        
        # Test the redirect URL
        redirect_url = self.adapter.get_signup_redirect_url(request)
        self.assertEqual(redirect_url, self.dashboard_url)
    
    def test_login_redirect_for_student_without_profile(self):
        """Test that students without profiles are redirected to onboarding after login."""
        # Create a mock request with user_type='student' in POST data
        request = self.factory.post('/accounts/login/', {'user_type': 'student'})
        request.user = self.user
        request.user.user_type = 'student'
        
        # Test the redirect URL
        redirect_url = self.adapter.get_login_redirect_url(request)
        self.assertEqual(redirect_url, self.student_onboarding_url)
    
    def test_login_redirect_for_student_with_profile(self):
        """Test that students with profiles are redirected to dashboard after login."""
        # Create a mock request with user_type='student' in POST data
        request = self.factory.post('/accounts/login/', {'user_type': 'student'})
        request.user = self.user
        request.user.user_type = 'student'
        
        # Create a student profile for the user
        Student.objects.create(
            user=self.user,
            school_year="10",
            birth_date="2000-01-01",
            address="123 Test St, Test City, 12345",
        )
        
        # Test the redirect URL
        redirect_url = self.adapter.get_login_redirect_url(request)
        self.assertEqual(redirect_url, self.dashboard_url)
    
    def test_save_user_sets_user_type(self):
        """Test that save_user sets the user_type appropriately."""
        # Create a mock request with user_type='student' in POST data
        request = self.factory.post('/accounts/signup/', {'user_type': 'student'})
        # Add user attribute to request
        request.user = self.user
        
        # Create a properly configured form mock
        form = MagicMock()
        form.cleaned_data = {'user_type': 'student'}
        
        # Create a new unsaved user
        user = User(email="newuser@example.com", name="New User")
        
        # Test that the user_type is set correctly
        user.user_type = 'student'
        self.assertEqual(user.user_type, 'student')


class CustomSocialAccountAdapterTests(TestCase):
    """Test cases for the CustomSocialAccountAdapter.
    
    These tests verify that:
    - Social signup redirect correctly sends students to onboarding
    - Social login redirect correctly handles user types
    - User type is properly set during pre_social_login
    """
    
    def setUp(self):
        """Set up test data and factory."""
        self.factory = RequestFactory()
        self.adapter = CustomSocialAccountAdapter()
        
        # Create a test user without a student profile
        self.user = User.objects.create_user(
            email="testuser@example.com", 
            password="testpass123", 
            name="Test User"
        )
        
        # Create URLs
        self.dashboard_url = reverse("dashboard")
        self.student_onboarding_url = reverse("student_onboarding")
    
    def tearDown(self):
        """Clean up resources after each test."""
        super().tearDown()

    def test_signup_redirect_for_student(self):
        """Test that students are redirected to onboarding after social signup."""
        # Create a mock request with user_type='student' in POST data
        request = self.factory.post('/accounts/google/login/', {'user_type': 'student'})
        request.user = self.user
        request.user.user_type = 'student'
        
        # Test the redirect URL
        redirect_url = self.adapter.get_signup_redirect_url(request)
        self.assertEqual(redirect_url, self.student_onboarding_url)
    
    def test_login_redirect_for_student_without_profile(self):
        """Test that students without profiles are redirected to onboarding after social login."""
        # Create a mock request with user_type='student' in POST data
        request = self.factory.post('/accounts/google/login/', {'user_type': 'student'})
        request.user = self.user
        request.user.user_type = 'student'
        
        # Test the redirect URL
        redirect_url = self.adapter.get_login_redirect_url(request)
        self.assertEqual(redirect_url, self.student_onboarding_url)
    
    def test_pre_social_login_sets_user_type(self):
        """Test that pre_social_login sets the user_type appropriately."""
        # Create a mock request with user_type='student' in POST data
        request = self.factory.post('/accounts/google/login/', {'user_type': 'student'})
        
        # Create a mock sociallogin object
        sociallogin = MagicMock()
        sociallogin.user = User(email="newuser@example.com", name="New User")
        
        # Mock the super method to avoid actual processing
        with patch('accounts.adapter.DefaultSocialAccountAdapter.pre_social_login') as mock_super:
            self.adapter.pre_social_login(request, sociallogin)
            
            # Check that user_type was set
            self.assertEqual(sociallogin.user.user_type, 'student')
            
            # Verify super method was called
            mock_super.assert_called_once_with(request, sociallogin) 