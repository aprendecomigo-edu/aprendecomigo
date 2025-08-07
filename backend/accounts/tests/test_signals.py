"""
Test suite for Django signals that automatically create school activities.
"""
from django.test import TestCase
from django.utils import timezone
from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolInvitation, 
    SchoolActivity, ActivityType, SchoolRole, TeacherProfile
)
from finances.models import ClassSession


class SchoolActivitySignalsTest(TestCase):
    """Test cases for automatic activity creation via signals"""
    
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
        
        # Create admin membership (won't trigger activity)
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
        
    def test_student_membership_creates_activity(self):
        """Test that student membership creation triggers activity logging business rule."""
        initial_count = SchoolActivity.objects.count()
        
        # Create student membership - should trigger signal
        SchoolMembership.objects.create(
            user=self.student_user,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        
        # Verify activity logging business rule was applied
        self.assertEqual(SchoolActivity.objects.count(), initial_count + 1)
        
        activity = SchoolActivity.objects.latest('timestamp')
        self.assertEqual(activity.activity_type, ActivityType.STUDENT_JOINED)
        self.assertEqual(activity.actor, self.student_user)
        self.assertEqual(activity.target_user, self.student_user)
        self.assertEqual(activity.school, self.school)
        self.assertIn('Student User joined as a student', activity.description)
        
    def test_teacher_membership_creates_activity(self):
        """Test that teacher onboarding triggers activity logging business rule."""
        initial_count = SchoolActivity.objects.count()
        
        # Create teacher membership - should trigger activity signal
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        # Verify teacher onboarding activity was logged
        self.assertEqual(SchoolActivity.objects.count(), initial_count + 1)
        
        activity = SchoolActivity.objects.latest('timestamp')
        self.assertEqual(activity.activity_type, ActivityType.TEACHER_JOINED)
        self.assertEqual(activity.actor, self.teacher_user)
        self.assertEqual(activity.target_user, self.teacher_user)
        self.assertIn('Teacher User joined as a teacher', activity.description)
        
    def test_invitation_sent_creates_activity(self):
        """Test that sending invitation triggers activity"""
        initial_count = SchoolActivity.objects.count()
        
        # Create invitation
        invitation = SchoolInvitation.objects.create(
            school=self.school,
            email='newteacher@test.com',
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            token='test-token',
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        # Check activity was created
        self.assertEqual(SchoolActivity.objects.count(), initial_count + 1)
        
        activity = SchoolActivity.objects.latest('timestamp')
        self.assertEqual(activity.activity_type, ActivityType.INVITATION_SENT)
        self.assertEqual(activity.actor, self.admin_user)
        self.assertEqual(activity.target_invitation, invitation)
        self.assertIn('invited newteacher@test.com', activity.description)
        
    def test_invitation_accepted_creates_activity(self):
        """Test that accepting invitation triggers activity"""
        # First create and accept invitation
        invitation = SchoolInvitation.objects.create(
            school=self.school,
            email='newteacher@test.com',
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            token='test-token',
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        initial_count = SchoolActivity.objects.count()
        
        # Accept the invitation (this triggers the signal)
        invitation.is_accepted = True
        invitation.save()
        
        # Check activity was created (should be 2: sent + accepted)
        activities = SchoolActivity.objects.order_by('timestamp')
        self.assertEqual(activities.count(), initial_count + 1)
        
        # Check the acceptance activity
        activity = activities.last()
        self.assertEqual(activity.activity_type, ActivityType.INVITATION_ACCEPTED)
        self.assertEqual(activity.target_invitation, invitation)
        self.assertIn('accepted invitation', activity.description)
        
    def test_class_session_created_creates_activity(self):
        """Test that creating class session triggers activity"""
        # Create teacher profile first
        teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio='Test teacher bio'
        )
        
        initial_count = SchoolActivity.objects.count()
        
        # Create class session
        class_session = ClassSession.objects.create(
            school=self.school,
            teacher=teacher_profile,
            date='2024-01-15',
            start_time='10:00:00',
            end_time='11:00:00',
            session_type='individual',
            grade_level='7',
            status='scheduled'
        )
        
        # Check activity was created
        self.assertEqual(SchoolActivity.objects.count(), initial_count + 1)
        
        activity = SchoolActivity.objects.latest('timestamp')
        self.assertEqual(activity.activity_type, ActivityType.CLASS_CREATED)
        self.assertEqual(activity.actor, self.teacher_user)
        self.assertEqual(activity.target_class, class_session)
        self.assertIn('Grade 7 class scheduled', activity.description)
        
    def test_class_session_completed_creates_activity(self):
        """Test that completing class session triggers activity"""
        # Create teacher profile and class session
        teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio='Test teacher bio'
        )
        
        class_session = ClassSession.objects.create(
            school=self.school,
            teacher=teacher_profile,
            date='2024-01-15',
            start_time='10:00:00',
            end_time='11:00:00',
            session_type='individual',
            grade_level='7',
            status='scheduled'
        )
        
        initial_count = SchoolActivity.objects.count()
        
        # Complete the session
        class_session.status = 'completed'
        class_session.save()
        
        # Check completion activity was created
        self.assertEqual(SchoolActivity.objects.count(), initial_count + 1)
        
        activity = SchoolActivity.objects.latest('timestamp')
        self.assertEqual(activity.activity_type, ActivityType.CLASS_COMPLETED)
        self.assertEqual(activity.actor, self.teacher_user)
        self.assertEqual(activity.target_class, class_session)
        self.assertIn('Grade 7 class completed', activity.description)
        
    def test_inactive_membership_does_not_create_activity(self):
        """Test that inactive memberships do not trigger activity logging (business rule)."""
        initial_count = SchoolActivity.objects.count()
        
        # Create inactive membership - should not trigger activity signal
        SchoolMembership.objects.create(
            user=self.student_user,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=False
        )
        
        # Verify business rule: only active memberships create activities
        self.assertEqual(SchoolActivity.objects.count(), initial_count)
        
    def test_admin_membership_does_not_create_activity(self):
        """Test that admin/owner memberships do not trigger activities (business rule)."""
        initial_count = SchoolActivity.objects.count()
        
        # Create admin membership - should not trigger activity signal
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN
        )
        
        # Verify business rule: admin roles don't create join activities
        self.assertEqual(SchoolActivity.objects.count(), initial_count)