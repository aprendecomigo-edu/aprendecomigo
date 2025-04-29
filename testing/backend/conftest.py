import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.conf import settings
import os
import sys

# Add the backend directory to the path so we can import from it
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

User = get_user_model()

@pytest.fixture
def api_client():
    """Return an API client for testing API endpoints."""
    return APIClient()

@pytest.fixture
def admin_user():
    """Create and return an admin user."""
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpassword'
    )
    return admin

@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def regular_user():
    """Create and return a regular user."""
    user = User.objects.create_user(
        username='user',
        email='user@example.com',
        password='userpassword'
    )
    return user

@pytest.fixture
def teacher_user():
    """Create and return a teacher user."""
    teacher = User.objects.create_user(
        username='teacher',
        email='teacher@example.com',
        password='teacherpassword'
    )
    # Assuming there's a teacher profile or group, you'd set that up here
    return teacher

@pytest.fixture
def student_user():
    """Create and return a student user."""
    student = User.objects.create_user(
        username='student',
        email='student@example.com',
        password='studentpassword'
    )
    # Assuming there's a student profile or group, you'd set that up here
    return student

@pytest.fixture
def user_client(api_client, regular_user):
    """Return an API client authenticated as a regular user."""
    api_client.force_authenticate(user=regular_user)
    return api_client

@pytest.fixture
def teacher_client(api_client, teacher_user):
    """Return an API client authenticated as a teacher."""
    api_client.force_authenticate(user=teacher_user)
    return api_client

@pytest.fixture
def student_client(api_client, student_user):
    """Return an API client authenticated as a student."""
    api_client.force_authenticate(user=student_user)
    return api_client
