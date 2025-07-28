"""
Test suite for School Dashboard API endpoints following TDD methodology.
Tests for metrics, activity feed, and school update endpoints.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolRole,
    EducationalSystem, SchoolActivity, ActivityType
)
from finances.models import ClassSession


class SchoolMetricsAPITest(TestCase):
    """Test cases for School Metrics API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test users
        self.school_owner = CustomUser.objects.create_user(
            email='owner@test.com',
            name='School Owner'
        )
        self.teacher1 = CustomUser.objects.create_user(
            email='teacher1@test.com',
            name='Teacher One'
        )
        self.teacher2 = CustomUser.objects.create_user(
            email='teacher2@test.com',
            name='Teacher Two'
        )
        self.student1 = CustomUser.objects.create_user(
            email='student1@test.com',
            name='Student One'
        )
        self.student2 = CustomUser.objects.create_user(
            email='student2@test.com',
            name='Student Two'
        )
        self.unauthorized_user = CustomUser.objects.create_user(
            email='unauthorized@test.com',
            name='Unauthorized User'
        )
        
        # Create test school
        self.school = School.objects.create(
            name='Test School',
            description='A test school'
        )
        
        # Create school memberships
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
        SchoolMembership.objects.create(
            user=self.teacher1,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        SchoolMembership.objects.create(
            user=self.teacher2,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=False  # Inactive teacher
        )
        SchoolMembership.objects.create(
            user=self.student1,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        SchoolMembership.objects.create(
            user=self.student2,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        # Create educational system for classes
        self.ed_system = EducationalSystem.objects.create(
            name='Test System',
            code='test'
        )
        
    def test_get_school_metrics_unauthorized(self):
        """Test metrics endpoint requires authentication"""
        url = reverse('accounts:school-dashboard-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_get_school_metrics_non_admin(self):
        """Test metrics endpoint requires admin/owner role"""
        self.client.force_authenticate(user=self.teacher1)
        url = reverse('accounts:school-dashboard-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_get_school_metrics_success(self):
        """Test successful metrics retrieval"""
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check student metrics
        self.assertEqual(data['student_count']['total'], 2)
        self.assertEqual(data['student_count']['active'], 2)
        self.assertEqual(data['student_count']['inactive'], 0)
        
        # Check teacher metrics
        self.assertEqual(data['teacher_count']['total'], 2)
        self.assertEqual(data['teacher_count']['active'], 1)
        self.assertEqual(data['teacher_count']['inactive'], 1)
        
        # Check structure includes trends
        self.assertIn('trend', data['student_count'])
        self.assertIn('daily', data['student_count']['trend'])
        self.assertIn('weekly', data['student_count']['trend'])
        self.assertIn('monthly', data['student_count']['trend'])
        
    def test_get_school_metrics_with_classes(self):
        """Test metrics with class data"""
        # Create some class sessions
        today = timezone.now()
        ClassSession.objects.create(
            school=self.school,
            teacher=self.teacher1,
            student=self.student1,
            date=today.date(),
            time=today.time(),
            duration=timedelta(hours=1),
            subject='Math',
            educational_system=self.ed_system,
            school_year='1',
            status='scheduled'
        )
        ClassSession.objects.create(
            school=self.school,
            teacher=self.teacher1,
            student=self.student2,
            date=today.date(),
            time=(today - timedelta(hours=2)).time(),
            duration=timedelta(hours=1),
            subject='Science',
            educational_system=self.ed_system,
            school_year='1',
            status='completed'
        )
        
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check class metrics
        self.assertEqual(data['class_metrics']['scheduled_today'], 1)
        self.assertEqual(data['class_metrics']['completed_today'], 1)
        self.assertIn('completion_rate', data['class_metrics'])
        
    def test_get_school_metrics_with_invitations(self):
        """Test metrics with invitation data"""
        from accounts.models import SchoolInvitation
        
        # Create some invitations
        SchoolInvitation.objects.create(
            school=self.school,
            email='new1@test.com',
            invited_by=self.school_owner,
            role=SchoolRole.TEACHER,
            token='token1',
            expires_at=timezone.now() + timedelta(days=7),
            is_accepted=False
        )
        SchoolInvitation.objects.create(
            school=self.school,
            email='new2@test.com',
            invited_by=self.school_owner,
            role=SchoolRole.STUDENT,
            token='token2',
            expires_at=timezone.now() + timedelta(days=7),
            is_accepted=True
        )
        
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check engagement metrics
        self.assertEqual(data['engagement_metrics']['invitations_sent'], 2)
        self.assertEqual(data['engagement_metrics']['invitations_accepted'], 1)
        self.assertEqual(data['engagement_metrics']['acceptance_rate'], 50.0)
        
    @patch('django.core.cache.cache.get')
    @patch('django.core.cache.cache.set')
    def test_get_school_metrics_caching(self, mock_cache_set, mock_cache_get):
        """Test that metrics are cached properly"""
        mock_cache_get.return_value = None  # Cache miss
        
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-metrics', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cache was set with 5-minute TTL
        mock_cache_set.assert_called_once()
        cache_key = f'school_metrics_{self.school.id}'
        self.assertEqual(mock_cache_set.call_args[0][0], cache_key)
        self.assertEqual(mock_cache_set.call_args[1]['timeout'], 300)  # 5 minutes


class SchoolActivityFeedAPITest(TestCase):
    """Test cases for School Activity Feed API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test users
        self.school_owner = CustomUser.objects.create_user(
            email='owner@test.com',
            name='School Owner'
        )
        self.teacher = CustomUser.objects.create_user(
            email='teacher@test.com',
            name='Teacher User'
        )
        
        # Create test school
        self.school = School.objects.create(
            name='Test School',
            description='A test school'
        )
        
        # Create school membership
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
        
    def test_get_activity_feed_unauthorized(self):
        """Test activity feed endpoint requires authentication"""
        url = reverse('accounts:school-dashboard-activity', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_get_activity_feed_success(self):
        """Test successful activity feed retrieval"""
        from accounts.models import SchoolActivity, ActivityType
        
        # Create some activities
        activity1 = SchoolActivity.objects.create(
            school=self.school,
            activity_type=ActivityType.INVITATION_SENT,
            actor=self.school_owner,
            description="Invited teacher@test.com as a teacher",
            metadata={'email': 'teacher@test.com', 'role': 'teacher'}
        )
        activity2 = SchoolActivity.objects.create(
            school=self.school,
            activity_type=ActivityType.TEACHER_JOINED,
            actor=self.teacher,
            target_user=self.teacher,
            description="Teacher User joined as a teacher"
        )
        
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-activity', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check pagination structure
        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)
        self.assertIn('results', data)
        
        # Check activity structure
        self.assertEqual(len(data['results']), 2)
        
        # Most recent activity should be first
        first_activity = data['results'][0]
        self.assertEqual(first_activity['activity_type'], ActivityType.TEACHER_JOINED)
        self.assertIn('id', first_activity)
        self.assertIn('timestamp', first_activity)
        self.assertIn('actor', first_activity)
        self.assertIn('description', first_activity)
        
    def test_get_activity_feed_pagination(self):
        """Test activity feed pagination"""
        from accounts.models import SchoolActivity, ActivityType
        
        # Create 25 activities
        for i in range(25):
            SchoolActivity.objects.create(
                school=self.school,
                activity_type=ActivityType.STUDENT_JOINED,
                actor=self.school_owner,
                description=f"Activity {i}"
            )
            
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-activity', kwargs={'pk': self.school.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Default page size is 20
        self.assertEqual(len(data['results']), 20)
        self.assertEqual(data['count'], 25)
        self.assertIsNotNone(data['next'])
        
        # Test page 2
        response = self.client.get(url, {'page': 2})
        data = response.json()
        self.assertEqual(len(data['results']), 5)
        self.assertIsNone(data['next'])
        self.assertIsNotNone(data['previous'])
        
    def test_get_activity_feed_filtering(self):
        """Test activity feed filtering by type and date"""
        from accounts.models import SchoolActivity, ActivityType
        
        # Create activities of different types
        SchoolActivity.objects.create(
            school=self.school,
            activity_type=ActivityType.INVITATION_SENT,
            actor=self.school_owner,
            description="Invitation sent"
        )
        SchoolActivity.objects.create(
            school=self.school,
            activity_type=ActivityType.TEACHER_JOINED,
            actor=self.teacher,
            description="Teacher joined"
        )
        SchoolActivity.objects.create(
            school=self.school,
            activity_type=ActivityType.STUDENT_JOINED,
            actor=self.school_owner,
            description="Student joined"
        )
        
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-activity', kwargs={'pk': self.school.id})
        
        # Filter by activity types
        response = self.client.get(url, {
            'activity_types': 'invitation_sent,teacher_joined'
        })
        data = response.json()
        
        self.assertEqual(data['count'], 2)
        activity_types = [a['activity_type'] for a in data['results']]
        self.assertIn(ActivityType.INVITATION_SENT, activity_types)
        self.assertIn(ActivityType.TEACHER_JOINED, activity_types)
        self.assertNotIn(ActivityType.STUDENT_JOINED, activity_types)
        
    def test_get_activity_feed_date_filtering(self):
        """Test activity feed filtering by date range"""
        from accounts.models import SchoolActivity, ActivityType
        
        # Create activities with different timestamps
        yesterday = timezone.now() - timedelta(days=1)
        last_week = timezone.now() - timedelta(days=7)
        
        activity1 = SchoolActivity.objects.create(
            school=self.school,
            activity_type=ActivityType.STUDENT_JOINED,
            actor=self.school_owner,
            description="Recent activity"
        )
        
        # Create an older activity
        activity2 = SchoolActivity.objects.create(
            school=self.school,
            activity_type=ActivityType.TEACHER_JOINED,
            actor=self.teacher,
            description="Old activity"
        )
        activity2.timestamp = last_week
        activity2.save()
        
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-activity', kwargs={'pk': self.school.id})
        
        # Filter by date range (only recent)
        response = self.client.get(url, {
            'date_from': yesterday.isoformat(),
            'date_to': timezone.now().isoformat()
        })
        data = response.json()
        
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['description'], "Recent activity")


class SchoolUpdateAPITest(TestCase):
    """Test cases for School Update API endpoint enhancement"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test users
        self.school_owner = CustomUser.objects.create_user(
            email='owner@test.com',
            name='School Owner'
        )
        self.school_admin = CustomUser.objects.create_user(
            email='admin@test.com',
            name='School Admin'
        )
        self.teacher = CustomUser.objects.create_user(
            email='teacher@test.com',
            name='Teacher User'
        )
        
        # Create test school
        self.school = School.objects.create(
            name='Test School',
            description='A test school'
        )
        
        # Create school memberships
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
        SchoolMembership.objects.create(
            user=self.school_admin,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        SchoolMembership.objects.create(
            user=self.teacher,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
    def test_update_school_unauthorized(self):
        """Test school update requires authentication"""
        url = reverse('accounts:school-dashboard-detail', kwargs={'pk': self.school.id})
        response = self.client.patch(url, {'name': 'Updated School'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_update_school_non_admin(self):
        """Test school update requires admin/owner role"""
        self.client.force_authenticate(user=self.teacher)
        url = reverse('accounts:school-dashboard-detail', kwargs={'pk': self.school.id})
        response = self.client.patch(url, {'name': 'Updated School'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_update_school_basic_info(self):
        """Test updating basic school information"""
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-detail', kwargs={'pk': self.school.id})
        
        update_data = {
            'name': 'Updated School Name',
            'description': 'Updated description',
            'address': '123 New Street',
            'contact_email': 'school@test.com',
            'phone_number': '+351123456789',
            'website': 'https://school.test.com'
        }
        
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify updates
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, 'Updated School Name')
        self.assertEqual(self.school.description, 'Updated description')
        self.assertEqual(self.school.contact_email, 'school@test.com')
        self.assertEqual(self.school.website, 'https://school.test.com')
        
    def test_update_school_settings(self):
        """Test updating school settings"""
        from accounts.models import SchoolSettings, TrialCostAbsorption
        
        # Create initial settings
        SchoolSettings.objects.create(school=self.school)
        
        self.client.force_authenticate(user=self.school_admin)
        url = reverse('accounts:school-dashboard-detail', kwargs={'pk': self.school.id})
        
        update_data = {
            'settings': {
                'trial_cost_absorption': 'teacher',
                'default_session_duration': 90,
                'timezone': 'Europe/Lisbon'
            }
        }
        
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify settings were updated
        settings = self.school.settings
        self.assertEqual(settings.trial_cost_absorption, 'teacher')
        self.assertEqual(settings.default_session_duration, 90)
        self.assertEqual(settings.timezone, 'Europe/Lisbon')
        
    def test_update_school_partial_update(self):
        """Test partial update works correctly"""
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-detail', kwargs={'pk': self.school.id})
        
        # Update only name
        response = self.client.patch(url, {'name': 'Partially Updated'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, 'Partially Updated')
        # Other fields should remain unchanged
        self.assertEqual(self.school.description, 'A test school')
        
    def test_update_school_invalid_email(self):
        """Test validation for email field"""
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-detail', kwargs={'pk': self.school.id})
        
        response = self.client.patch(url, {'contact_email': 'invalid-email'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('contact_email', response.json())
        
    def test_update_school_invalid_url(self):
        """Test validation for URL field"""
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-detail', kwargs={'pk': self.school.id})
        
        response = self.client.patch(url, {'website': 'not-a-url'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('website', response.json())
        
    def test_update_school_creates_activity(self):
        """Test that updating school creates an activity log"""
        from accounts.models import SchoolActivity, ActivityType
        
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-detail', kwargs={'pk': self.school.id})
        
        response = self.client.patch(url, {'name': 'Activity Test School'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check activity was created
        activity = SchoolActivity.objects.filter(
            school=self.school,
            actor=self.school_owner
        ).first()
        
        self.assertIsNotNone(activity)
        self.assertIn('updated school', activity.description.lower())


class SecurityFixesTest(TestCase):
    """Test cases for critical security fixes"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test users
        self.school_owner = CustomUser.objects.create_user(
            email='owner@test.com',
            name='School Owner'
        )
        self.unauthorized_user = CustomUser.objects.create_user(
            email='unauthorized@test.com',
            name='Unauthorized User'
        )
        
        # Create test school
        self.school = School.objects.create(
            name='Test School',
            description='A test school'
        )
        
        # Get or create educational system
        self.educational_system, _ = EducationalSystem.objects.get_or_create(
            code='custom',
            defaults={'name': 'Test System'}
        )
        
        # Add owner membership
        SchoolMembership.objects.create(
            user=self.school_owner,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )
    
    def test_activity_type_fix_settings_updated(self):
        """Test Fix #1: Correct ActivityType.SETTINGS_UPDATED is used for school updates"""
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-detail', kwargs={'pk': self.school.id})
        
        # Clear any existing activities
        SchoolActivity.objects.filter(school=self.school).delete()
        
        # Verify no activities exist before update
        self.assertEqual(SchoolActivity.objects.filter(school=self.school).count(), 0)
        
        # Update school settings
        response = self.client.patch(url, {'name': 'Updated School Name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that correct ActivityType was used
        activity = SchoolActivity.objects.filter(
            school=self.school,
            actor=self.school_owner
        ).first()
        
        self.assertIsNotNone(activity, "No activity was created for school update")
        self.assertEqual(activity.activity_type, ActivityType.SETTINGS_UPDATED)
        self.assertNotEqual(activity.activity_type, ActivityType.STUDENT_JOINED)
    
    def test_permission_class_authentication(self):
        """Test Fix #2: IsSchoolOwnerOrAdmin permission is properly enforced"""
        url = reverse('accounts:school-dashboard-metrics', kwargs={'pk': self.school.id})
        
        # Test unauthenticated access
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test unauthorized user access
        self.client.force_authenticate(user=self.unauthorized_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test authorized user access
        self.client.force_authenticate(user=self.school_owner)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_pagination_parameter_validation(self):
        """Test Fix #3: Proper validation prevents SQL injection in pagination"""
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-activity', kwargs={'pk': self.school.id})
        
        # Test invalid page parameter
        response = self.client.get(url, {'page': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid page parameter', response.json()['error'])
        
        # Test invalid page_size parameter
        response = self.client.get(url, {'page_size': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid page_size parameter', response.json()['error'])
        
        # Test negative page parameter
        response = self.client.get(url, {'page': '-1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Should default to 1
        
        # Test excessive page_size parameter
        response = self.client.get(url, {'page_size': '1000'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Should cap at 100
        
        # Test valid parameters
        response = self.client.get(url, {'page': '1', 'page_size': '10'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_monthly_calculation_accuracy(self):
        """Test Fix #4: Accurate monthly calculations using proper calendar arithmetic"""
        from accounts.services.metrics_service import SchoolMetricsService
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        # Create test memberships at different months
        now = datetime.now()
        
        # Create memberships for the last 3 months
        for i in range(3):
            month_date = now - relativedelta(months=i)
            CustomUser.objects.create_user(
                email=f'student{i}@test.com',
                name=f'Student {i}'
            )
            user = CustomUser.objects.get(email=f'student{i}@test.com')
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.STUDENT,
                is_active=True,
                joined_at=month_date
            )
        
        # Test that metrics service uses proper calendar arithmetic
        metrics_service = SchoolMetricsService(self.school)
        trends = metrics_service._calculate_membership_trends(SchoolRole.STUDENT)
        
        # Should have monthly data
        self.assertIn('monthly', trends)
        self.assertEqual(len(trends['monthly']), 6)  # Last 6 months
    
    @patch('accounts.signals.logger')
    def test_websocket_error_handling(self, mock_logger):
        """Test Fix #5: Proper error logging for WebSocket failures"""
        from accounts.signals import invalidate_metrics_cache_on_activity
        from unittest.mock import patch
        
        # Create an activity
        activity = SchoolActivity.objects.create(
            school=self.school,
            activity_type=ActivityType.SETTINGS_UPDATED,
            actor=self.school_owner,
            description='Test activity'
        )
        
        # Mock WebSocket broadcaster to raise exception
        with patch('asgiref.sync.async_to_sync') as mock_async_to_sync:
            mock_async_to_sync.side_effect = Exception('WebSocket connection failed')
            
            # Call the signal handler directly
            invalidate_metrics_cache_on_activity(sender=SchoolActivity, instance=activity, created=True)
            
            # Verify error was logged (may be called multiple times due to real Redis failures + our mock)
            self.assertTrue(mock_logger.error.called)
            
            # Check that at least one call was our mocked WebSocket failure
            calls = mock_logger.error.call_args_list
            mock_call_found = False
            for call in calls:
                if 'WebSocket connection failed' in call[0][0]:
                    mock_call_found = True
                    extra = call[1]['extra']
                    self.assertEqual(extra['school_id'], self.school.id)
                    self.assertEqual(extra['activity_id'], activity.id)
                    self.assertEqual(extra['activity_type'], ActivityType.SETTINGS_UPDATED)
                    break
            
            self.assertTrue(mock_call_found, "Expected mocked WebSocket failure log not found")
    
    def test_all_activity_types_exist(self):
        """Test that all expected ActivityType choices exist including SETTINGS_UPDATED"""
        expected_types = [
            ActivityType.INVITATION_SENT,
            ActivityType.INVITATION_ACCEPTED,
            ActivityType.INVITATION_DECLINED,
            ActivityType.STUDENT_JOINED,
            ActivityType.TEACHER_JOINED,
            ActivityType.CLASS_CREATED,
            ActivityType.CLASS_COMPLETED,
            ActivityType.CLASS_CANCELLED,
            ActivityType.SETTINGS_UPDATED,  # New type added for security fix
        ]
        
        for activity_type in expected_types:
            self.assertIn(activity_type, ActivityType.values)
    
    def test_pagination_boundary_conditions(self):
        """Test edge cases for pagination parameter validation"""
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-activity', kwargs={'pk': self.school.id})
        
        # Test minimum valid values
        response = self.client.get(url, {'page': '1', 'page_size': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test maximum page_size
        response = self.client.get(url, {'page': '1', 'page_size': '100'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test zero values (should be corrected to defaults)
        response = self.client.get(url, {'page': '0', 'page_size': '0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Zero gets corrected to 1 and 20
        
        # Test empty string values are handled gracefully (uses defaults when not provided)
        response = self.client.get(url)  # No parameters at all uses defaults
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_settings_activity_metadata(self):
        """Test that settings update activity includes proper metadata"""
        self.client.force_authenticate(user=self.school_owner)
        url = reverse('accounts:school-dashboard-detail', kwargs={'pk': self.school.id})
        
        # Clear existing activities
        SchoolActivity.objects.filter(school=self.school).delete()
        
        # Update multiple fields
        response = self.client.patch(url, {
            'name': 'New School Name',
            'description': 'New description'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check activity metadata
        activity = SchoolActivity.objects.filter(
            school=self.school,
            activity_type=ActivityType.SETTINGS_UPDATED
        ).first()
        
        self.assertIsNotNone(activity, "No activity was created for school settings update")
        # Check that the description includes the changes
        self.assertIn('Updated school:', activity.description)
        self.assertIn('New School Name', activity.description)
        self.assertIn('New description', activity.description)