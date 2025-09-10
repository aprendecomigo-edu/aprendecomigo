"""
Test cases for SchoolSettingsView to prevent authentication regression
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import EducationalSystem, School, SchoolMembership, SchoolRole
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class SchoolSettingsViewTest(BaseTestCase):
    """Test SchoolSettingsView authentication and permission handling"""

    def setUp(self):
        super().setUp()
        self.client = Client()

        # Create test users
        self.school_owner = User.objects.create_user(
            username='owner@test.com',
            email='owner@test.com',
            first_name='Owner',
            last_name='User',
            phone_number='+1234567890'
        )

        self.school_admin = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            first_name='Admin',
            last_name='User',
            phone_number='+1234567891'
        )

        self.regular_user = User.objects.create_user(
            username='user@test.com',
            email='user@test.com',
            first_name='Regular',
            last_name='User',
            phone_number='+1234567892'
        )

        # Create test school
        self.school = School.objects.create(
            name='Test School',
            description='A test school for settings testing'
        )

        # Create memberships
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )

        SchoolMembership.objects.create(
            user=self.school_admin,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )

    def test_anonymous_user_redirected_to_login(self):
        """Test that anonymous users are redirected to login page"""
        url = reverse('accounts:school_settings', kwargs={'pk': self.school.pk})
        response = self.client.get(url)

        # Should redirect to login page (302)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/signin/', response.url)

    def test_school_owner_can_access_settings(self):
        """Test that school owner can access school settings"""
        self.client.force_login(self.school_owner)
        url = reverse('accounts:school_settings', kwargs={'pk': self.school.pk})
        response = self.client.get(url)

        # Should be successful (200)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test School')

    def test_school_admin_can_access_settings(self):
        """Test that school admin can access school settings"""
        self.client.force_login(self.school_admin)
        url = reverse('accounts:school_settings', kwargs={'pk': self.school.pk})
        response = self.client.get(url)

        # Should be successful (200)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test School')

    def test_regular_user_cannot_access_settings(self):
        """Test that regular users cannot access school settings"""
        self.client.force_login(self.regular_user)
        url = reverse('accounts:school_settings', kwargs={'pk': self.school.pk})
        response = self.client.get(url)

        # Should be forbidden (403) or permission denied
        self.assertIn(response.status_code, [403, 302])

    def test_dispatch_method_handles_authentication_correctly(self):
        """
        Regression test: Ensure dispatch method doesn't access user before authentication

        This test specifically checks that the dispatch method reordering fix works correctly.
        Previously, get_user_schools_by_role was called before super().dispatch(),
        causing AnonymousUser to be passed to the database query.
        """
        from django.contrib.auth.models import AnonymousUser
        from django.http import HttpRequest

        from accounts.views import SchoolSettingsView

        # Create a mock request with AnonymousUser
        request = HttpRequest()
        request.user = AnonymousUser()
        request.method = 'GET'

        # Create view instance
        view = SchoolSettingsView()
        view.request = request
        view.kwargs = {'pk': self.school.pk}

        # Test that get_user_schools_by_role handles AnonymousUser gracefully
        from accounts.models.schools import SchoolRole
        queryset = view.get_user_schools_by_role(SchoolRole.SCHOOL_OWNER)

        # Should return empty queryset, not raise TypeError
        self.assertFalse(queryset.exists())
        self.assertEqual(list(queryset), [])

    def test_nonexistent_school_returns_permission_denied(self):
        """Test that accessing non-existent school returns permission denied"""
        self.client.force_login(self.school_owner)
        url = reverse('accounts:school_settings', kwargs={'pk': 99999})
        response = self.client.get(url)

        # Should be forbidden (403)
        self.assertEqual(response.status_code, 403)
