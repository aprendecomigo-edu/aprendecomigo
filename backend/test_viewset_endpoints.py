#!/usr/bin/env python
"""
Quick test script to verify the new PackageExpirationViewSet endpoints work correctly.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aprendecomigo.settings.testing')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from finances.models import PurchaseTransaction, TransactionType, TransactionPaymentStatus
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

User = get_user_model()

def test_viewset_endpoints():
    print("Testing PackageExpirationViewSet endpoints...")
    
    # Create test users (or get existing ones)
    admin_user, created = User.objects.get_or_create(
        email="admin@test.com",
        defaults={
            'name': "Admin User", 
            'phone_number': "+1234567890",
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    # Ensure admin permissions are set
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()
    
    student, created = User.objects.get_or_create(
        email="student@test.com",
        defaults={
            'name': "Test Student",
            'phone_number': "+1234567891"
        }
    )
    
    # Create test data
    now = timezone.now()
    expired_package = PurchaseTransaction.objects.create(
        student=student,
        transaction_type=TransactionType.PACKAGE,
        amount=Decimal('100.00'),
        payment_status=TransactionPaymentStatus.COMPLETED,
        expires_at=now - timedelta(days=1)
    )
    
    client = APIClient()
    client.force_authenticate(user=admin_user)
    
    # Test the new ViewSet endpoints
    endpoints = [
        ('/api/finances/package-expiration/expired/', 'GET'),
        ('/api/finances/package-expiration/analytics/', 'GET'),
        ('/api/finances/package-expiration/process-expired/', 'POST'),
        ('/api/finances/package-expiration/send-notifications/', 'POST'),
    ]
    
    for endpoint, method in endpoints:
        if method == 'GET':
            response = client.get(endpoint)
        else:
            response = client.post(endpoint, {})
            
        print(f"{method} {endpoint}: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  Error: {response.data}")
    
    # Test extend endpoint with data
    extend_data = {
        'package_id': expired_package.id,
        'extension_days': 30,
        'reason': 'Test extension'
    }
    response = client.post('/api/finances/package-expiration/extend/', extend_data)
    print(f"POST /api/finances/package-expiration/extend/: {response.status_code}")
    if response.status_code != 200:
        print(f"  Error: {response.data}")
    
    print("ViewSet endpoint test completed!")

if __name__ == '__main__':
    test_viewset_endpoints()
