#!/usr/bin/env python
"""Debug script to check list response structure"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aprendecomigo.settings.testing')
django.setup()

from rest_framework.test import APIClient
from accounts.models import CustomUser, SchoolRole
from django.urls import reverse

# Get existing test user (assuming it exists from previous tests)
try:
    teacher_user = CustomUser.objects.filter(email='teacher_debug@test.com').first()
    if not teacher_user:
        print("No teacher user found")
        exit(1)
    
    client = APIClient()
    client.force_authenticate(user=teacher_user)
    
    url = reverse('teacher-availability-list')
    response = client.get(url)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Type: {type(response.data)}")
    print(f"Response Keys: {response.data.keys() if isinstance(response.data, dict) else 'Not a dict'}")
    print(f"Response Data: {response.data}")
    
except Exception as e:
    print(f"Error: {e}")