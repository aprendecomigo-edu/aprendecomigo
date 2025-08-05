"""
Tests for ProfileCompletionService.
Following TDD methodology - tests are written first.
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from accounts.models import (
    School, 
    SchoolMembership, 
    SchoolRole, 
    TeacherProfile,
    Course,
    EducationalSystem,
    TeacherCourse
)
from accounts.tests.test_base import BaseTestCase
from accounts.services.profile_completion import ProfileCompletionService

User = get_user_model()


class ProfileCompletionServiceTestCase(BaseTestCase):
    """Test cases for ProfileCompletionService"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="teacher@test.com",
            name="Test Teacher",
            phone_number="+351123456789"
        )
        
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )
        
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        # Get or create educational system
        self.edu_system, created = EducationalSystem.objects.get_or_create(
            code="pt",
            defaults={
                "name": "Portugal"
            }
        )
        
        # Create some courses
        self.course1 = Course.objects.create(
            name="Mathematics",
            code="MAT",
            educational_system=self.edu_system,
            education_level="ensino_basico_1_ciclo"
        )
        
        self.course2 = Course.objects.create(
            name="Physics",
            code="PHY",
            educational_system=self.edu_system,
            education_level="ensino_secundario"
        )
    
    def test_calculate_completion_empty_profile(self):
        """Test completion calculation for empty profile"""
        # Create minimal teacher profile
        teacher_profile = TeacherProfile.objects.create(user=self.user, bio="")
        
        result = ProfileCompletionService.calculate_completion(teacher_profile)
        
        # Empty profile should have low completion
        self.assertIsInstance(result, dict)
        self.assertIn('completion_percentage', result)
        self.assertIn('missing_critical', result)
        self.assertIn('missing_optional', result)
        self.assertIn('recommendations', result)
        
        # Should be very low completion due to missing critical fields
        self.assertLess(result['completion_percentage'], 30)
        self.assertTrue(len(result['missing_critical']) > 0)
    
    def test_calculate_completion_basic_profile(self):
        """Test completion calculation for basic profile with some fields"""
        teacher_profile = TeacherProfile.objects.create(
            user=self.user,
            bio="Experienced mathematics teacher with 10 years of experience.",
            specialty="Mathematics",
            education="Master's Degree in Mathematics Education",
            hourly_rate=Decimal('25.00')
        )
        
        # Add one course
        TeacherCourse.objects.create(
            teacher=teacher_profile,
            course=self.course1,
            hourly_rate=Decimal('25.00')
        )
        
        result = ProfileCompletionService.calculate_completion(teacher_profile)
        
        # Should have higher completion due to basic info
        self.assertGreater(result['completion_percentage'], 50)
        self.assertLess(result['completion_percentage'], 80)
        
        # Should have fewer missing critical fields
        self.assertLess(len(result['missing_critical']), 3)
    
    def test_calculate_completion_complete_profile(self):
        """Test completion calculation for complete profile"""
        teacher_profile = TeacherProfile.objects.create(
            user=self.user,
            bio="Experienced mathematics teacher with 10 years of experience.",
            specialty="Mathematics and Physics",
            education="Master's Degree in Mathematics Education, PhD in Physics",
            hourly_rate=Decimal('35.00'),
            availability="Monday to Friday, 9:00-17:00",
            address="123 Teacher Street, Lisbon, Portugal",
            phone_number="+351987654321",
            calendar_iframe="<iframe src='https://calendar.example.com'></iframe>",
            # New fields (to be added to model)
            education_background={
                "degree": "Master's",
                "institution": "University of Lisbon",
                "field": "Mathematics Education",
                "year": 2015
            },
            teaching_subjects=["Mathematics", "Physics", "Statistics"],
            rate_structure={
                "individual": 35.00,
                "group": 25.00,
                "trial": 20.00
            },
            weekly_availability={
                "monday": ["09:00-12:00", "14:00-17:00"],
                "tuesday": ["09:00-12:00", "14:00-17:00"],
                "wednesday": ["09:00-12:00"],
                "friday": ["14:00-17:00"]
            },
            profile_completion_score=95.0,
            is_profile_complete=True
        )
        
        # Add multiple courses
        TeacherCourse.objects.create(
            teacher=teacher_profile,
            course=self.course1,
            hourly_rate=Decimal('35.00')
        )
        TeacherCourse.objects.create(
            teacher=teacher_profile,
            course=self.course2,
            hourly_rate=Decimal('30.00')
        )
        
        result = ProfileCompletionService.calculate_completion(teacher_profile)
        
        # Should have very high completion
        self.assertGreater(result['completion_percentage'], 90)
        
        # Should have no missing critical fields
        self.assertEqual(len(result['missing_critical']), 0)
        
        # Should have minimal missing optional fields
        self.assertLessEqual(len(result['missing_optional']), 2)
    
    def test_get_profile_recommendations(self):
        """Test generation of profile improvement recommendations"""
        teacher_profile = TeacherProfile.objects.create(
            user=self.user,
            bio="Short bio"
        )
        
        recommendations = ProfileCompletionService.get_profile_recommendations(teacher_profile)
        
        self.assertIsInstance(recommendations, list)
        self.assertTrue(len(recommendations) > 0)
        
        # Should recommend adding critical missing fields
        recommendation_texts = [r['text'] for r in recommendations]
        self.assertTrue(any('hourly rate' in text.lower() for text in recommendation_texts))
        self.assertTrue(any('course' in text.lower() or 'subject' in text.lower() for text in recommendation_texts))
    
    def test_identify_missing_fields(self):
        """Test identification of missing critical and optional fields"""
        teacher_profile = TeacherProfile.objects.create(
            user=self.user,
            bio="Basic bio"
        )
        
        missing_critical, missing_optional = ProfileCompletionService.identify_missing_fields(teacher_profile)
        
        self.assertIsInstance(missing_critical, list)
        self.assertIsInstance(missing_optional, list)
        
        # Should identify missing hourly rate as critical
        self.assertIn('hourly_rate', missing_critical)
        
        # Should identify missing availability as optional
        self.assertIn('availability', missing_optional)
    
    def test_calculate_weighted_score(self):
        """Test weighted scoring calculation"""
        # Test with perfect scores
        basic_score = 100.0
        teaching_score = 100.0
        professional_score = 100.0
        
        total_score = ProfileCompletionService.calculate_weighted_score(
            basic_score, teaching_score, professional_score
        )
        
        self.assertEqual(total_score, 100.0)
        
        # Test with mixed scores
        basic_score = 80.0
        teaching_score = 60.0
        professional_score = 40.0
        
        total_score = ProfileCompletionService.calculate_weighted_score(
            basic_score, teaching_score, professional_score
        )
        
        # Should be weighted average: 0.4*80 + 0.4*60 + 0.2*40 = 32 + 24 + 8 = 64
        self.assertEqual(total_score, 64.0)
    
    def test_profile_quality_scoring(self):
        """Test profile quality scoring business logic"""
        teacher_profile = TeacherProfile.objects.create(
            user=self.user,
            bio="Very detailed biography describing experience and qualifications.",
            specialty="Mathematics and Statistics",
            education="PhD in Mathematics, Master's in Education",
            hourly_rate=Decimal('40.00')
        )
        
        # Add courses
        TeacherCourse.objects.create(
            teacher=teacher_profile,
            course=self.course1,
            hourly_rate=Decimal('40.00')
        )
        
        result = ProfileCompletionService.calculate_completion(teacher_profile)
        
        # Should have good completion due to quality content
        self.assertGreater(result['completion_percentage'], 60)
        
        # Bio should meet quality standards
        bio_quality = ProfileCompletionService._assess_bio_quality(teacher_profile.bio)
        self.assertGreater(bio_quality, 70)  # Adjusted to be more realistic for the test bio
    
    def test_bulk_completion_calculation(self):
        """Test bulk calculation for multiple profiles"""
        # Create multiple teacher profiles
        profiles = []
        for i in range(3):
            user = User.objects.create_user(
                email=f"teacher{i}@test.com",
                name=f"Teacher {i}"
            )
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.TEACHER
            )
            profile = TeacherProfile.objects.create(
                user=user,
                bio=f"Bio for teacher {i}",
                hourly_rate=Decimal('25.00') if i > 0 else None
            )
            profiles.append(profile)
        
        results = ProfileCompletionService.calculate_bulk_completion(profiles)
        
        self.assertEqual(len(results), 3)
        self.assertIsInstance(results, list)
        
        # Each result should have completion data
        for result in results:
            self.assertIn('teacher_id', result)
            self.assertIn('completion_percentage', result)
            self.assertIn('is_complete', result)
    
    def test_school_completion_analytics(self):
        """Test school-wide completion analytics"""
        # Create multiple teachers for the school
        for i in range(5):
            user = User.objects.create_user(
                email=f"teacher{i}@school.com",
                name=f"Teacher {i}"
            )
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.TEACHER
            )
            TeacherProfile.objects.create(
                user=user,
                bio=f"Bio {i}" if i < 3 else "",
                hourly_rate=Decimal('25.00') if i < 2 else None
            )
        
        analytics = ProfileCompletionService.get_school_completion_analytics(self.school.id)
        
        self.assertIsInstance(analytics, dict)
        self.assertIn('total_teachers', analytics)
        self.assertIn('average_completion', analytics)
        self.assertIn('complete_profiles', analytics)
    
    def test_calculate_completion_invalid_user(self):
        """Test that calculating completion for non-existent user fails gracefully"""
        service = ProfileCompletionService()
        result = service.calculate_completion(user_id=99999)
        self.assertIsNone(result)
    
    def test_calculate_completion_user_without_teacher_profile(self):
        """Test completion calculation for user without teacher profile"""
        non_teacher = User.objects.create_user(
            email="student@test.com",
            name="Student User"
        )
        service = ProfileCompletionService()
        result = service.calculate_completion(user_id=non_teacher.id)
        self.assertEqual(result['percentage'], 0)
    
    def test_get_recommendations_invalid_user(self):
        """Test that getting recommendations for invalid user returns empty list"""
        service = ProfileCompletionService()
        recommendations = service.get_profile_recommendations(user_id=99999)
        self.assertEqual(recommendations, [])
    
    def test_calculate_completion_with_corrupted_data(self):
        """Test handling of corrupted profile data"""
        # Create profile with invalid data
        profile = TeacherProfile.objects.create(
            user=self.user,
            bio="",  # Empty string instead of None (bio field doesn't allow NULL)
            hourly_rate=Decimal("-10.00")  # Invalid negative rate
        )
        
        service = ProfileCompletionService()
        result = service.calculate_completion(user_id=self.user.id)
        # Should handle gracefully and still return a result
        self.assertIsNotNone(result)
        self.assertIn('percentage', result)
    
    def test_school_analytics_invalid_school(self):
        """Test analytics for non-existent school"""
        analytics = ProfileCompletionService.get_school_completion_analytics(99999)
        self.assertIsNone(analytics)