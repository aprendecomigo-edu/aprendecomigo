"""
Test suite for School Activity models following TDD methodology.
These tests are written before the implementation to ensure proper functionality.
"""
import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolRole, 
    SchoolInvitation, EducationalSystem
)
from finances.models import ClassSession


class SchoolActivityModelTest(TestCase):
    """Test cases for SchoolActivity model"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.admin_user = CustomUser.objects.create_user(
            email='admin@test.com',
            name='Admin User'
        )
        self.teacher_user = CustomUser.objects.create_user(
            email='teacher@test.com',
            name='Teacher User'
        )
        self.student_user = CustomUser.objects.create_user(
            email='student@test.com',
            name='Student User'
        )
        
        # Create test school
        self.school = School.objects.create(
            name='Test School',
            description='A test school'
        )
        
        # Create school memberships
        self.admin_membership = SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
        
    def test_create_school_activity_invitation_sent(self):
        """Test creating an invitation sent activity"""
        from accounts.models import SchoolActivity, ActivityType
        
        activity = SchoolActivity.objects.create(
            school=self.school,
            activity_type=ActivityType.INVITATION_SENT,
            actor=self.admin_user,
            description="Admin User invited teacher@test.com as a teacher",
            metadata={
                'email': 'teacher@test.com',
                'role': 'teacher'
            }
        )
        
        self.assertEqual(activity.school, self.school)
        self.assertEqual(activity.activity_type, ActivityType.INVITATION_SENT)
        self.assertEqual(activity.actor, self.admin_user)
        self.assertIsNotNone(activity.id)
        self.assertIsInstance(activity.id, uuid.UUID)
        self.assertIsNotNone(activity.timestamp)
        
    def test_create_school_activity_student_joined(self):
        """Test creating a student joined activity"""
        from accounts.models import SchoolActivity, ActivityType
        
        activity = SchoolActivity.objects.create(
            school=self.school,
            activity_type=ActivityType.STUDENT_JOINED,
            actor=self.student_user,
            target_user=self.student_user,
            description="Student User joined as a student"
        )
        
        self.assertEqual(activity.activity_type, ActivityType.STUDENT_JOINED)
        self.assertEqual(activity.target_user, self.student_user)
        
    def test_create_school_activity_class_completed(self):
        """Test creating a class completed activity"""
        from accounts.models import SchoolActivity, ActivityType, TeacherProfile
        from finances.models import ClassSession
        
        # Create a teacher profile for the teacher user
        teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio='Test teacher bio'
        )
        
        # Create a test class session  
        class_session = ClassSession.objects.create(
            school=self.school,
            teacher=teacher_profile,
            date=timezone.now().date(),
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=1)).time(),
            session_type='individual',
            grade_level='7',
            status='completed'
        )
        
        activity = SchoolActivity.objects.create(
            school=self.school,
            activity_type=ActivityType.CLASS_COMPLETED,
            actor=self.teacher_user,
            target_class=class_session,
            description="Grade 7 class completed",
            metadata={
                'duration': '60 minutes',
                'grade_level': '7'
            }
        )
        
        self.assertEqual(activity.target_class, class_session)
        self.assertEqual(activity.metadata['grade_level'], '7')
        
    def test_school_activity_ordering(self):
        """Test that activities are ordered by timestamp descending"""
        from accounts.models import SchoolActivity, ActivityType
        
        # Create activities with slight time differences
        activity1 = SchoolActivity.objects.create(
            school=self.school,
            activity_type=ActivityType.STUDENT_JOINED,
            actor=self.student_user,
            description="First activity"
        )
        
        # Wait a moment
        activity2 = SchoolActivity.objects.create(
            school=self.school,
            activity_type=ActivityType.TEACHER_JOINED,
            actor=self.teacher_user,
            description="Second activity"
        )
        
        activities = SchoolActivity.objects.filter(school=self.school)
        # Most recent should be first
        self.assertEqual(activities[0].id, activity2.id)
        self.assertEqual(activities[1].id, activity1.id)
        
    def test_school_activity_indexes(self):
        """Test that proper indexes exist on SchoolActivity"""
        from accounts.models import SchoolActivity
        
        # Get model indexes
        indexes = SchoolActivity._meta.indexes
        index_fields = [index.fields for index in indexes]
        
        # Check required indexes exist
        self.assertIn(['school', '-timestamp'], index_fields)
        self.assertIn(['school', 'activity_type', '-timestamp'], index_fields)
        self.assertIn(['actor', '-timestamp'], index_fields)
        
    def test_activity_type_choices(self):
        """Test all required activity types exist"""
        from accounts.models import ActivityType
        
        expected_types = [
            'invitation_sent',
            'invitation_accepted',
            'invitation_declined',
            'student_joined',
            'teacher_joined',
            'class_created',
            'class_completed',
            'class_cancelled'
        ]
        
        actual_types = [choice[0] for choice in ActivityType.choices]
        
        for expected in expected_types:
            self.assertIn(expected, actual_types)


class SchoolSettingsModelTest(TestCase):
    """Test cases for SchoolSettings model extension"""
    
    def setUp(self):
        """Set up test data"""
        self.school = School.objects.create(
            name='Test School',
            description='A test school'
        )
        
    def test_create_school_settings(self):
        """Test creating school settings"""
        from accounts.models import SchoolSettings, TrialCostAbsorption
        
        settings = SchoolSettings.objects.create(
            school=self.school,
            trial_cost_absorption=TrialCostAbsorption.SCHOOL,
            default_session_duration=60,
            timezone='Europe/Lisbon'
        )
        
        self.assertEqual(settings.school, self.school)
        self.assertEqual(settings.trial_cost_absorption, TrialCostAbsorption.SCHOOL)
        self.assertEqual(settings.default_session_duration, 60)
        self.assertEqual(settings.timezone, 'Europe/Lisbon')
        
    def test_school_settings_defaults(self):
        """Test default values for school settings"""
        from accounts.models import SchoolSettings, TrialCostAbsorption
        
        settings = SchoolSettings.objects.create(school=self.school)
        
        self.assertEqual(settings.trial_cost_absorption, TrialCostAbsorption.SCHOOL)
        self.assertEqual(settings.default_session_duration, 60)
        self.assertEqual(settings.timezone, 'UTC')
        self.assertEqual(settings.dashboard_refresh_interval, 30)
        self.assertEqual(settings.activity_retention_days, 90)
        
    def test_school_settings_one_to_one(self):
        """Test that school can have only one settings object"""
        from accounts.models import SchoolSettings
        
        settings1 = SchoolSettings.objects.create(school=self.school)
        
        # Try to create another settings for the same school
        with self.assertRaises(IntegrityError):
            SchoolSettings.objects.create(school=self.school)
            
    def test_trial_cost_absorption_choices(self):
        """Test trial cost absorption choices"""
        from accounts.models import TrialCostAbsorption
        
        expected_choices = ['school', 'teacher', 'split']
        actual_choices = [choice[0] for choice in TrialCostAbsorption.choices]
        
        for expected in expected_choices:
            self.assertIn(expected, actual_choices)


class SchoolMembershipIndexesTest(TestCase):
    """Test cases for SchoolMembership model indexes"""
    
    def test_school_membership_indexes(self):
        """Test that proper indexes exist on SchoolMembership"""
        from accounts.models import SchoolMembership
        
        # Get model indexes
        indexes = SchoolMembership._meta.indexes
        index_fields = [index.fields for index in indexes]
        
        # Check required indexes exist
        self.assertIn(['school', 'role', 'is_active'], index_fields)
        self.assertIn(['school', 'joined_at'], index_fields)