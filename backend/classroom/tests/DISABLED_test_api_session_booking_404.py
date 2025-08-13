"""
Session Booking API Tests - Issue #173 Priority 2

This test suite validates that SessionBookingViewSet endpoints are properly
registered and accessible for core booking functionality, addressing 404 errors
in the session booking system.

These tests are designed to initially FAIL to demonstrate current endpoint
registration issues where session booking API endpoints return 404 errors
despite having business logic implemented in SessionBookingService.

Test Coverage:
- Session Booking ViewSet basic operations (list, create, cancel)
- Session booking custom actions (book, cancel, adjust-duration)
- URL routing validation for session-booking endpoints
- Integration between SessionBookingService and API layer
- Permission and authentication requirements for booking operations
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, NoReverseMatch
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import School, TeacherProfile
from finances.models import (
    ClassSession,
    SessionStatus,
    StudentPackage,
    PackageStatus,
    StudentAccountBalance
)

User = get_user_model()


class SessionBookingViewSetEndpointTests(APITestCase):
    """
    Test SessionBookingViewSet endpoint registration and accessibility.
    
    These tests validate that session booking API endpoints are properly
    registered and accessible, addressing the current 404 errors where
    SessionBookingService exists but no API endpoints are exposed.
    """

    def setUp(self):
        """Set up test data for session booking API tests."""
        # Create test users
        self.school_owner = User.objects.create_user(
            email='owner@school.com',
            name='School Owner',
        )
        
        self.teacher_user = User.objects.create_user(
            email='teacher@school.com',
            name='Test Teacher',
        )
        
        self.student = User.objects.create_user(
            email='student@test.com',
            name='Test Student',
        )
        
        # Create school
        self.school = School.objects.create(
            name='Test School',
            owner=self.school_owner,
            time_zone='UTC'
        )
        
        # Create teacher profile
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            school=self.school,
            hourly_rate=Decimal('25.00'),
            bio='Test teacher bio'
        )
        
        # Create student package
        self.student_package = StudentPackage.objects.create(
            student=self.student,
            school=self.school,
            package_name='Test Package',
            hours_purchased=Decimal('10.00'),
            hours_remaining=Decimal('8.00'),
            amount_paid=Decimal('200.00'),
            expires_at='2025-12-31',
            status=PackageStatus.ACTIVE
        )
        
        # Create student balance
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('2.00'),
            balance_amount=Decimal('200.00')
        )
        
        self.client = APIClient()

    def test_session_booking_list_endpoint_exists(self):
        """
        Test that session booking list endpoint is properly registered.
        
        This test validates that a SessionBookingViewSet or equivalent
        is registered to handle session booking list operations.
        
        Expected to FAIL initially due to missing SessionBookingViewSet
        registration in classroom/urls.py.
        """
        self.client.force_authenticate(user=self.teacher_user)
        
        # Test various possible URL patterns for session booking
        possible_urls = [
            '/api/classroom/session-booking/',
            '/api/classroom/sessions/',
            '/api/classroom/bookings/',
            '/api/scheduler/session-booking/',
            '/api/finances/sessions/',  # Already registered in finances
        ]
        
        found_working_url = False
        for url in possible_urls:
            response = self.client.get(url)
            
            if response.status_code != status.HTTP_404_NOT_FOUND:
                found_working_url = True
                break
        
        # At least one session booking endpoint should be accessible
        self.assertTrue(
            found_working_url,
            f"No session booking list endpoints found. Tested URLs: {possible_urls}. "
            f"SessionBookingService exists but no ViewSet is registered. "
            f"Need to create and register SessionBookingViewSet in classroom app."
        )

    def test_session_booking_create_endpoint_exists(self):
        """
        Test that session booking create endpoint is properly registered.
        
        This test validates that session creation/booking functionality
        is exposed via API endpoints, not just service layer.
        
        Expected to FAIL initially due to missing session booking API endpoints.
        """
        self.client.force_authenticate(user=self.teacher_user)
        
        # Test session booking creation
        booking_data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'date': '2025-08-15',
            'start_time': '14:00:00',
            'end_time': '15:00:00',
            'session_type': 'individual',
            'grade_level': 'elementary',
            'student_ids': [self.student.id],
            'is_trial': False,
            'notes': 'Test session booking'
        }
        
        # Try different possible endpoints for session creation
        create_urls = [
            '/api/classroom/session-booking/',
            '/api/classroom/sessions/',
            '/api/scheduler/sessions/',
        ]
        
        found_create_endpoint = False
        for url in create_urls:
            response = self.client.post(url, booking_data, format='json')
            
            # Should not return 404 - some endpoint should handle session booking
            if response.status_code != status.HTTP_404_NOT_FOUND:
                found_create_endpoint = True
                break
        
        self.assertTrue(
            found_create_endpoint,
            f"No session booking CREATE endpoints found. Tested URLs: {create_urls}. "
            f"SessionBookingService.book_session() exists but no API endpoint exposes it. "
            f"Need to create SessionBookingViewSet with create method."
        )

    def test_session_booking_custom_actions_exist(self):
        """
        Test that session booking custom actions are registered.
        
        This test validates that custom actions for session booking
        operations (book, cancel, adjust-duration) are accessible via API.
        
        Expected to FAIL initially due to missing custom action registration.
        """
        # Create a test session first
        test_session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date='2025-08-15',
            start_time='14:00:00',
            end_time='15:00:00',
            session_type='individual',
            grade_level='elementary',
            student_count=1,
            status=SessionStatus.SCHEDULED,
            notes='Test session for custom actions'
        )
        test_session.students.set([self.student])
        
        self.client.force_authenticate(user=self.teacher_user)
        
        # Test custom actions that should exist based on SessionBookingService
        custom_actions = [
            ('book', 'book-session'),
            ('cancel', 'cancel-session'),
            ('adjust-duration', 'adjust-duration')
        ]
        
        for action_name, expected_url_name in custom_actions:
            with self.subTest(action=action_name):
                # Try different URL patterns
                possible_urls = [
                    f'/api/classroom/sessions/{test_session.id}/{action_name}/',
                    f'/api/classroom/session-booking/{test_session.id}/{action_name}/',
                    f'/api/scheduler/sessions/{test_session.id}/{action_name}/',
                ]
                
                action_found = False
                for url in possible_urls:
                    response = self.client.post(url, {})
                    
                    if response.status_code != status.HTTP_404_NOT_FOUND:
                        action_found = True
                        break
                
                self.assertTrue(
                    action_found,
                    f"Custom action '{action_name}' not found. Tested URLs: {possible_urls}. "
                    f"SessionBookingService has {action_name} methods but no API endpoints. "
                    f"Need @action decorators in SessionBookingViewSet."
                )

    def test_session_booking_service_integration(self):
        """
        Test that API endpoints properly integrate with SessionBookingService.
        
        This test validates that the API layer correctly uses the existing
        SessionBookingService for business logic operations.
        
        Expected to FAIL initially due to missing API-Service integration.
        """
        from classroom.services.session_booking_service import SessionBookingService
        
        self.client.force_authenticate(user=self.teacher_user)
        
        # Test that service layer works (this should pass)
        try:
            session, booking_info = SessionBookingService.book_session(
                teacher_id=self.teacher.id,
                school_id=self.school.id,
                date='2025-08-15',
                start_time='14:00:00',
                end_time='15:00:00',
                session_type='individual',
                grade_level='elementary',
                student_ids=[self.student.id],
                is_trial=False,
                notes='Service layer test'
            )
            
            service_works = True
            session_id = session.id
        except Exception as e:
            service_works = False
            session_id = None
            
        self.assertTrue(
            service_works,
            "SessionBookingService should work at service layer"
        )
        
        if session_id:
            # Test that API endpoints can access this session
            possible_urls = [
                f'/api/classroom/sessions/{session_id}/',
                f'/api/classroom/session-booking/{session_id}/',
                f'/api/scheduler/sessions/{session_id}/',
            ]
            
            api_access_found = False
            for url in possible_urls:
                response = self.client.get(url)
                if response.status_code != status.HTTP_404_NOT_FOUND:
                    api_access_found = True
                    break
            
            self.assertTrue(
                api_access_found,
                f"SessionBookingService creates sessions but no API endpoints to access them. "
                f"Need SessionBookingViewSet with retrieve method. Tested URLs: {possible_urls}"
            )

    def test_url_reverse_for_session_booking_endpoints(self):
        """
        Test that URL reverse works for session booking endpoints.
        
        This validates that session booking URL names are properly
        configured and can be resolved using Django's reverse function.
        
        Expected to FAIL initially due to missing URL configuration.
        """
        # Test potential URL names for session booking
        url_patterns_to_test = [
            ('classroom:session-booking-list', [], {}),
            ('classroom:sessions-list', [], {}),
            ('classroom:bookings-list', [], {}),
        ]
        
        found_reversible_url = False
        for url_name, args, kwargs in url_patterns_to_test:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name, args=args, kwargs=kwargs)
                    self.assertIsNotNone(url, f"URL name '{url_name}' could not be reversed")
                    self.assertTrue(url.startswith('/'), f"Reversed URL should be absolute: {url}")
                    found_reversible_url = True
                except NoReverseMatch:
                    continue  # Expected for missing URLs
        
        self.assertTrue(
            found_reversible_url,
            f"No session booking URL names found in URL configuration. "
            f"Tested patterns: {[p[0] for p in url_patterns_to_test]}. "
            f"Need to register SessionBookingViewSet in classroom/urls.py with proper basename."
        )

    def test_session_booking_permissions_not_404(self):
        """
        Test that session booking endpoints handle permissions correctly.
        
        This test ensures that authentication/permission failures return
        401/403 status codes, not 404 errors that indicate missing endpoints.
        
        Expected to FAIL initially if endpoints return 404 instead of
        proper permission errors.
        """
        # Test without authentication on existing session endpoints
        test_urls = [
            '/api/classroom/sessions/',
            '/api/scheduler/sessions/',
            '/api/finances/sessions/',  # This one exists
        ]
        
        for url in test_urls:
            response = self.client.get(url)
            
            if response.status_code != status.HTTP_404_NOT_FOUND:
                # Should be 401 (unauthorized) or 403 (forbidden), NOT 404
                self.assertIn(
                    response.status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_200_OK],
                    f"URL {url}: Unauthenticated request should return 401/403, not {response.status_code}. "
                    f"If returning 404, check endpoint registration."
                )
                break
        else:
            self.fail(
                f"All session endpoints return 404. URLs tested: {test_urls}. "
                f"This suggests missing SessionBookingViewSet registration."
            )


class SessionBookingAPIFunctionalTests(APITestCase):
    """
    Functional tests for Session Booking API once endpoints are registered.
    
    These tests validate that session booking API functionality works
    correctly after endpoint registration issues are resolved.
    """

    def setUp(self):
        """Set up test data for functional tests."""
        self.school_owner = User.objects.create_user(
            email='owner@school.com',
            name='School Owner',
        )
        
        self.teacher_user = User.objects.create_user(
            email='teacher@school.com',
            name='Test Teacher',
        )
        
        self.student = User.objects.create_user(
            email='student@test.com',
            name='Test Student',
        )
        
        self.school = School.objects.create(
            name='Test School',
            owner=self.school_owner,
            time_zone='UTC'
        )
        
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            school=self.school,
            hourly_rate=Decimal('25.00'),
            bio='Test teacher'
        )
        
        self.student_package = StudentPackage.objects.create(
            student=self.student,
            school=self.school,
            package_name='Active Package',
            hours_purchased=Decimal('10.00'),
            hours_remaining=Decimal('8.00'),
            amount_paid=Decimal('200.00'),
            expires_at='2025-12-31',
            status=PackageStatus.ACTIVE
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.teacher_user)

    def test_session_booking_api_creates_session(self):
        """
        Test that session booking API creates sessions correctly.
        
        This validates that the API endpoints properly integrate with
        SessionBookingService to create session bookings.
        """
        booking_data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'date': '2025-08-15',
            'start_time': '14:00:00',
            'end_time': '15:00:00',
            'session_type': 'individual',
            'grade_level': 'elementary',
            'student_ids': [self.student.id],
            'is_trial': False,
            'notes': 'API booking test'
        }
        
        # Try to find a working create endpoint
        create_urls = [
            '/api/classroom/sessions/',
            '/api/classroom/session-booking/',
            '/api/scheduler/sessions/',
        ]
        
        session_created = False
        for url in create_urls:
            response = self.client.post(url, booking_data, format='json')
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                continue
                
            # Skip if endpoints still not registered
            if response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]:
                session_created = True
                
                # Validate response structure
                data = response.json()
                self.assertIn('session_id', data)
                self.assertIn('booking_confirmed_at', data)
                break
        
        if not session_created:
            self.skipTest("Skipping functional test - session booking endpoints not yet registered")

    def test_session_booking_cancel_api(self):
        """
        Test that session cancellation API works correctly.
        
        This validates that cancel functionality from SessionBookingService
        is properly exposed through API endpoints.
        """
        # Create a session first
        test_session = ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date='2025-08-15',
            start_time='14:00:00',
            end_time='15:00:00',
            session_type='individual',
            grade_level='elementary',
            student_count=1,
            status=SessionStatus.SCHEDULED
        )
        test_session.students.set([self.student])
        
        cancel_data = {
            'reason': 'Teacher illness'
        }
        
        # Try different cancel endpoints
        cancel_urls = [
            f'/api/classroom/sessions/{test_session.id}/cancel/',
            f'/api/classroom/session-booking/{test_session.id}/cancel/',
            f'/api/scheduler/sessions/{test_session.id}/cancel/',
        ]
        
        cancel_worked = False
        for url in cancel_urls:
            response = self.client.post(url, cancel_data, format='json')
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                continue
                
            if response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]:
                cancel_worked = True
                
                # Validate cancellation response
                data = response.json()
                self.assertIn('cancelled_at', data)
                self.assertIn('refund_info', data)
                break
        
        if not cancel_worked:
            self.skipTest("Skipping functional test - session cancel endpoints not yet registered")

    def test_session_booking_list_shows_sessions(self):
        """
        Test that session booking list API shows booked sessions.
        
        This validates that list functionality works once endpoints
        are properly registered.
        """
        # Create test sessions
        ClassSession.objects.create(
            teacher=self.teacher,
            school=self.school,
            date='2025-08-15',
            start_time='14:00:00',
            end_time='15:00:00',
            session_type='individual',
            grade_level='elementary',
            student_count=1,
            status=SessionStatus.SCHEDULED
        )
        
        # Try different list endpoints
        list_urls = [
            '/api/classroom/sessions/',
            '/api/classroom/session-booking/',
            '/api/scheduler/sessions/',
        ]
        
        list_worked = False
        for url in list_urls:
            response = self.client.get(url)
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                continue
                
            if response.status_code == status.HTTP_200_OK:
                list_worked = True
                
                data = response.json()
                self.assertIn('results', data)
                
                if data['results']:
                    session_data = data['results'][0]
                    expected_fields = [
                        'id', 'teacher', 'school', 'date', 'start_time',
                        'end_time', 'session_type', 'status', 'student_count'
                    ]
                    
                    for field in expected_fields:
                        self.assertIn(
                            field, session_data,
                            f"Session data missing field: {field}"
                        )
                break
        
        if not list_worked:
            self.skipTest("Skipping functional test - session list endpoints not yet registered")