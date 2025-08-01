"""
Tests for StudentProgress and ProgressAssessment models.

Following TDD approach - write tests first, then implement models.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from accounts.models import (
    CustomUser, School, SchoolMembership, SchoolRole, 
    TeacherProfile, StudentProfile, Course, EducationalSystem
)
# Models to be implemented:
# from accounts.models import StudentProgress, ProgressAssessment


class StudentProgressModelTest(TestCase):
    """Test suite for StudentProgress model."""
    
    def setUp(self):
        """Set up test data."""
        # Create educational system
        self.educational_system, _ = EducationalSystem.objects.get_or_create(
            code="pt",
            defaults={
                "name": "Portugal", 
                "description": "Portuguese education system"
            }
        )
        
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
            bio="Test teacher bio"
        )
        
        # Create teacher school membership
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )
        
        # Create student user and profile
        self.student_user = CustomUser.objects.create_user(
            email="student@test.com",
            name="Student Test",
            password="testpass123"
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            educational_system=self.educational_system,
            school_year="7",
            birth_date="2010-01-01"
        )
        
        # Create student school membership
        SchoolMembership.objects.create(
            user=self.student_user,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        
        # Create course
        self.course = Course.objects.create(
            name="Mathematics",
            code="MATH7",
            educational_system=self.educational_system,
            education_level="ensino_basico_3_ciclo"
        )
    
    def test_student_progress_creation(self):
        """Test creating a StudentProgress instance."""
        from accounts.models import StudentProgress
        
        progress = StudentProgress.objects.create(
            student=self.student_user,
            teacher=self.teacher_profile,
            school=self.school,
            course=self.course,
            current_level="beginner",
            completion_percentage=Decimal("25.50"),
            skills_mastered=["basic_arithmetic", "fractions"],
            notes="Student is making good progress"
        )
        
        self.assertEqual(progress.student, self.student_user)
        self.assertEqual(progress.teacher, self.teacher_profile)
        self.assertEqual(progress.school, self.school)
        self.assertEqual(progress.course, self.course)
        self.assertEqual(progress.current_level, "beginner")
        self.assertEqual(progress.completion_percentage, Decimal("25.50"))
        self.assertEqual(progress.skills_mastered, ["basic_arithmetic", "fractions"])
        self.assertEqual(progress.notes, "Student is making good progress")
        self.assertIsNotNone(progress.created_at)
        self.assertIsNotNone(progress.updated_at)
    
    def test_student_progress_unique_constraint(self):
        """Test that a student can only have one progress record per teacher per course."""
        from accounts.models import StudentProgress
        
        # Create first progress record
        StudentProgress.objects.create(
            student=self.student_user,
            teacher=self.teacher_profile,
            school=self.school,
            course=self.course,
            current_level="beginner"
        )
        
        # Try to create another progress record for same student/teacher/course
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            StudentProgress.objects.create(
                student=self.student_user,
                teacher=self.teacher_profile,
                school=self.school,
                course=self.course,
                current_level="intermediate"
            )
    
    def test_student_progress_str_method(self):
        """Test string representation of StudentProgress."""
        from accounts.models import StudentProgress
        
        progress = StudentProgress.objects.create(
            student=self.student_user,
            teacher=self.teacher_profile,
            school=self.school,
            course=self.course,
            current_level="intermediate"
        )
        
        expected_str = f"{self.student_user.name} - {self.course.name} (Teacher: {self.teacher_user.name})"
        self.assertEqual(str(progress), expected_str)
    
    def test_student_progress_completion_percentage_validation(self):
        """Test that completion percentage is validated between 0 and 100."""
        from accounts.models import StudentProgress
        
        # Test valid percentage
        progress = StudentProgress(
            student=self.student_user,
            teacher=self.teacher_profile,
            school=self.school,
            course=self.course,
            completion_percentage=Decimal("50.00")
        )
        progress.clean()  # Should not raise
        
        # Test invalid percentage > 100
        progress.completion_percentage = Decimal("150.00")
        with self.assertRaises(ValidationError):
            progress.clean()
        
        # Test invalid negative percentage
        progress.completion_percentage = Decimal("-10.00")
        with self.assertRaises(ValidationError):
            progress.clean()


class ProgressAssessmentModelTest(TestCase):
    """Test suite for ProgressAssessment model."""
    
    def setUp(self):
        """Set up test data."""
        # Create educational system
        self.educational_system, _ = EducationalSystem.objects.get_or_create(
            code="pt",
            defaults={
                "name": "Portugal", 
                "description": "Portuguese education system"
            }
        )
        
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
            bio="Test teacher bio"
        )
        
        # Create student user
        self.student_user = CustomUser.objects.create_user(
            email="student@test.com",
            name="Student Test",
            password="testpass123"
        )
        
        # Create course
        self.course = Course.objects.create(
            name="Mathematics",
            code="MATH7",
            educational_system=self.educational_system,
            education_level="ensino_basico_3_ciclo"
        )
    
    def test_progress_assessment_creation(self):
        """Test creating a ProgressAssessment instance."""
        from accounts.models import StudentProgress, ProgressAssessment
        
        # Create progress record first
        progress = StudentProgress.objects.create(
            student=self.student_user,
            teacher=self.teacher_profile,
            school=self.school,
            course=self.course,
            current_level="intermediate"
        )
        
        # Create assessment
        assessment = ProgressAssessment.objects.create(
            student_progress=progress,
            assessment_type="quiz",
            title="Fractions Quiz",
            score=Decimal("85.50"),
            max_score=Decimal("100.00"),
            assessment_date=timezone.now().date(),
            skills_assessed=["fractions", "decimals"],
            teacher_notes="Good understanding of basic fractions",
            is_graded=True
        )
        
        self.assertEqual(assessment.student_progress, progress)
        self.assertEqual(assessment.assessment_type, "quiz")
        self.assertEqual(assessment.title, "Fractions Quiz")
        self.assertEqual(assessment.score, Decimal("85.50"))
        self.assertEqual(assessment.max_score, Decimal("100.00"))
        self.assertEqual(assessment.skills_assessed, ["fractions", "decimals"])
        self.assertEqual(assessment.teacher_notes, "Good understanding of basic fractions")
        self.assertTrue(assessment.is_graded)
        self.assertIsNotNone(assessment.created_at)
    
    def test_progress_assessment_percentage_property(self):
        """Test the percentage property calculation."""
        from accounts.models import StudentProgress, ProgressAssessment
        
        # Create progress record first
        progress = StudentProgress.objects.create(
            student=self.student_user,
            teacher=self.teacher_profile,
            school=self.school,
            course=self.course,
            current_level="intermediate"
        )
        
        # Create assessment
        assessment = ProgressAssessment.objects.create(
            student_progress=progress,
            assessment_type="test",
            title="Math Test",
            score=Decimal("17.50"),
            max_score=Decimal("20.00"),
            assessment_date=timezone.now().date()
        )
        
        expected_percentage = Decimal("87.50")
        self.assertEqual(assessment.percentage, expected_percentage)
    
    def test_progress_assessment_str_method(self):
        """Test string representation of ProgressAssessment."""
        from accounts.models import StudentProgress, ProgressAssessment
        
        # Create progress record first
        progress = StudentProgress.objects.create(
            student=self.student_user,
            teacher=self.teacher_profile,
            school=self.school,
            course=self.course,
            current_level="intermediate"
        )
        
        # Create assessment
        assessment = ProgressAssessment.objects.create(
            student_progress=progress,
            assessment_type="homework",
            title="Algebra Homework",
            score=Decimal("9.00"),
            max_score=Decimal("10.00"),
            assessment_date=timezone.now().date()
        )
        
        expected_str = f"Algebra Homework - {self.student_user.name} (90.00%)"
        self.assertEqual(str(assessment), expected_str)
    
    def test_progress_assessment_score_validation(self):
        """Test that score cannot exceed max_score."""
        from accounts.models import StudentProgress, ProgressAssessment
        
        # Create progress record first
        progress = StudentProgress.objects.create(
            student=self.student_user,
            teacher=self.teacher_profile,
            school=self.school,
            course=self.course,
            current_level="intermediate"
        )
        
        # Test valid score
        assessment = ProgressAssessment(
            student_progress=progress,
            assessment_type="quiz",
            title="Test Quiz",
            score=Decimal("8.50"),
            max_score=Decimal("10.00"),
            assessment_date=timezone.now().date()
        )
        assessment.clean()  # Should not raise
        
        # Test invalid score > max_score
        assessment.score = Decimal("12.00")
        with self.assertRaises(ValidationError):
            assessment.clean()
        
        # Test negative score
        assessment.score = Decimal("-1.00")
        with self.assertRaises(ValidationError):
            assessment.clean()