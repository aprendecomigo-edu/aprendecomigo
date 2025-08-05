"""
Tests for enhanced teacher profile creation during invitation acceptance.

Tests GitHub issue #50: [Flow C] Teacher Acceptance Workflow - Complete Profile Creation During Invitation Acceptance

This test suite covers:
- Comprehensive teacher profile creation with all fields during invitation acceptance
- File upload support for profile photos and credentials
- Validation of structured JSON fields
- Transaction safety and atomicity
- Backward compatibility with existing invitation acceptance
- Security measures and proper error handling
"""

import tempfile
import json
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from knox.models import AuthToken

from accounts.models import (
    School,
    SchoolMembership,
    SchoolRole,
    TeacherInvitation,
    TeacherProfile,
    InvitationStatus,
    EmailDeliveryStatus,
)

User = get_user_model()


class TeacherProfileCreationInvitationAcceptanceTest(APITestCase):
    """Test cases for comprehensive teacher profile creation during invitation acceptance."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            name="Admin User"
        )
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com", 
            name="Teacher User"
        )
        
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )
        
        # Create school membership for admin
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
        
        # Create test invitation
        self.invitation = TeacherInvitation.objects.create(
            email=self.teacher_user.email,
            school=self.school,
            invited_by=self.admin_user,
            role=SchoolRole.TEACHER,
            status=InvitationStatus.SENT,
            email_delivery_status=EmailDeliveryStatus.DELIVERED,
            expires_at=timezone.now() + timezone.timedelta(days=7),
            batch_id=uuid.uuid4()
        )
        
        # Create auth tokens
        self.admin_token = AuthToken.objects.create(self.admin_user)[1]
        self.teacher_token = AuthToken.objects.create(self.teacher_user)[1]
    
    def _create_test_image(self, format='PNG'):
        """Create a test image for upload testing."""
        image = Image.new('RGB', (100, 100), color='red')
        image_io = BytesIO()
        image.save(image_io, format=format)
        image_io.seek(0)
        return SimpleUploadedFile(
            name=f'test_image.{format.lower()}',
            content=image_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )
    
    def _create_test_document(self, filename='test_document.pdf'):
        """Create a test document for upload testing."""
        return SimpleUploadedFile(
            name=filename,
            content=b'Test document content',
            content_type='application/pdf'
        )
    
    def test_accept_invitation_with_comprehensive_profile_data(self):
        """Test successful invitation acceptance with comprehensive profile data."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        comprehensive_profile_data = {
            # Basic Information
            'bio': 'Experienced mathematics teacher with 10+ years of experience in secondary education.',
            'specialty': 'Mathematics and Physics',
            
            # Teaching Subjects with expertise levels
            'teaching_subjects': [
                {'subject': 'Mathematics', 'level': 'expert', 'grade_levels': ['9', '10', '11', '12']},
                {'subject': 'Physics', 'level': 'advanced', 'grade_levels': ['10', '11', '12']},
                {'subject': 'Calculus', 'level': 'expert', 'grade_levels': ['11', '12']}
            ],
            
            # Grade Levels Preferences
            'grade_level_preferences': ['high_school', 'university_prep'],
            
            # Rates & Compensation
            'hourly_rate': '45.50',
            'rate_structure': {
                'individual_tutoring': 45.50,
                'group_sessions': 30.00,
                'exam_preparation': 55.00,
                'currency': 'EUR'
            },
            
            # Availability and Schedule
            'availability': 'Monday to Friday, 14:00-20:00; Saturday mornings available',
            'weekly_availability': {
                'monday': [{'start': '14:00', 'end': '20:00'}],
                'tuesday': [{'start': '14:00', 'end': '20:00'}],
                'wednesday': [{'start': '14:00', 'end': '20:00'}],
                'thursday': [{'start': '14:00', 'end': '20:00'}],
                'friday': [{'start': '14:00', 'end': '20:00'}],
                'saturday': [{'start': '9:00', 'end': '13:00'}]
            },
            'availability_schedule': {
                'timezone': 'Europe/Lisbon',
                'preferred_session_duration': 60,
                'break_between_sessions': 15,
                'maximum_daily_hours': 6
            },
            
            # Credentials and Education
            'education_background': {
                'degrees': [
                    {
                        'degree': 'Master of Science',
                        'field': 'Mathematics Education',
                        'institution': 'University of Porto',
                        'year': 2015,
                        'grade': 'Distinction'
                    },
                    {
                        'degree': 'Bachelor of Science',
                        'field': 'Mathematics',
                        'institution': 'University of Porto',
                        'year': 2013,
                        'grade': 'First Class Honours'
                    }
                ],
                'certifications': [
                    {
                        'name': 'Advanced Mathematics Teaching Certificate',
                        'issuer': 'Portuguese Ministry of Education',
                        'year': 2016,
                        'expiry': 2026
                    }
                ]
            },
            
            # Teaching Experience
            'teaching_experience': {
                'total_years': 10,
                'positions': [
                    {
                        'institution': 'Porto Secondary School',
                        'position': 'Mathematics Teacher',
                        'start_year': 2015,
                        'end_year': 2020,
                        'subjects': ['Mathematics', 'Physics'],
                        'achievements': ['Increased class average by 15%', 'Developed innovative teaching methods']
                    },
                    {
                        'institution': 'Private Tutoring',
                        'position': 'Independent Tutor',
                        'start_year': 2020,
                        'end_year': 2025,
                        'subjects': ['Mathematics', 'Physics', 'Calculus'],
                        'achievements': ['100+ successful students', 'Specialization in exam preparation']
                    }
                ],
                'specializations': ['Exam Preparation', 'Learning Difficulties Support', 'Advanced Mathematics']
            },
            
            # Contact Information
            'phone_number': '+351912345678',
            'address': 'Rua Example, 123, 4000-001 Porto, Portugal'
        }
        
        # Authenticate as the teacher
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        
        response = self.client.post(url, comprehensive_profile_data, format='json')
        
        # This should fail initially as the endpoint doesn't support comprehensive profile creation yet
        # Following TDD - this test should fail first, then we implement the functionality
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('invitation', response.data)
        self.assertIn('teacher_profile', response.data)
        
        # Verify invitation was accepted
        self.invitation.refresh_from_db()
        self.assertTrue(self.invitation.is_accepted)
        self.assertEqual(self.invitation.status, InvitationStatus.ACCEPTED.value)
        
        # Verify comprehensive teacher profile was created
        self.assertTrue(hasattr(self.teacher_user, 'teacher_profile'))
        teacher_profile = self.teacher_user.teacher_profile
        
        # Verify basic information
        self.assertEqual(teacher_profile.bio, comprehensive_profile_data['bio'])
        self.assertEqual(teacher_profile.specialty, comprehensive_profile_data['specialty'])
        self.assertEqual(teacher_profile.hourly_rate, Decimal(comprehensive_profile_data['hourly_rate']))
        
        # Verify structured JSON fields
        self.assertEqual(teacher_profile.teaching_subjects, comprehensive_profile_data['teaching_subjects'])
        self.assertEqual(teacher_profile.grade_level_preferences, comprehensive_profile_data['grade_level_preferences'])
        self.assertEqual(teacher_profile.rate_structure, comprehensive_profile_data['rate_structure'])
        self.assertEqual(teacher_profile.weekly_availability, comprehensive_profile_data['weekly_availability'])
        self.assertEqual(teacher_profile.availability_schedule, comprehensive_profile_data['availability_schedule'])
        self.assertEqual(teacher_profile.education_background, comprehensive_profile_data['education_background'])
        self.assertEqual(teacher_profile.teaching_experience, comprehensive_profile_data['teaching_experience'])
        
        # Verify contact information
        self.assertEqual(teacher_profile.phone_number, comprehensive_profile_data['phone_number'])
        self.assertEqual(teacher_profile.address, comprehensive_profile_data['address'])
        
        # Verify profile completion tracking
        self.assertGreater(teacher_profile.profile_completion_score, 50)  # Should be reasonably high with comprehensive data
        # Profile completion depends on the scoring algorithm - may not be 100% complete without all optional fields
    
    def test_accept_invitation_with_profile_photo_upload(self):
        """Test invitation acceptance with profile photo upload."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        # Create test image
        test_image = self._create_test_image()
        
        profile_data = {
            'bio': 'Mathematics teacher with photo',
            'specialty': 'Mathematics',
            'profile_photo': test_image
        }
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url, profile_data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify profile photo was uploaded
        self.teacher_user.refresh_from_db()
        self.assertIsNotNone(self.teacher_user.profile_photo)
        self.assertTrue(self.teacher_user.profile_photo.name.startswith('profile_photos/'))
    
    def test_accept_invitation_with_credentials_documents_upload(self):
        """Test invitation acceptance with credentials documents upload."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        # Create test documents
        test_diploma = self._create_test_document('diploma.pdf')
        test_certificate = self._create_test_document('certificate.pdf')
        
        profile_data = {
            'bio': 'Mathematics teacher with credentials',
            'specialty': 'Mathematics',
            'credentials_documents': [
                {
                    'type': 'diploma',
                    'name': 'Master of Science Diploma',
                    'file': test_diploma
                },
                {
                    'type': 'certificate',
                    'name': 'Teaching Certificate',
                    'file': test_certificate
                }
            ]
        }
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url, profile_data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify credentials documents were processed
        teacher_profile = self.teacher_user.teacher_profile
        self.assertIsInstance(teacher_profile.credentials_documents, list)
        self.assertEqual(len(teacher_profile.credentials_documents), 2)
    
    def test_accept_invitation_with_partial_profile_data(self):
        """Test invitation acceptance with partial profile data (backward compatibility)."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        partial_profile_data = {
            'bio': 'Simple teacher bio',
            'specialty': 'Mathematics',
            'hourly_rate': '40.00'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url, partial_profile_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify partial profile was created
        teacher_profile = self.teacher_user.teacher_profile
        self.assertEqual(teacher_profile.bio, partial_profile_data['bio'])
        self.assertEqual(teacher_profile.specialty, partial_profile_data['specialty'])
        self.assertEqual(teacher_profile.hourly_rate, Decimal(partial_profile_data['hourly_rate']))
        
        # Verify empty structured fields have defaults
        self.assertEqual(teacher_profile.teaching_subjects, [])
        self.assertEqual(teacher_profile.grade_level_preferences, [])
        self.assertEqual(teacher_profile.rate_structure, {})
        self.assertEqual(teacher_profile.education_background, {})
        self.assertEqual(teacher_profile.teaching_experience, {})
    
    def test_accept_invitation_without_profile_data(self):
        """Test invitation acceptance without any profile data (backward compatibility)."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify minimal profile was created (existing behavior)
        teacher_profile = self.teacher_user.teacher_profile
        self.assertEqual(teacher_profile.bio, "")
        self.assertEqual(teacher_profile.specialty, "")
        self.assertIsNone(teacher_profile.hourly_rate)
    
    def test_accept_invitation_with_invalid_structured_data(self):
        """Test invitation acceptance with invalid structured data validation."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        invalid_profile_data = {
            'bio': 'Teacher with invalid data',
            'teaching_subjects': 'invalid_string_instead_of_list',  # Should be list
            'grade_level_preferences': {'invalid': 'dict_instead_of_list'},  # Should be list
            'hourly_rate': 'invalid_rate',  # Should be decimal
            'education_background': 'invalid_string',  # Should be dict
            'teaching_experience': ['invalid', 'list'],  # Should be dict
        }
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url, invalid_profile_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        
        # Verify no partial data was saved (transaction rollback)
        self.assertFalse(hasattr(self.teacher_user, 'teacher_profile'))
    
    def test_accept_invitation_with_oversized_files(self):
        """Test invitation acceptance with oversized file uploads."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        # Create oversized file (> 5MB)
        large_content = b'x' * (6 * 1024 * 1024)  # 6MB
        oversized_file = SimpleUploadedFile(
            name='oversized.pdf',
            content=large_content,
            content_type='application/pdf'
        )
        
        profile_data = {
            'bio': 'Teacher with oversized file',
            'specialty': 'Mathematics',
            'profile_photo': oversized_file
        }
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url, profile_data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file size', response.data.get('errors', {}).get('profile_photo', [{}])[0].get('message', '').lower())
    
    def test_accept_invitation_with_malicious_file_upload(self):
        """Test invitation acceptance with malicious file upload."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        # Create potentially malicious file
        malicious_file = SimpleUploadedFile(
            name='malicious.exe',
            content=b'MZ\x90\x00',  # PE header
            content_type='application/octet-stream'
        )
        
        profile_data = {
            'bio': 'Teacher with malicious file',
            'specialty': 'Mathematics',
            'profile_photo': malicious_file
        }
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url, profile_data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file type', response.data.get('errors', {}).get('profile_photo', [{}])[0].get('message', '').lower())
    
    def test_accept_invitation_atomic_transaction(self):
        """Test that invitation acceptance with profile creation is atomic."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        profile_data = {
            'bio': 'Teacher profile for transaction test',
            'specialty': 'Mathematics',
            'hourly_rate': '40.00'
        }
        
        # Mock a failure in profile completion calculation to simulate transaction rollback
        with patch('accounts.models.TeacherProfile.update_completion_score', side_effect=Exception('Test error')):
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
            response = self.client.post(url, profile_data, format='json')
            
            # Should return error
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Verify invitation was not accepted (transaction rolled back)
            self.invitation.refresh_from_db()
            self.assertFalse(self.invitation.is_accepted)
            self.assertNotEqual(self.invitation.status, InvitationStatus.ACCEPTED)
            
            # Verify no teacher profile was created
            self.assertFalse(hasattr(self.teacher_user, 'teacher_profile'))
    
    def test_accept_invitation_rate_validation_against_school_settings(self):
        """Test that teacher hourly rate is validated against school billing settings."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        # Set school maximum rate (this would be implemented in school settings)
        profile_data = {
            'bio': 'Teacher with high rate',
            'specialty': 'Mathematics',
            'hourly_rate': '150.00'  # Very high rate
        }
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url, profile_data, format='json')
        
        # Should succeed but potentially with warning (depending on implementation)
        # Or could fail if school has strict rate limits
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn('rate', response.data.get('errors', {}).get('hourly_rate', [{}])[0].get('message', '').lower())
    
    @patch('accounts.views.SchoolActivityService.create_activity')
    def test_accept_invitation_with_profile_creates_activity_log(self, mock_create_activity):
        """Test that accepting invitation with profile data creates proper activity log."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        profile_data = {
            'bio': 'Teacher for activity logging test',
            'specialty': 'Mathematics',
            'hourly_rate': '40.00'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url, profile_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify activity was logged with profile creation details
        mock_create_activity.assert_called_once()
        call_kwargs = mock_create_activity.call_args[1]
        self.assertEqual(call_kwargs['school'], self.invitation.school)
        self.assertEqual(call_kwargs['actor'], self.teacher_user)
        self.assertIn('profile', call_kwargs['description'].lower())
    
    def test_accept_invitation_returns_comprehensive_response(self):
        """Test that invitation acceptance returns comprehensive response data."""
        url = reverse('accounts:teacher-invitation-accept', kwargs={'token': self.invitation.token})
        
        profile_data = {
            'bio': 'Comprehensive response test teacher',
            'specialty': 'Mathematics',
            'hourly_rate': '45.00',
            'teaching_subjects': [{'subject': 'Math', 'level': 'expert'}]
        }
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token}')
        response = self.client.post(url, profile_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify comprehensive response structure
        self.assertIn('message', response.data)
        self.assertIn('invitation', response.data)
        self.assertIn('membership', response.data)
        self.assertIn('teacher_profile', response.data)
        
        # Verify teacher profile data in response
        teacher_profile_data = response.data['teacher_profile']
        self.assertEqual(teacher_profile_data['bio'], profile_data['bio'])
        self.assertEqual(teacher_profile_data['specialty'], profile_data['specialty'])
        self.assertEqual(str(teacher_profile_data['hourly_rate']), profile_data['hourly_rate'])
        
        # Verify profile completion data is included
        self.assertIn('profile_completion', teacher_profile_data)
        self.assertIn('completion_percentage', teacher_profile_data['profile_completion'])
        self.assertIn('is_complete', teacher_profile_data['profile_completion'])