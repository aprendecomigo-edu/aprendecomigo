"""
Tests for Django Waffle feature switches functionality.

This module tests the core waffle switch implementation for:
- Schedule feature access control 
- Chat feature access control
- Navigation template rendering based on switch states

Tests verify that features are properly hidden when switches are OFF
and accessible when switches are ON.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from waffle.testutils import override_switch

from accounts.models import School, SchoolMembership

User = get_user_model()


class WaffleSwitchTestCase(TestCase):
    """Base test class with common setup for waffle switch testing."""

    def setUp(self):
        """Set up test data for waffle switch testing."""
        # Create test school and user
        self.school = School.objects.create(
            name="Test School",
            description="School for waffle switch testing"
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        # Create school membership
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role="teacher"
        )
        
        self.client = Client()
        self.client.force_login(self.user)


class ScheduleFeatureSwitchTest(WaffleSwitchTestCase):
    """Test schedule feature switch functionality."""

    @override_switch('schedule_feature', active=False)
    def test_schedule_urls_return_404_when_switch_off(self):
        """Test that schedule URLs return 404 when schedule_feature switch is OFF."""
        schedule_urls = [
            reverse('calendar'),
            # Note: scheduler URLs are not included in main URLs, so we only test calendar
        ]
        
        for url in schedule_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, 
                    404, 
                    f"Expected 404 for {url} when schedule_feature is OFF"
                )

    @override_switch('schedule_feature', active=True)
    def test_schedule_urls_accessible_when_switch_on(self):
        """Test that schedule URLs are accessible when schedule_feature switch is ON."""
        schedule_urls = [
            reverse('calendar'),
            # Note: scheduler URLs are not included in main URLs, so we only test calendar
        ]
        
        for url in schedule_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertNotEqual(
                    response.status_code,
                    404,
                    f"Expected non-404 status for {url} when schedule_feature is ON"
                )


class ChatFeatureSwitchTest(WaffleSwitchTestCase):
    """Test chat feature switch functionality."""

    @override_switch('chat_feature', active=False)
    def test_chat_urls_return_404_when_switch_off(self):
        """Test that chat URLs return 404 when chat_feature switch is OFF."""
        chat_urls = [
            reverse('chat'),
            reverse('chat_user_search'),
            reverse('chat_channels'),
        ]
        
        for url in chat_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    404,
                    f"Expected 404 for {url} when chat_feature is OFF"
                )

    @override_switch('chat_feature', active=True)
    def test_chat_urls_accessible_when_switch_on(self):
        """Test that chat URLs are accessible when chat_feature switch is ON."""
        chat_urls = [
            reverse('chat'),
            reverse('chat_user_search'),
            reverse('chat_channels'),
        ]
        
        for url in chat_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertNotEqual(
                    response.status_code,
                    404,
                    f"Expected non-404 status for {url} when chat_feature is ON"
                )


class NavigationTemplateSwitchTest(WaffleSwitchTestCase):
    """Test navigation template rendering based on waffle switches."""

    @override_switch('chat_feature', active=False)
    def test_chat_navigation_hidden_when_switch_off(self):
        """Test that chat navigation items are hidden when chat_feature switch is OFF."""
        # Get a page that uses base_with_navs.html
        response = self.client.get(reverse('dashboard:dashboard'))
        
        # Verify chat navigation item is not present
        self.assertNotContains(response, "id: 'chat'", msg_prefix="Chat nav should be hidden when switch is OFF")

    @override_switch('chat_feature', active=True)
    def test_chat_navigation_visible_when_switch_on(self):
        """Test that chat navigation items are visible when chat_feature switch is ON."""
        # Get a page that uses base_with_navs.html
        response = self.client.get(reverse('dashboard:dashboard'))
        
        # Verify chat navigation item is present
        self.assertContains(response, "id: 'chat'", msg_prefix="Chat nav should be visible when switch is ON")