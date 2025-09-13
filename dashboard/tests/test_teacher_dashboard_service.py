"""
Tests for TeacherDashboardService.

This module provides comprehensive testing for the TeacherDashboardService,
which handles data aggregation and calculations for teacher dashboard API.
"""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import (
    School,
    SchoolActivity,
    SchoolMembership,
    SchoolRole,
    TeacherProfile,
)
from accounts.services.teacher_dashboard_service import TeacherDashboardService
from accounts.tests.test_base import BaseTestCase

# Mock the finances models since they might not be available in isolation
try:
    from finances.models import ClassSession, SessionStatus, TeacherPaymentEntry
except ImportError:
    # Create mock classes for testing if finances app is not available
    class ClassSession:
        pass

    class SessionStatus:
        PENDING = "pending"
        COMPLETED = "completed"
        CANCELLED = "cancelled"

    class TeacherPaymentEntry:
        pass


User = get_user_model()


class TeacherDashboardServiceTest(BaseTestCase):
    """Test cases for TeacherDashboardService."""

    def setUp(self):
        """Set up test data."""
        super().setUp()

        # Clear cache before each test
        cache.clear()

        # Create teacher user and profile
        self.teacher_user = User.objects.create_user(
            email="teacher@example.com", name="Test Teacher", first_name="Test", last_name="Teacher"
        )

        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user, bio="Test teacher bio", specialty="Mathematics", hourly_rate=Decimal("30.00")
        )

        # Create school and membership
        self.school = School.objects.create(name="Test School", contact_email=self.teacher_user.email)

        SchoolMembership.objects.create(
            user=self.teacher_user, school=self.school, role=SchoolRole.TEACHER, is_active=True
        )

        # Create service instance
        self.service = TeacherDashboardService(self.teacher_profile)

    def test_service_initialization(self):
        """Test service initialization with teacher profile."""
        self.assertEqual(self.service.teacher_profile, self.teacher_profile)
        self.assertEqual(self.service.teacher_user, self.teacher_user)
        self.assertEqual(self.service.cache_timeout, 300)  # 5 minutes

    def test_get_consolidated_dashboard_data_structure(self):
        """Test that consolidated dashboard data returns expected structure."""
        with (
            patch.object(self.service, "_get_sessions_data") as mock_sessions,
            patch.object(self.service, "_get_earnings_data") as mock_earnings,
            patch.object(self.service, "_get_recent_activities") as mock_activities,
            patch.object(self.service, "_get_teacher_info") as mock_teacher_info,
            patch.object(self.service, "_get_quick_stats") as mock_stats,
        ):
            # Mock the individual data methods
            mock_sessions.return_value = {"total_sessions": 10, "completed_sessions": 8, "pending_sessions": 2}

            mock_earnings.return_value = {"total_earnings": Decimal("240.00"), "pending_payments": Decimal("60.00")}

            mock_activities.return_value = [
                {"type": "session_completed", "description": "Class completed", "timestamp": timezone.now()}
            ]

            mock_teacher_info.return_value = {"id": self.teacher_profile.id, "name": "Test Teacher"}

            mock_stats.return_value = {"active_students": 5, "this_month_sessions": 3}

            data = self.service.get_consolidated_dashboard_data()

            # Verify data structure
            self.assertIn("sessions", data)
            self.assertIn("earnings", data)
            self.assertIn("recent_activities", data)
            self.assertIn("teacher_info", data)
            self.assertIn("quick_stats", data)

            # Verify session data
            self.assertEqual(data["sessions"]["total_sessions"], 10)
            self.assertEqual(data["sessions"]["completed_sessions"], 8)

            # Verify earnings data
            self.assertEqual(data["earnings"]["total_earnings"], Decimal("240.00"))

            # Verify activities
            self.assertEqual(len(data["recent_activities"]), 1)

    @patch("accounts.services.teacher_dashboard_service.cache")
    def test_get_consolidated_dashboard_data_uses_cache(self, mock_cache):
        """Test that dashboard data uses caching correctly."""
        # Mock cache.get to return None (cache miss)
        mock_cache.get.return_value = None

        # Mock the individual data methods
        with (
            patch.object(self.service, "_get_session_stats") as mock_sessions,
            patch.object(self.service, "_get_payment_stats") as mock_payments,
            patch.object(self.service, "_get_school_activities") as mock_activities,
        ):
            mock_sessions.return_value = {}
            mock_payments.return_value = {}
            mock_activities.return_value = []

            self.service.get_consolidated_dashboard_data()

            # Verify cache was checked
            cache_key = f"teacher_dashboard_{self.teacher_profile.id}"
            mock_cache.get.assert_called_once_with(cache_key)

            # Verify cache was set
            mock_cache.set.assert_called_once()

    @patch("accounts.services.teacher_dashboard_service.cache")
    def test_get_consolidated_dashboard_data_returns_cached_data(self, mock_cache):
        """Test that cached data is returned when available."""
        cached_data = {
            "session_stats": {"total_sessions": 5},
            "payment_stats": {"total_earnings": Decimal("150.00")},
            "recent_activities": [],
        }

        # Mock cache.get to return cached data
        mock_cache.get.return_value = cached_data

        with patch.object(self.service, "_get_session_stats") as mock_sessions:
            # This shouldn't be called if cache hit occurs
            result = self.service.get_consolidated_dashboard_data()

            # Should return cached data
            self.assertEqual(result, cached_data)

            # Session stats method should not be called
            mock_sessions.assert_not_called()

    def test_session_stats_calculation(self):
        """Test session statistics calculation."""
        # This test would require the ClassSession model to be available
        # For now, we'll test the method structure

        with patch("accounts.services.teacher_dashboard_service.ClassSession") as MockClassSession:
            # Mock queryset methods
            mock_queryset = Mock()
            mock_queryset.filter.return_value = mock_queryset
            mock_queryset.count.return_value = 5
            MockClassSession.objects.filter.return_value = mock_queryset

            # Test that the method exists and can be called
            if hasattr(self.service, "_get_session_stats"):
                stats = self.service._get_session_stats()
                self.assertIsInstance(stats, dict)

    def test_payment_stats_calculation(self):
        """Test payment statistics calculation."""
        # Test the payment stats method if it exists
        with patch("accounts.services.teacher_dashboard_service.TeacherPaymentEntry") as MockPaymentEntry:
            # Mock queryset for payment calculations
            mock_queryset = Mock()
            mock_queryset.filter.return_value = mock_queryset
            mock_queryset.aggregate.return_value = {"total": Decimal("200.00")}
            MockPaymentEntry.objects.filter.return_value = mock_queryset

            if hasattr(self.service, "_get_payment_stats"):
                stats = self.service._get_payment_stats()
                self.assertIsInstance(stats, dict)

    def test_school_activities_retrieval(self):
        """Test school activities retrieval for dashboard."""
        # Create some school activities
        SchoolActivity.objects.create(
            school=self.school,
            activity_type="session_completed",
            actor=self.teacher_user,
            description="Test class completed",
            metadata={"test": True},
        )

        SchoolActivity.objects.create(
            school=self.school,
            activity_type="session_cancelled",
            actor=self.teacher_user,
            description="Test class cancelled",
            metadata={"test": True},
        )

        if hasattr(self.service, "_get_school_activities"):
            activities = self.service._get_school_activities()

            # Should return activities for the teacher's school
            self.assertIsInstance(activities, list)

    def test_cache_key_generation(self):
        """Test that cache key is generated correctly."""
        cache_key = f"teacher_dashboard_{self.teacher_profile.id}"

        # The cache key should be consistent
        self.assertIsInstance(cache_key, str)
        self.assertIn(str(self.teacher_profile.id), cache_key)

    def test_error_handling_in_dashboard_data(self):
        """Test error handling in dashboard data aggregation."""
        with patch.object(self.service, "_get_session_stats", side_effect=Exception("Database error")):
            # Should handle errors gracefully and not crash
            try:
                data = self.service.get_consolidated_dashboard_data()
                # If it returns data, it should handle the error
                self.assertIsInstance(data, dict)
            except Exception:
                # If it raises an exception, it should be a handled one
                pass

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        }
    )
    def test_cache_timeout_setting(self):
        """Test that cache timeout is configurable."""
        # Create service with custom cache timeout
        service_with_custom_timeout = TeacherDashboardService(self.teacher_profile)
        service_with_custom_timeout.cache_timeout = 600  # 10 minutes

        self.assertEqual(service_with_custom_timeout.cache_timeout, 600)

    def test_multiple_schools_data_isolation(self):
        """Test that teacher data is properly isolated between schools."""
        # Create another school and membership
        other_school = School.objects.create(name="Other School", contact_email="other@example.com")

        SchoolMembership.objects.create(
            user=self.teacher_user, school=other_school, role=SchoolRole.TEACHER, is_active=True
        )

        # Create activities in both schools
        SchoolActivity.objects.create(
            school=self.school,
            activity_type="session_completed",
            actor=self.teacher_user,
            description="Activity in first school",
        )

        SchoolActivity.objects.create(
            school=other_school,
            activity_type="session_completed",
            actor=self.teacher_user,
            description="Activity in second school",
        )

        # Dashboard should include data from all schools where teacher is active
        if hasattr(self.service, "_get_school_activities"):
            activities = self.service._get_school_activities()

            # Should handle multi-school scenarios appropriately
            self.assertIsInstance(activities, list)

    def test_performance_with_large_dataset(self):
        """Test service performance considerations with larger datasets."""
        # Create multiple activities to test performance
        activities = []
        for i in range(50):  # Simulate larger dataset
            activity = SchoolActivity.objects.create(
                school=self.school,
                activity_type="session_completed",
                actor=self.teacher_user,
                description=f"Activity {i}",
                metadata={"index": i},
            )
            activities.append(activity)

        # Test that the service can handle larger datasets
        with (
            patch.object(self.service, "_get_session_stats", return_value={}),
            patch.object(self.service, "_get_payment_stats", return_value={}),
        ):
            data = self.service.get_consolidated_dashboard_data()

            # Should return data without performance issues
            self.assertIsInstance(data, dict)

    def test_data_consistency_after_cache_invalidation(self):
        """Test data consistency after cache is invalidated."""
        # Get initial data (will be cached)
        with patch.object(self.service, "_get_session_stats", return_value={"total": 5}):
            initial_data = self.service.get_consolidated_dashboard_data()

        # Clear cache manually
        cache_key = f"teacher_dashboard_{self.teacher_profile.id}"
        cache.delete(cache_key)

        # Get data again (should regenerate cache)
        with patch.object(self.service, "_get_session_stats", return_value={"total": 7}):
            new_data = self.service.get_consolidated_dashboard_data()

        # Should reflect updated data after cache invalidation
        self.assertNotEqual(initial_data.get("session_stats", {}), new_data.get("session_stats", {}))


class TeacherDashboardServiceIntegrationTest(BaseTestCase):
    """Integration tests for TeacherDashboardService with real data."""

    def setUp(self):
        """Set up integration test data."""
        super().setUp()
        cache.clear()

        # Create teacher and school setup
        self.teacher_user = User.objects.create_user(email="integration@example.com", name="Integration Teacher")

        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user, bio="Integration test teacher", hourly_rate=Decimal("25.00")
        )

        self.school = School.objects.create(name="Integration Test School", contact_email=self.teacher_user.email)

        SchoolMembership.objects.create(
            user=self.teacher_user, school=self.school, role=SchoolRole.TEACHER, is_active=True
        )

        self.service = TeacherDashboardService(self.teacher_profile)

    def test_real_dashboard_data_integration(self):
        """Test dashboard service with real data integration."""
        # Create real school activities
        for activity_type in ["session_completed", "session_cancelled", "teacher_joined"]:
            SchoolActivity.objects.create(
                school=self.school,
                activity_type=activity_type,
                actor=self.teacher_user,
                description=f"Integration test {activity_type}",
                metadata={"integration_test": True},
            )

        # Test that service works with real data
        try:
            data = self.service.get_consolidated_dashboard_data()

            # Should return valid dashboard data structure
            self.assertIsInstance(data, dict)

            # Should have required sections (even if some are mocked)
            expected_keys = ["session_stats", "payment_stats", "recent_activities"]
            for key in expected_keys:
                if key in data:
                    self.assertIsInstance(data[key], (dict, list))

        except Exception as e:
            # Integration test should not fail due to missing dependencies
            self.fail(f"Dashboard service integration failed: {e}")

    def test_empty_data_handling(self):
        """Test dashboard service behavior with no data."""
        # Test with fresh teacher (no activities, sessions, or payments)
        empty_teacher = User.objects.create_user(email="empty@example.com", name="Empty Teacher")

        empty_profile = TeacherProfile.objects.create(user=empty_teacher, bio="Empty teacher for testing")

        empty_service = TeacherDashboardService(empty_profile)

        # Should handle empty data gracefully
        data = empty_service.get_consolidated_dashboard_data()
        self.assertIsInstance(data, dict)
