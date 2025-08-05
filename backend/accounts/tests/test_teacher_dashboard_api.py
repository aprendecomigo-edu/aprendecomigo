"""
Tests for Teacher Dashboard API endpoints.

Following TDD approach - comprehensive tests for consolidated teacher dashboard.
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import datetime, timedelta, date, time

from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolRole, 
    TeacherProfile, StudentProfile, Course, EducationalSystem,
    StudentProgress, ProgressAssessment
)
from accounts.tests.test_base import BaseTestCase
from finances.models import ClassSession, SessionStatus, SessionType, TeacherPaymentEntry
from knox.models import AuthToken


class TeacherDashboardAPITest(BaseTestCase, APITestCase):
    """Test suite for Teacher Dashboard API functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Clear cache to ensure clean test isolation
        from django.core.cache import cache
        cache.clear()
        
        # Use the default educational system from base class
        self.educational_system = self.default_educational_system
        
        # Create school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )
        
        # Create teacher user and profile
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com",
            name="Teacher Test",
            password="testpass123"
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Test teacher bio",
            specialty="Mathematics",
            hourly_rate=Decimal("25.00")
        )
        
        # Create teacher school membership
        self.teacher_membership = SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        # Create students
        self.student1 = CustomUser.objects.create_user(
            email="student1@test.com",
            name="Student One",
            password="testpass123"
        )
        self.student2 = CustomUser.objects.create_user(
            email="student2@test.com",
            name="Student Two",
            password="testpass123"
        )
        
        # Create student profiles
        self.student1_profile = StudentProfile.objects.create(
            user=self.student1,
            educational_system=self.educational_system,
            school_year="7",
            birth_date="2010-01-01"
        )
        self.student2_profile = StudentProfile.objects.create(
            user=self.student2,
            educational_system=self.educational_system,
            school_year="8",
            birth_date="2009-01-01"
        )
        
        # Create student school memberships
        SchoolMembership.objects.create(
            user=self.student1,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        SchoolMembership.objects.create(
            user=self.student2,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        
        # Create course
        self.course = Course.objects.create(
            name="Mathematics Grade 7",
            code="MATH7",
            educational_system=self.educational_system,
            education_level="ensino_basico_3_ciclo"
        )
        
        # Create student progress records
        self.progress1 = StudentProgress.objects.create(
            student=self.student1,
            teacher=self.teacher_profile,
            school=self.school,
            course=self.course,
            current_level="intermediate",
            completion_percentage=Decimal("75.50"),
            skills_mastered=["algebra", "geometry"],
            notes="Excellent progress in algebra"
        )
        
        self.progress2 = StudentProgress.objects.create(
            student=self.student2,
            teacher=self.teacher_profile,
            school=self.school,
            course=self.course,
            current_level="beginner",
            completion_percentage=Decimal("45.00"),
            skills_mastered=["basic_arithmetic"],
            notes="Needs more practice with fractions"
        )
        
        # Create some assessments
        ProgressAssessment.objects.create(
            student_progress=self.progress1,
            assessment_type="quiz",
            title="Algebra Quiz 1",
            score=Decimal("18.5"),
            max_score=Decimal("20.0"),
            assessment_date=timezone.now().date(),
            skills_assessed=["linear_equations"],
            teacher_notes="Great work on linear equations"
        )
        
        ProgressAssessment.objects.create(
            student_progress=self.progress2,
            assessment_type="homework",
            title="Fractions Homework",
            score=Decimal("7.0"),
            max_score=Decimal("10.0"),
            assessment_date=timezone.now().date() - timedelta(days=1),
            skills_assessed=["fractions"],
            teacher_notes="Keep practicing fractions"
        )
        
        # Create class sessions
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        # Completed session from yesterday
        self.completed_session = ClassSession.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=yesterday,
            start_time=time(14, 0),
            end_time=time(15, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="7",
            student_count=1,
            status=SessionStatus.COMPLETED,
            notes="Good session on algebra"
        )
        self.completed_session.students.add(self.student1)
        
        # Scheduled session for today
        self.today_session = ClassSession.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=today,
            start_time=time(15, 0),
            end_time=time(16, 0),
            session_type=SessionType.INDIVIDUAL,
            grade_level="8",
            student_count=1,
            status=SessionStatus.SCHEDULED
        )
        self.today_session.students.add(self.student2)
        
        # Scheduled session for tomorrow
        self.future_session = ClassSession.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=tomorrow,
            start_time=time(16, 0),
            end_time=time(17, 0),
            session_type=SessionType.GROUP,
            grade_level="7",
            student_count=2,
            status=SessionStatus.SCHEDULED
        )
        self.future_session.students.add(self.student1, self.student2)
        
        # Create payment entry for completed session
        TeacherPaymentEntry.objects.create(
            session=self.completed_session,
            teacher=self.teacher_profile,
            school=self.school,
            billing_period="2025-01",
            hours_taught=Decimal("1.0"),
            rate_applied=Decimal("25.00"),
            amount_earned=Decimal("25.00")
        )
        
        # Authenticate as teacher
        self.auth_token = AuthToken.objects.create(user=self.teacher_user)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.auth_token}')
    
    def test_consolidated_dashboard_endpoint_exists(self):
        """Test that the consolidated dashboard endpoint exists and is accessible."""
        url = '/api/accounts/teachers/consolidated_dashboard/'
        response = self.client.get(url)
        
        # Should not return 404
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Should return 200 for authenticated teacher
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_consolidated_dashboard_returns_all_required_data(self):
        """Test that dashboard returns all required consolidated data."""
        url = '/api/accounts/teachers/consolidated_dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check top-level structure
        required_keys = [
            'teacher_info',
            'students',
            'sessions',
            'progress_metrics',
            'recent_activities',
            'earnings',
            'quick_stats'
        ]
        
        for key in required_keys:
            self.assertIn(key, data, f"Missing required key: {key}")
    
    def test_dashboard_teacher_info_structure(self):
        """Test the teacher_info section of dashboard response."""
        url = '/api/accounts/teachers/consolidated_dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        teacher_info = response.json()['teacher_info']
        
        expected_fields = [
            'id', 'name', 'email', 'specialty', 'hourly_rate',
            'profile_completion_score', 'schools', 'courses_taught'
        ]
        
        for field in expected_fields:
            self.assertIn(field, teacher_info, f"Missing teacher_info field: {field}")
        
        # Verify data accuracy
        self.assertEqual(teacher_info['name'], self.teacher_user.name)
        self.assertEqual(teacher_info['email'], self.teacher_user.email)
        self.assertEqual(teacher_info['specialty'], self.teacher_profile.specialty)
        self.assertEqual(float(teacher_info['hourly_rate']), float(self.teacher_profile.hourly_rate))
    
    def test_dashboard_students_data(self):
        """Test the students section with progress data."""
        url = '/api/accounts/teachers/consolidated_dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        students = response.json()['students']
        
        self.assertEqual(len(students), 2)
        
        # Check student data structure
        student_data = students[0]
        expected_fields = [
            'id', 'name', 'email', 'current_level', 'completion_percentage',
            'last_session_date', 'recent_assessments', 'skills_mastered'
        ]
        
        for field in expected_fields:
            self.assertIn(field, student_data, f"Missing student field: {field}")
    
    def test_dashboard_sessions_data(self):
        """Test the sessions section with comprehensive session data."""
        url = '/api/accounts/teachers/consolidated_dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sessions_data = response.json()['sessions']
        
        # Should have sections for different session types
        expected_sections = ['today', 'upcoming', 'recent_completed']
        for section in expected_sections:
            self.assertIn(section, sessions_data)
        
        # Check today's sessions
        today_sessions = sessions_data['today']
        self.assertEqual(len(today_sessions), 1)
        
        session = today_sessions[0]
        expected_fields = [
            'id', 'date', 'start_time', 'end_time', 'session_type',
            'student_names', 'status', 'notes'
        ]
        
        for field in expected_fields:
            self.assertIn(field, session, f"Missing session field: {field}")
    
    def test_dashboard_progress_metrics(self):
        """Test the progress_metrics section."""
        url = '/api/accounts/teachers/consolidated_dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        metrics = response.json()['progress_metrics']
        
        expected_metrics = [
            'average_student_progress',
            'total_assessments_given',
            'students_improved_this_month',
            'completion_rate_trend'
        ]
        
        for metric in expected_metrics:
            self.assertIn(metric, metrics, f"Missing progress metric: {metric}")
        
        # Verify calculated values
        self.assertGreater(metrics['average_student_progress'], 0)
        self.assertGreater(metrics['total_assessments_given'], 0)
    
    def test_dashboard_earnings_data(self):
        """Test the earnings section."""
        url = '/api/accounts/teachers/consolidated_dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        earnings = response.json()['earnings']
        
        expected_fields = [
            'current_month_total',
            'last_month_total',
            'pending_amount',
            'total_hours_taught',
            'recent_payments'
        ]
        
        for field in expected_fields:
            self.assertIn(field, earnings, f"Missing earnings field: {field}")
    
    def test_dashboard_quick_stats(self):
        """Test the quick_stats section."""
        url = '/api/accounts/teachers/consolidated_dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.json()['quick_stats']
        
        expected_stats = [
            'total_students',
            'sessions_today',
            'sessions_this_week',
            'completion_rate',
            'average_rating'
        ]
        
        for stat in expected_stats:
            self.assertIn(stat, stats, f"Missing quick stat: {stat}")
        
        # Verify accuracy
        self.assertEqual(stats['total_students'], 2)
        self.assertEqual(stats['sessions_today'], 1)
    
    def test_dashboard_performance_response_time(self):
        """Test that dashboard responds within performance requirements (<500ms)."""
        import time
        
        url = '/api/accounts/teachers/consolidated_dashboard/'
        
        start_time = time.time()
        response = self.client.get(url)
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 500, f"Response time {response_time}ms exceeds 500ms requirement")
    
    def test_dashboard_unauthorized_access(self):
        """Test that unauthorized users cannot access dashboard."""
        # Remove authentication
        self.client.credentials()
        
        url = '/api/accounts/teachers/consolidated_dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_dashboard_non_teacher_access(self):
        """Test that non-teacher users cannot access teacher dashboard."""
        # Create and authenticate as student
        student_user = CustomUser.objects.create_user(
            email="onlystudent@test.com",
            name="Only Student",
            password="testpass123"
        )
        SchoolMembership.objects.create(
            user=student_user,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        
        student_token = AuthToken.objects.create(user=student_user)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {student_token}')
        
        url = '/api/accounts/teachers/consolidated_dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_dashboard_caching_headers(self):
        """Test that appropriate caching headers are set."""
        url = '/api/accounts/teachers/consolidated_dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have cache control headers for optimization
        self.assertIn('Cache-Control', response.headers)
    
    def test_dashboard_with_no_data(self):
        """Test dashboard response when teacher has no students/sessions."""
        # Create teacher with no associated data
        empty_teacher = CustomUser.objects.create_user(
            email="empty@test.com",
            name="Empty Teacher",
            password="testpass123"
        )
        empty_teacher_profile = TeacherProfile.objects.create(
            user=empty_teacher,
            bio="Empty teacher"
        )
        SchoolMembership.objects.create(
            user=empty_teacher,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        empty_token = AuthToken.objects.create(user=empty_teacher)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {empty_token}')
        
        url = '/api/accounts/teachers/consolidated_dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should still return proper structure with empty/zero values
        self.assertEqual(len(data['students']), 0)
        self.assertEqual(data['quick_stats']['total_students'], 0)
        self.assertEqual(data['quick_stats']['sessions_today'], 0)
    
    def test_dashboard_query_optimization(self):
        """Test that dashboard uses optimized queries."""
        from django.test.utils import override_settings
        from django.db import connection
        
        url = '/api/accounts/teachers/consolidated_dashboard/'
        
        with override_settings(DEBUG=True):
            # Reset query log
            connection.queries_log.clear()
            
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Should use efficient queries (reasonable for a comprehensive dashboard)
            query_count = len(connection.queries)
            self.assertLess(query_count, 40, f"Too many queries: {query_count}. Check for N+1 problems.")
            # Verify we're within acceptable range for a multi-section dashboard
            self.assertGreater(query_count, 10, "Dashboard should be comprehensive with multiple data sections")


class TeacherDashboardPermissionsTest(APITestCase):
    """Test permissions and security for teacher dashboard."""
    
    def setUp(self):
        """Set up test data for permissions testing."""
        # Clear cache to ensure clean test isolation
        from django.core.cache import cache
        cache.clear()
        
        # Create multiple schools and teachers
        self.school1 = School.objects.create(name="School 1")
        self.school2 = School.objects.create(name="School 2")
        
        # Teacher 1 in School 1
        self.teacher1 = CustomUser.objects.create_user(
            email="teacher1@test.com",
            name="Teacher One"
        )
        self.teacher1_profile = TeacherProfile.objects.create(user=self.teacher1)
        SchoolMembership.objects.create(
            user=self.teacher1,
            school=self.school1,
            role=SchoolRole.TEACHER
        )
        
        # Teacher 2 in School 2
        self.teacher2 = CustomUser.objects.create_user(
            email="teacher2@test.com",
            name="Teacher Two"
        )
        self.teacher2_profile = TeacherProfile.objects.create(user=self.teacher2)
        SchoolMembership.objects.create(
            user=self.teacher2,
            school=self.school2,
            role=SchoolRole.TEACHER
        )
    
    def test_teacher_can_only_see_own_dashboard(self):
        """Test that teachers can only access their own dashboard data."""
        # Authenticate as teacher1
        token1 = AuthToken.objects.create(user=self.teacher1)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token1}')
        
        url = '/api/accounts/teachers/consolidated_dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify it's teacher1's data
        self.assertEqual(data['teacher_info']['id'], self.teacher1_profile.id)
        self.assertEqual(data['teacher_info']['name'], self.teacher1.name)
    
    def test_teacher_cannot_access_other_teacher_data(self):
        """Test that URL parameter manipulation doesn't allow access to other teachers' data."""
        # This would be relevant if we had endpoints like /teachers/{id}/dashboard/
        # For now, the consolidated dashboard is always for the authenticated teacher
        pass