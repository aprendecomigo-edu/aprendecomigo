"""
Integration tests for tutor discovery system.

Tests the complete flow from tutor profile creation to public discovery,
ensuring all APIs work together seamlessly.
"""

from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from accounts.models import (
    School,
    SchoolMembership,
    SchoolRole,
    TeacherProfile,
    Course,
    EducationalSystem,
    TeacherCourse,
    EducationalSystemType,
)

User = get_user_model()


class TutorDiscoveryIntegrationTestCase(TransactionTestCase):
    """Integration tests for the complete tutor discovery system."""

    def setUp(self):
        """Set up integration test data."""
        cache.clear()
        
        # Create educational systems
        self.edu_system_pt = EducationalSystem.objects.create(
            name="Portugal",
            code=EducationalSystemType.PORTUGAL,
            description="Portuguese education system"
        )
        
        # Create courses
        self.course_math = Course.objects.create(
            name="Mathematics",
            code="MATH101",
            education_level="10",
            educational_system=self.edu_system_pt
        )
        self.course_physics = Course.objects.create(
            name="Physics",
            code="PHYS101",
            education_level="11",
            educational_system=self.edu_system_pt
        )
        
        # Create school
        self.school = School.objects.create(
            name="Integration Test School",
            description="School for integration testing"
        )
        
        self.client = APIClient()

    def test_complete_tutor_onboarding_to_discovery_flow(self):
        """Test complete flow from tutor creation to public discovery."""
        
        # Step 1: Create a new tutor user
        user = User.objects.create_user(
            email="newtutor@test.com",
            name="New Integration Tutor"
        )
        
        # Step 2: Create school membership
        membership = SchoolMembership.objects.create(
            user=user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        # Step 3: Initially, tutor should not appear in discovery (incomplete profile)
        discovery_url = reverse('accounts:tutor-discovery')
        response = self.client.get(discovery_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should not find our new tutor
        tutor_names = [tutor['name'] for tutor in data['results']]
        self.assertNotIn('New Integration Tutor', tutor_names)
        
        # Step 4: Create incomplete teacher profile
        incomplete_profile = TeacherProfile.objects.create(
            user=user,
            bio="Just starting out",
            specialty="",  # Empty specialty makes it incomplete
            hourly_rate=Decimal('25.00'),
            is_profile_complete=False,
            profile_completion_score=30.0
        )
        
        # Step 5: Still should not appear in discovery
        response = self.client.get(discovery_url)
        data = response.json()
        
        tutor_names = [tutor['name'] for tutor in data['results']]
        self.assertNotIn('New Integration Tutor', tutor_names)
        
        # Step 6: Complete the teacher profile
        incomplete_profile.bio = "Experienced mathematics and physics tutor with passion for teaching."
        incomplete_profile.specialty = "Mathematics & Physics"
        incomplete_profile.education = "MSc in Mathematics, BSc in Physics"
        incomplete_profile.is_profile_complete = True
        incomplete_profile.profile_completion_score = 85.0
        incomplete_profile.teaching_subjects = ["Mathematics", "Physics", "Algebra"]
        incomplete_profile.save()
        
        # Step 7: Add courses that the tutor can teach
        math_course = TeacherCourse.objects.create(
            teacher=incomplete_profile,
            course=self.course_math,
            hourly_rate=Decimal('30.00'),
            is_active=True
        )
        
        physics_course = TeacherCourse.objects.create(
            teacher=incomplete_profile,
            course=self.course_physics,
            hourly_rate=Decimal('28.00'),
            is_active=True
        )
        
        # Step 8: Now tutor should appear in discovery
        cache.clear()  # Clear cache to ensure fresh data
        response = self.client.get(discovery_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should find our new tutor
        tutor_names = [tutor['name'] for tutor in data['results']]
        self.assertIn('New Integration Tutor', tutor_names)
        
        # Get our tutor's data
        our_tutor = next(t for t in data['results'] if t['name'] == 'New Integration Tutor')
        
        # Verify all expected data is present
        self.assertEqual(our_tutor['specialty'], 'Mathematics & Physics')
        self.assertEqual(our_tutor['profile_completion_score'], 85.0)
        self.assertTrue(our_tutor['is_profile_complete'])
        self.assertEqual(len(our_tutor['subjects']), 2)  # Math and Physics courses
        
        # Verify subjects are correctly populated
        subject_names = [s['name'] for s in our_tutor['subjects']]
        self.assertIn('Mathematics', subject_names)
        self.assertIn('Physics', subject_names)
        
        # Verify rates are correctly calculated
        math_subject = next(s for s in our_tutor['subjects'] if s['name'] == 'Mathematics')
        physics_subject = next(s for s in our_tutor['subjects'] if s['name'] == 'Physics')
        
        self.assertEqual(math_subject['hourly_rate'], 30.00)
        self.assertEqual(physics_subject['hourly_rate'], 28.00)
        
        # Average rate should be calculated correctly
        expected_avg = (30.00 + 28.00) / 2
        self.assertEqual(our_tutor['average_hourly_rate'], expected_avg)

    def test_filtering_integration_with_profile_updates(self):
        """Test that filtering works correctly as profiles are updated."""
        
        # Create a tutor
        user = User.objects.create_user(
            email="filtering_tutor@test.com",
            name="Filtering Test Tutor"
        )
        
        SchoolMembership.objects.create(
            user=user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        profile = TeacherProfile.objects.create(
            user=user,
            bio="Mathematics specialist",
            specialty="Mathematics",
            hourly_rate=Decimal('35.00'),
            is_profile_complete=True,
            profile_completion_score=80.0,
            teaching_subjects=["Mathematics", "Algebra"]
        )
        
        # Add a math course
        TeacherCourse.objects.create(
            teacher=profile,
            course=self.course_math,
            hourly_rate=Decimal('40.00'),
            is_active=True
        )
        
        discovery_url = reverse('accounts:tutor-discovery')
        
        # Test 1: Filter by subject - should find tutor
        cache.clear()
        response = self.client.get(discovery_url, {'subjects': 'Mathematics'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['results'][0]['name'], 'Filtering Test Tutor')
        
        # Test 2: Filter by rate range - should find tutor
        response = self.client.get(discovery_url, {'rate_min': '35', 'rate_max': '45'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['total'], 1)
        
        # Test 3: Filter by specialty search - should find tutor
        response = self.client.get(discovery_url, {'search': 'Mathematics'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['total'], 1)
        
        # Test 4: Add physics course and verify filtering still works
        TeacherCourse.objects.create(
            teacher=profile,
            course=self.course_physics,
            hourly_rate=Decimal('42.00'),
            is_active=True
        )
        
        # Update specialty
        profile.specialty = "Mathematics & Physics"
        profile.teaching_subjects = ["Mathematics", "Physics", "Algebra"]
        profile.save()
        
        cache.clear()
        
        # Should now be found by physics filter too
        response = self.client.get(discovery_url, {'subjects': 'Physics'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['results'][0]['name'], 'Filtering Test Tutor')
        
        # Verify both subjects are now listed
        tutor = data['results'][0]
        subject_names = [s['name'] for s in tutor['subjects']]
        self.assertIn('Mathematics', subject_names)
        self.assertIn('Physics', subject_names)

    def test_membership_deactivation_removes_from_discovery(self):
        """Test that deactivating membership removes tutor from discovery."""
        
        # Create tutor with complete profile
        user = User.objects.create_user(
            email="deactivation_tutor@test.com",
            name="Deactivation Test Tutor"
        )
        
        membership = SchoolMembership.objects.create(
            user=user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        profile = TeacherProfile.objects.create(
            user=user,
            bio="Physics specialist",
            specialty="Physics",
            hourly_rate=Decimal('30.00'),
            is_profile_complete=True,
            profile_completion_score=75.0
        )
        
        TeacherCourse.objects.create(
            teacher=profile,
            course=self.course_physics,
            hourly_rate=Decimal('35.00'),
            is_active=True
        )
        
        discovery_url = reverse('accounts:tutor-discovery')
        
        # Initially should be discoverable
        cache.clear()
        response = self.client.get(discovery_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        tutor_names = [tutor['name'] for tutor in data['results']]
        self.assertIn('Deactivation Test Tutor', tutor_names)
        
        # Deactivate membership
        membership.is_active = False
        membership.save()
        
        # Should no longer be discoverable
        cache.clear()
        response = self.client.get(discovery_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        tutor_names = [tutor['name'] for tutor in data['results']]
        self.assertNotIn('Deactivation Test Tutor', tutor_names)

    def test_course_deactivation_affects_subject_filtering(self):
        """Test that deactivating courses affects subject-based filtering."""
        
        # Create tutor with multiple courses
        user = User.objects.create_user(
            email="course_deactivation_tutor@test.com",
            name="Course Deactivation Tutor"
        )
        
        SchoolMembership.objects.create(
            user=user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        profile = TeacherProfile.objects.create(
            user=user,
            bio="Multi-subject tutor",
            specialty="Mathematics & Physics",
            hourly_rate=Decimal('30.00'),
            is_profile_complete=True,
            profile_completion_score=80.0
        )
        
        math_course = TeacherCourse.objects.create(
            teacher=profile,
            course=self.course_math,
            hourly_rate=Decimal('35.00'),
            is_active=True
        )
        
        physics_course = TeacherCourse.objects.create(
            teacher=profile,
            course=self.course_physics,
            hourly_rate=Decimal('32.00'),
            is_active=True
        )
        
        discovery_url = reverse('accounts:tutor-discovery')
        
        # Initially should be found by both subject filters
        cache.clear()
        
        # Test math filter
        response = self.client.get(discovery_url, {'subjects': 'Mathematics'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total'], 1)
        
        # Test physics filter
        response = self.client.get(discovery_url, {'subjects': 'Physics'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total'], 1)
        
        # Deactivate math course
        math_course.is_active = False
        math_course.save()
        
        cache.clear()
        
        # Should no longer be found by math filter
        response = self.client.get(discovery_url, {'subjects': 'Mathematics'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total'], 0)
        
        # But should still be found by physics filter
        response = self.client.get(discovery_url, {'subjects': 'Physics'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total'], 1)
        
        # And in general discovery
        response = self.client.get(discovery_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        tutor_names = [tutor['name'] for tutor in data['results']]
        self.assertIn('Course Deactivation Tutor', tutor_names)
        
        # But should only have physics subject listed
        our_tutor = next(t for t in data['results'] if t['name'] == 'Course Deactivation Tutor')
        subject_names = [s['name'] for s in our_tutor['subjects']]
        self.assertNotIn('Mathematics', subject_names)
        self.assertIn('Physics', subject_names)

    def test_individual_tutor_vs_school_teacher_distinction(self):
        """Test that individual tutors and school teachers are properly distinguished."""
        
        # Create individual tutor school
        individual_school = School.objects.create(
            name="Individual Tutor School",
            description="School for individual tutor"
        )
        
        # Create individual tutor (school owner)
        individual_user = User.objects.create_user(
            email="individual@test.com",
            name="Individual Tutor"
        )
        
        SchoolMembership.objects.create(
            user=individual_user,
            school=individual_school,
            role=SchoolRole.SCHOOL_OWNER,  # Individual tutor
            is_active=True
        )
        
        individual_profile = TeacherProfile.objects.create(
            user=individual_user,
            bio="Independent mathematics tutor",
            specialty="Mathematics",
            hourly_rate=Decimal('40.00'),
            is_profile_complete=True,
            profile_completion_score=90.0
        )
        
        # Create school teacher
        school_teacher_user = User.objects.create_user(
            email="schoolteacher@test.com",
            name="School Teacher"
        )
        
        SchoolMembership.objects.create(
            user=school_teacher_user,
            school=self.school,  # Regular school
            role=SchoolRole.TEACHER,  # School employee
            is_active=True
        )
        
        teacher_profile = TeacherProfile.objects.create(
            user=school_teacher_user,
            bio="Physics teacher at established school",
            specialty="Physics",
            hourly_rate=Decimal('35.00'),
            is_profile_complete=True,
            profile_completion_score=85.0
        )
        
        # Add courses for both
        TeacherCourse.objects.create(
            teacher=individual_profile,
            course=self.course_math,
            hourly_rate=Decimal('45.00'),
            is_active=True
        )
        
        TeacherCourse.objects.create(
            teacher=teacher_profile,
            course=self.course_physics,
            hourly_rate=Decimal('38.00'),
            is_active=True
        )
        
        discovery_url = reverse('accounts:tutor-discovery')
        
        # Test discovery includes both
        cache.clear()
        response = self.client.get(discovery_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should find both tutors
        self.assertEqual(data['total'], 2)
        
        # Verify individual tutor is marked correctly
        individual_tutor = next(t for t in data['results'] if t['name'] == 'Individual Tutor')
        self.assertTrue(individual_tutor['school']['is_individual_tutor'])
        
        # Verify school teacher is marked correctly
        school_teacher = next(t for t in data['results'] if t['name'] == 'School Teacher')
        self.assertFalse(school_teacher['school']['is_individual_tutor'])
        
        # Verify school information is included
        self.assertEqual(individual_tutor['school']['name'], 'Individual Tutor School')
        self.assertEqual(school_teacher['school']['name'], 'Integration Test School')

    def test_profile_completion_score_ordering_integration(self):
        """Test that profile completion score ordering works correctly."""
        
        # Create tutors with different completion scores
        tutors_data = [
            ("High Score Tutor", 95.0, "Mathematics"),
            ("Medium Score Tutor", 80.0, "Physics"),
            ("Low Score Tutor", 70.0, "Chemistry")
        ]
        
        for name, score, specialty in tutors_data:
            user = User.objects.create_user(
                email=f"{name.lower().replace(' ', '')}@test.com",
                name=name
            )
            
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.TEACHER,
                is_active=True
            )
            
            profile = TeacherProfile.objects.create(
                user=user,
                bio=f"{specialty} specialist",
                specialty=specialty,
                hourly_rate=Decimal('30.00'),
                is_profile_complete=True,
                profile_completion_score=score
            )
            
            # Add appropriate course
            if specialty == "Mathematics":
                course = self.course_math
            else:
                course = self.course_physics  # Use physics for others
            
            TeacherCourse.objects.create(
                teacher=profile,
                course=course,
                hourly_rate=Decimal('35.00'),
                is_active=True
            )
        
        discovery_url = reverse('accounts:tutor-discovery')
        
        # Test default ordering (by completion score descending)
        cache.clear()
        response = self.client.get(discovery_url, {'ordering': '-completion_score'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should be ordered by completion score (highest first)
        expected_order = ["High Score Tutor", "Medium Score Tutor", "Low Score Tutor"]
        actual_order = [tutor['name'] for tutor in data['results']]
        
        self.assertEqual(actual_order, expected_order)
        
        # Verify scores are correctly returned
        for i, tutor in enumerate(data['results']):
            expected_score = tutors_data[i][1]
            self.assertEqual(tutor['profile_completion_score'], expected_score)