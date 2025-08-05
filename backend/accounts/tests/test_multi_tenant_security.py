"""
Multi-Tenant Data Isolation Security Tests for Aprende Comigo Platform

These tests verify that data is properly isolated between different schools
and that users cannot access data from schools they don't belong to.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import (
    CustomUser,
    School,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
    TeacherProfile,
    TeacherInvitation,
    SchoolInvitation,
    ParentChildRelationship,
    SchoolActivity,
    SchoolSettings,
)
from finances.models import ClassSession, PurchaseTransaction
from tasks.models import Task

User = get_user_model()


class MultiTenantDataIsolationTestCase(TestCase):
    """
    Test suite for verifying strict data isolation between schools.
    
    Each test verifies that users from one school cannot access data
    from another school through API endpoints or direct database access.
    """

    def setUp(self):
        """Set up test data with multiple schools and users."""
        # Create two separate schools
        self.school_a = School.objects.create(
            name="School A",
            description="Test School A",
            contact_email="admin@schoola.com"
        )
        self.school_b = School.objects.create(
            name="School B", 
            description="Test School B",
            contact_email="admin@schoolb.com"
        )
        
        # School A users
        self.owner_school_a = CustomUser.objects.create_user(
            email="owner.a@example.com",
            username="owner_a",
            first_name="Owner",
            last_name="A"
        )
        self.teacher_school_a = CustomUser.objects.create_user(
            email="teacher.a@example.com",
            username="teacher_a", 
            first_name="Teacher",
            last_name="A"
        )
        self.student_school_a = CustomUser.objects.create_user(
            email="student.a@example.com",
            username="student_a",
            first_name="Student", 
            last_name="A"
        )
        self.parent_school_a = CustomUser.objects.create_user(
            email="parent.a@example.com",
            username="parent_a",
            first_name="Parent",
            last_name="A"
        )
        
        # School B users
        self.owner_school_b = CustomUser.objects.create_user(
            email="owner.b@example.com", 
            username="owner_b",
            first_name="Owner",
            last_name="B"
        )
        self.teacher_school_b = CustomUser.objects.create_user(
            email="teacher.b@example.com",
            username="teacher_b",
            first_name="Teacher", 
            last_name="B"
        )
        self.student_school_b = CustomUser.objects.create_user(
            email="student.b@example.com",
            username="student_b",
            first_name="Student",
            last_name="B"
        )
        self.parent_school_b = CustomUser.objects.create_user(
            email="parent.b@example.com",
            username="parent_b", 
            first_name="Parent",
            last_name="B"
        )
        
        # Create school memberships for School A
        SchoolMembership.objects.create(
            user=self.owner_school_a, 
            school=self.school_a,
            role=SchoolRole.SCHOOL_OWNER
        )
        SchoolMembership.objects.create(
            user=self.teacher_school_a,
            school=self.school_a, 
            role=SchoolRole.TEACHER
        )
        SchoolMembership.objects.create(
            user=self.student_school_a,
            school=self.school_a,
            role=SchoolRole.STUDENT
        )
        SchoolMembership.objects.create(
            user=self.parent_school_a,
            school=self.school_a, 
            role=SchoolRole.PARENT
        )
        
        # Create school memberships for School B  
        SchoolMembership.objects.create(
            user=self.owner_school_b,
            school=self.school_b,
            role=SchoolRole.SCHOOL_OWNER
        )
        SchoolMembership.objects.create(
            user=self.teacher_school_b,
            school=self.school_b,
            role=SchoolRole.TEACHER
        )
        SchoolMembership.objects.create(
            user=self.student_school_b, 
            school=self.school_b,
            role=SchoolRole.STUDENT
        )
        SchoolMembership.objects.create(
            user=self.parent_school_b,
            school=self.school_b,
            role=SchoolRole.PARENT
        )
        
        # Create profiles
        self.teacher_profile_a = TeacherProfile.objects.create(
            user=self.teacher_school_a,
            bio="Teacher A profile",
            hourly_rate=25.00
        )
        self.teacher_profile_b = TeacherProfile.objects.create(
            user=self.teacher_school_b,
            bio="Teacher B profile", 
            hourly_rate=30.00
        )
        
        self.student_profile_a = StudentProfile.objects.create(
            user=self.student_school_a,
            birth_date="2010-01-01",
            school_year="5th Grade"
        )
        self.student_profile_b = StudentProfile.objects.create(
            user=self.student_school_b,
            birth_date="2011-01-01", 
            school_year="4th Grade"
        )
        
        # Create parent-child relationships within schools
        ParentChildRelationship.objects.create(
            parent=self.parent_school_a,
            child=self.student_school_a,
            school=self.school_a
        )
        ParentChildRelationship.objects.create(
            parent=self.parent_school_b,
            child=self.student_school_b,
            school=self.school_b
        )
        
        # Create school-specific data
        SchoolSettings.objects.create(school=self.school_a)
        SchoolSettings.objects.create(school=self.school_b)
        
        # Create API client
        self.client = APIClient()

    def test_school_owners_cannot_access_other_schools_data(self):
        """Test that school owners can only access their own school's data."""
        self.client.force_authenticate(user=self.owner_school_a)
        
        # Should be able to access own school
        url = reverse('accounts:school-detail', kwargs={'pk': self.school_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'School A')
        
        # Should NOT be able to access other school
        url = reverse('accounts:school-detail', kwargs={'pk': self.school_b.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_school_memberships_filtered_by_school_access(self):
        """Test that users can only see memberships for schools they have access to."""
        self.client.force_authenticate(user=self.owner_school_a)
        
        url = reverse('accounts:school_membership-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see memberships for School A
        membership_school_ids = {
            membership['school'] for membership in response.data['results']
        }
        self.assertIn(self.school_a.id, membership_school_ids)
        self.assertNotIn(self.school_b.id, membership_school_ids)

    def test_teachers_cannot_access_other_schools_student_data(self):
        """Test that teachers can only access student data from their own school."""
        self.client.force_authenticate(user=self.teacher_school_a)
        
        url = reverse('accounts:student-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see students from School A
        student_emails = {
            student['user']['email'] for student in response.data['results']
        }
        self.assertIn(self.student_school_a.email, student_emails)
        self.assertNotIn(self.student_school_b.email, student_emails)

    def test_students_cannot_access_other_schools_teacher_data(self):
        """Test that students can only see teachers from their own school."""
        self.client.force_authenticate(user=self.student_school_a)
        
        url = reverse('accounts:teacher-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see teachers from School A
        teacher_emails = {
            teacher['user']['email'] for teacher in response.data['results']
        }
        self.assertIn(self.teacher_school_a.email, teacher_emails)
        self.assertNotIn(self.teacher_school_b.email, teacher_emails)

    def test_parent_child_relationships_isolated_by_school(self):
        """Test that parent-child relationships are properly isolated by school."""
        self.client.force_authenticate(user=self.parent_school_a)
        
        # Parent from School A should not see child from School B
        relationships = ParentChildRelationship.objects.filter(
            parent=self.parent_school_a
        )
        
        child_schools = {rel.school for rel in relationships}
        self.assertIn(self.school_a, child_schools)
        self.assertNotIn(self.school_b, child_schools)

    def test_school_invitations_isolated_by_school(self):
        """Test that school invitations are properly filtered by school."""
        # Create invitations for both schools
        TeacherInvitation.objects.create(
            school=self.school_a,
            email="newteacher.a@example.com",
            invited_by=self.owner_school_a,
            role=SchoolRole.TEACHER
        )
        TeacherInvitation.objects.create(
            school=self.school_b,
            email="newteacher.b@example.com", 
            invited_by=self.owner_school_b,
            role=SchoolRole.TEACHER
        )
        
        self.client.force_authenticate(user=self.owner_school_a)
        
        url = reverse('accounts:teacher-invitation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see invitations for School A
        invitation_emails = {
            invitation['email'] for invitation in response.data['results']
        }
        self.assertIn("newteacher.a@example.com", invitation_emails)
        self.assertNotIn("newteacher.b@example.com", invitation_emails)

    def test_school_activities_isolated_by_school(self):
        """Test that school activities are properly isolated by school."""
        # Create activities for both schools
        SchoolActivity.objects.create(
            school=self.school_a,
            activity_type="user_joined",
            actor=self.owner_school_a
        )
        SchoolActivity.objects.create(
            school=self.school_b,
            activity_type="user_joined",
            actor=self.owner_school_b
        )
        
        self.client.force_authenticate(user=self.owner_school_a)
        
        # Get activities for School A
        url = reverse('accounts:school-dashboard-activity', kwargs={'pk': self.school_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify activities are only from School A
        for activity in response.data['results']:
            self.assertEqual(activity['actor']['id'], self.owner_school_a.id)

    def test_school_settings_access_restricted(self):
        """Test that school settings are only accessible by authorized users."""
        self.client.force_authenticate(user=self.teacher_school_a)
        
        # Teacher should not be able to access school settings
        url = reverse('accounts:school-dashboard-settings', kwargs={'pk': self.school_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # School owner should be able to access their school's settings
        self.client.force_authenticate(user=self.owner_school_a)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cross_school_teacher_profile_access_denied(self):
        """Test that teachers cannot access profiles from other schools."""
        self.client.force_authenticate(user=self.teacher_school_a)
        
        # Should not be able to access teacher profile from School B
        url = reverse('accounts:teacher-detail', kwargs={'pk': self.teacher_profile_b.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Should be able to access own profile
        url = reverse('accounts:teacher-detail', kwargs={'pk': self.teacher_profile_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cross_school_student_profile_access_denied(self):
        """Test that students cannot access profiles from other schools."""
        self.client.force_authenticate(user=self.student_school_a)
        
        # Should not be able to access student profile from School B
        url = reverse('accounts:student-detail', kwargs={'pk': self.student_profile_b.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_school_dashboard_stats_isolation(self):
        """Test that dashboard statistics are properly isolated by school."""
        self.client.force_authenticate(user=self.owner_school_a)
        
        # Get dashboard stats for School A
        url = reverse('accounts:school-dashboard-metrics', kwargs={'pk': self.school_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Stats should only reflect School A data
        stats = response.data
        # Verify student and teacher counts are only for School A
        self.assertEqual(stats['students'], 1)  # Only student_school_a
        self.assertEqual(stats['teachers'], 1)   # Only teacher_school_a
        
        # Should not be able to access School B stats
        url_b = reverse('accounts:school-dashboard-metrics', kwargs={'pk': self.school_b.id})
        response = self.client.get(url_b)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bulk_operations_respect_school_boundaries(self):
        """Test that bulk operations cannot affect users from other schools."""
        self.client.force_authenticate(user=self.owner_school_a)
        
        # Attempt bulk operation with teacher IDs from both schools
        url = reverse('accounts:teacher-bulk-actions')
        data = {
            'action': 'update_status',
            'teacher_ids': [self.teacher_profile_a.id, self.teacher_profile_b.id],
            'parameters': {'is_active': False}
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only affect teacher from School A
        self.teacher_profile_a.refresh_from_db()
        self.teacher_profile_b.refresh_from_db()
        
        # Only School A teacher should be affected by the operation
        affected_membership_a = SchoolMembership.objects.get(
            user=self.teacher_school_a,
            school=self.school_a
        )
        affected_membership_b = SchoolMembership.objects.get(
            user=self.teacher_school_b,
            school=self.school_b
        )
        
        # School B teacher should remain unaffected
        self.assertTrue(affected_membership_b.is_active)

    def test_search_results_scoped_to_user_schools(self):
        """Test that search results are properly scoped to user's schools."""
        self.client.force_authenticate(user=self.teacher_school_a)
        
        url = reverse('accounts:global-search')
        response = self.client.get(url, {'query': 'Teacher', 'types': 'teacher'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only return teachers from School A
        teacher_names = {
            result['name'] for result in response.data['results']
            if result['type'] == 'teacher'
        }
        self.assertIn('Teacher A', teacher_names)
        self.assertNotIn('Teacher B', teacher_names)

    def test_multi_school_user_sees_appropriate_data(self):
        """Test users who belong to multiple schools see combined appropriate data."""
        # Create a user who is a teacher in both schools
        multi_school_user = CustomUser.objects.create_user(
            email="multischool@example.com",
            username="multischool",
            first_name="Multi",
            last_name="School"
        )
        
        # Add to both schools
        SchoolMembership.objects.create(
            user=multi_school_user,
            school=self.school_a,
            role=SchoolRole.TEACHER
        )
        SchoolMembership.objects.create(
            user=multi_school_user,
            school=self.school_b,
            role=SchoolRole.TEACHER
        )
        
        self.client.force_authenticate(user=multi_school_user)
        
        # Should see students from both schools
        url = reverse('accounts:student-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        student_emails = {
            student['user']['email'] for student in response.data['results']
        }
        self.assertIn(self.student_school_a.email, student_emails)
        self.assertIn(self.student_school_b.email, student_emails)

    def test_database_queries_include_school_filtering(self):
        """Test that direct database queries properly include school filtering."""
        from django.db import connection
        from django.test.utils import override_settings
        
        # Test that queryset methods include proper school filtering
        self.client.force_authenticate(user=self.teacher_school_a)
        
        with self.assertNumQueries(5):  # Should be efficient with proper filtering
            url = reverse('accounts:student-list')
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the queries include school filtering
        queries = [q['sql'] for q in connection.queries]
        # At least one query should include school membership filtering
        has_school_filter = any(
            'school' in query.lower() and 'membership' in query.lower()
            for query in queries
        )
        self.assertTrue(has_school_filter, "Queries should include school filtering")

    def test_api_endpoints_reject_invalid_school_contexts(self):
        """Test that API endpoints reject requests with invalid school contexts."""
        self.client.force_authenticate(user=self.teacher_school_a)
        
        # Attempt to create a membership in School B (which user has no access to)
        url = reverse('accounts:school_membership-list')
        data = {
            'user': self.student_school_a.id,
            'school': self.school_b.id,
            'role': SchoolRole.STUDENT
        }
        
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST])

    def tearDown(self):
        """Clean up test data."""
        # Clear all data to prevent test interference
        ParentChildRelationship.objects.all().delete()
        SchoolMembership.objects.all().delete()
        TeacherProfile.objects.all().delete()
        StudentProfile.objects.all().delete()
        TeacherInvitation.objects.all().delete()
        SchoolActivity.objects.all().delete()
        SchoolSettings.objects.all().delete()
        CustomUser.objects.all().delete()
        School.objects.all().delete()


@pytest.mark.django_db
class TestSchoolDataIsolationQuerysets:
    """
    Pytest-based tests for testing querysets and model-level data isolation.
    
    These tests verify that the ORM queries properly filter data by school context
    without relying on API endpoints.
    """

    def test_school_membership_queryset_filtering(self):
        """Test SchoolMembership queryset filtering by school."""
        school1 = School.objects.create(name="School 1")
        school2 = School.objects.create(name="School 2") 
        
        user1 = CustomUser.objects.create_user(email="user1@test.com")
        user2 = CustomUser.objects.create_user(email="user2@test.com")
        
        # Create memberships
        membership1 = SchoolMembership.objects.create(
            user=user1, school=school1, role=SchoolRole.STUDENT
        )
        membership2 = SchoolMembership.objects.create(
            user=user2, school=school2, role=SchoolRole.STUDENT
        )
        
        # Filter by school - should only return relevant membership
        school1_memberships = SchoolMembership.objects.filter(school=school1)
        assert membership1 in school1_memberships
        assert membership2 not in school1_memberships

    def test_teacher_profile_school_filtering(self):
        """Test that teacher profiles are properly filtered by school context."""
        school1 = School.objects.create(name="School 1")
        school2 = School.objects.create(name="School 2")
        
        teacher1 = CustomUser.objects.create_user(email="teacher1@test.com")
        teacher2 = CustomUser.objects.create_user(email="teacher2@test.com")
        
        SchoolMembership.objects.create(
            user=teacher1, school=school1, role=SchoolRole.TEACHER
        )
        SchoolMembership.objects.create(
            user=teacher2, school=school2, role=SchoolRole.TEACHER
        )
        
        profile1 = TeacherProfile.objects.create(user=teacher1, hourly_rate=25.0)
        profile2 = TeacherProfile.objects.create(user=teacher2, hourly_rate=30.0)
        
        # Get teachers from school1 only
        school1_teacher_ids = SchoolMembership.objects.filter(
            school=school1, role=SchoolRole.TEACHER, is_active=True
        ).values_list('user_id', flat=True)
        
        school1_teachers = TeacherProfile.objects.filter(
            user_id__in=school1_teacher_ids
        )
        
        assert profile1 in school1_teachers
        assert profile2 not in school1_teachers

    def test_parent_child_relationship_school_isolation(self):
        """Test that parent-child relationships enforce school isolation."""
        school1 = School.objects.create(name="School 1")
        school2 = School.objects.create(name="School 2")
        
        parent = CustomUser.objects.create_user(email="parent@test.com")
        child1 = CustomUser.objects.create_user(email="child1@test.com")
        child2 = CustomUser.objects.create_user(email="child2@test.com")
        
        # Parent and child1 in school1
        SchoolMembership.objects.create(
            user=parent, school=school1, role=SchoolRole.PARENT
        )
        SchoolMembership.objects.create(
            user=child1, school=school1, role=SchoolRole.STUDENT
        )
        
        # Child2 in school2
        SchoolMembership.objects.create(
            user=child2, school=school2, role=SchoolRole.STUDENT
        )
        
        # Create relationships
        relationship1 = ParentChildRelationship.objects.create(
            parent=parent, child=child1, school=school1
        )
        
        # Parent should only see children from their schools
        parent_children_school1 = ParentChildRelationship.objects.filter(
            parent=parent, school=school1
        )
        
        assert relationship1 in parent_children_school1
        assert parent_children_school1.filter(child=child2).count() == 0

    def test_school_activities_isolation(self):
        """Test that school activities are isolated by school."""
        school1 = School.objects.create(name="School 1")
        school2 = School.objects.create(name="School 2")
        
        user1 = CustomUser.objects.create_user(email="user1@test.com")
        user2 = CustomUser.objects.create_user(email="user2@test.com")
        
        activity1 = SchoolActivity.objects.create(
            school=school1,
            activity_type="user_joined",
            actor=user1
        )
        activity2 = SchoolActivity.objects.create(
            school=school2,
            activity_type="user_joined",
            actor=user2
        )
        
        # Activities should be filtered by school
        school1_activities = SchoolActivity.objects.filter(school=school1)
        
        assert activity1 in school1_activities
        assert activity2 not in school1_activities

    def test_invitation_school_filtering(self):
        """Test that invitations are properly filtered by school."""
        school1 = School.objects.create(name="School 1")
        school2 = School.objects.create(name="School 2")
        
        owner1 = CustomUser.objects.create_user(email="owner1@test.com")
        owner2 = CustomUser.objects.create_user(email="owner2@test.com")
        
        invitation1 = TeacherInvitation.objects.create(
            school=school1,
            email="teacher1@test.com",
            invited_by=owner1,
            role=SchoolRole.TEACHER
        )
        invitation2 = TeacherInvitation.objects.create(
            school=school2,
            email="teacher2@test.com",
            invited_by=owner2,
            role=SchoolRole.TEACHER
        )
        
        # Filter invitations by school
        school1_invitations = TeacherInvitation.objects.filter(school=school1)
        
        assert invitation1 in school1_invitations
        assert invitation2 not in school1_invitations