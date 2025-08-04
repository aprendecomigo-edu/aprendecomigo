"""
Base test classes that ensure consistent test data setup
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from accounts.models import EducationalSystem

User = get_user_model()


class BaseTestCase(TestCase):
    """
    Base test case that ensures default EducationalSystem exists
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_default_educational_system()
    
    @classmethod
    def _ensure_default_educational_system(cls):
        """Ensure the default EducationalSystem with id=1 exists"""
        # Try to get existing system with code 'pt' first
        try:
            cls.default_educational_system = EducationalSystem.objects.get(code='pt')
        except EducationalSystem.DoesNotExist:
            # Create it with id=1 if it doesn't exist
            cls.default_educational_system, created = EducationalSystem.objects.get_or_create(
                id=1,
                defaults={
                    'name': 'Portugal',
                    'code': 'pt',
                    'description': 'Portuguese educational system',
                    'is_active': True
                }
            )


class BaseTransactionTestCase(TransactionTestCase):
    """
    Base transaction test case that ensures default EducationalSystem exists
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_default_educational_system()
    
    @classmethod
    def _ensure_default_educational_system(cls):
        """Ensure the default EducationalSystem with id=1 exists"""
        # Try to get existing system with code 'pt' first
        try:
            cls.default_educational_system = EducationalSystem.objects.get(code='pt')
        except EducationalSystem.DoesNotExist:
            # Create it with id=1 if it doesn't exist
            cls.default_educational_system, created = EducationalSystem.objects.get_or_create(
                id=1,
                defaults={
                    'name': 'Portugal',
                    'code': 'pt',
                    'description': 'Portuguese educational system',
                    'is_active': True
                }
            )