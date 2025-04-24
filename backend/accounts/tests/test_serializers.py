from django.test import TestCase
from accounts.serializers import OnboardingSerializer


class TestOnboardingSerializer(TestCase):
    """Test suite for the OnboardingSerializer."""
    
    def test_valid_user_data(self):
        """Test serializer with valid user data."""
        data = {
            'user': {
                'name': 'Test User',
                'phone_number': '+1234567890'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_valid_school_data(self):
        """Test serializer with valid school data."""
        data = {
            'school': {
                'name': 'Test School',
                'description': 'A test school',
                'contact_email': 'school@example.com',
                'phone_number': '+1234567890',
                'website': 'https://example.com'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_valid_complete_data(self):
        """Test serializer with both valid user and school data."""
        data = {
            'user': {
                'name': 'Test User',
                'phone_number': '+1234567890'
            },
            'school': {
                'name': 'Test School',
                'description': 'A test school',
                'contact_email': 'school@example.com',
                'phone_number': '+1234567890',
                'website': 'https://example.com'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_empty_data(self):
        """Test serializer with empty data."""
        data = {}
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("At least one of 'user' or 'school' information must be provided", 
                     str(serializer.errors))
    
    def test_invalid_user_name(self):
        """Test serializer with invalid user name."""
        # Test empty name
        data = {
            'user': {
                'name': '',
                'phone_number': '+1234567890'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors.get('user', {}))
        
        # Test too long name
        data = {
            'user': {
                'name': 'x' * 151,
                'phone_number': '+1234567890'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors.get('user', {}))
    
    def test_invalid_user_phone(self):
        """Test serializer with invalid user phone number."""
        data = {
            'user': {
                'name': 'Test User',
                'phone_number': 'invalid-phone'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors.get('user', {}))
        
        # Test too long phone number
        data = {
            'user': {
                'name': 'Test User',
                'phone_number': '+' + '1' * 30
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors.get('user', {}))
    
    def test_invalid_school_name(self):
        """Test serializer with invalid school name."""
        # Test empty name
        data = {
            'school': {
                'name': '',
                'description': 'A test school'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors.get('school', {}))
        
        # Test too long name
        data = {
            'school': {
                'name': 'x' * 151,
                'description': 'A test school'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors.get('school', {}))
    
    def test_invalid_school_email(self):
        """Test serializer with invalid school email."""
        data = {
            'school': {
                'name': 'Test School',
                'contact_email': 'invalid-email'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('contact_email', serializer.errors.get('school', {}))
    
    def test_invalid_school_phone(self):
        """Test serializer with invalid school phone number."""
        data = {
            'school': {
                'name': 'Test School',
                'phone_number': 'invalid-phone'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors.get('school', {}))
    
    def test_invalid_school_website(self):
        """Test serializer with invalid school website."""
        data = {
            'school': {
                'name': 'Test School',
                'website': 'invalid-website'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('website', serializer.errors.get('school', {}))
    
    def test_extra_user_fields_ignored(self):
        """Test that extra user fields are ignored."""
        data = {
            'user': {
                'name': 'Test User',
                'extra_field': 'This should be ignored'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('extra_field', serializer.validated_data['user'])
    
    def test_extra_school_fields_ignored(self):
        """Test that extra school fields are ignored."""
        data = {
            'school': {
                'name': 'Test School',
                'extra_field': 'This should be ignored'
            }
        }
        serializer = OnboardingSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('extra_field', serializer.validated_data['school']) 